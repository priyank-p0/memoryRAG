"""LLM-powered Named Entity Recognition with reflection passes."""

from typing import List, Dict, Any, Optional, Tuple
import uuid
from datetime import datetime

from ..models.knowledge_graph import Entity, EntityType, Relationship, RelationType
from ..models.chat import ChatMessage, ChatRole
from ..config import settings
from .openai_adapter import OpenAIAdapter
from .google_adapter import GoogleAdapter
from .anthropic_adapter import AnthropicAdapter
from .cache import cache_service


SYSTEM_PROMPT = (
    "You are an information extraction system. Extract entities and relations as strict JSON. "
    "Use the schema: {entities:[{id,name,type,confidence}], relationships:[{id,source_name,target_name,type,confidence}]}. "
    "Entity types: PERSON, ORGANIZATION, LOCATION, DATE, QUANTITY, EVENT, OBJECT, CONCEPT. "
    "Relationship types: IS_A, HAS, BELONGS_TO, LOCATED_IN, WORKS_FOR, KNOWS, CREATED_BY, PART_OF, RELATED_TO, CAUSES, PREVENTS. "
    "Only return JSON, no commentary."
)


class LLMNERService:
    """Call an LLM to extract entities/relationships, with reflection passes."""

    def __init__(self):
        self.provider = settings.llm_ner_provider.lower()
        self.temperature = settings.llm_ner_temperature
        self.model_name = settings.llm_ner_model
        self.max_reflection = max(0, int(settings.llm_ner_max_reflection_passes))

        self.adapters = {}
        if settings.openai_api_key:
            self.adapters["openai"] = OpenAIAdapter(settings.openai_api_key)
        if settings.google_api_key:
            self.adapters["google"] = GoogleAdapter(settings.google_api_key)
        if settings.anthropic_api_key:
            self.adapters["anthropic"] = AnthropicAdapter(settings.anthropic_api_key)

    async def extract(self, text: str, session_id: str, message_id: Optional[str] = None) -> Tuple[List[Entity], List[Relationship]]:
        if not settings.enable_llm_ner:
            return [], []

        cache_key = f"llmner:{hash((text, session_id, message_id, self.provider, self.model_name))}"
        cached = cache_service.get(cache_key)
        if cached:
            try:
                ents = [Entity(**e) for e in cached.get("entities", [])]
                rels = [Relationship(**r) for r in cached.get("relationships", [])]
                return ents, rels
            except Exception:
                pass

        # Select adapter
        adapter = self.adapters.get(self.provider)
        if not adapter:
            return [], []

        # First pass
        entities, relationships, raw = await self._run_once(adapter, text, session_id, message_id)

        # Reflection passes
        for _ in range(self.max_reflection):
            critique = self._critique(raw, entities, relationships)
            if not critique:
                break
            entities, relationships, raw = await self._run_once(
                adapter, text + "\nCritique:" + critique, session_id, message_id
            )

        cache_service.set(
            cache_key,
            {
                "entities": [e.model_dump() for e in entities],
                "relationships": [r.model_dump() for r in relationships],
            },
        )
        return entities, relationships

    async def _run_once(self, adapter, text: str, session_id: str, message_id: Optional[str]):
        # Construct messages to be compatible across adapters (esp. Gemini)
        # 1) A preface instruction as a prior user turn (goes into history)
        # 2) The actual text as the current user message
        messages = [
            ChatMessage(role=ChatRole.USER, content=SYSTEM_PROMPT),
            ChatMessage(role=ChatRole.USER, content=text),
        ]
        try:
            resp = await adapter.chat_completion(
                messages=messages,
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=800,
                system_prompt=SYSTEM_PROMPT,
            )
            raw = resp.get("content", "{}")
            data = self._safe_parse_json(raw)
            entities = self._map_entities(data.get("entities", []), text, session_id, message_id)
            relationships = self._map_relationships(data.get("relationships", []), entities, session_id, message_id)
            return entities, relationships, raw
        except Exception as e:
            return [], [], "{}"

    def _safe_parse_json(self, s: str) -> Dict[str, Any]:
        import json
        try:
            # Trim leading/trailing content if model added extra text
            start = s.find("{")
            end = s.rfind("}")
            if start != -1 and end != -1 and end >= start:
                s = s[start : end + 1]
            return json.loads(s)
        except Exception:
            return {"entities": [], "relationships": []}

    def _critique(self, raw: str, entities: List[Entity], relationships: List[Relationship]) -> str:
        # Simple heuristic: request more structure if nothing found
        if not entities and not relationships:
            return "No entities or relationships were extracted. Ensure JSON with fields entities and relationships."
        # Ask for link resolution if names are ambiguous
        ambiguous = any(len(e.name.split()) == 1 and e.type in {EntityType.PERSON, EntityType.ORGANIZATION} for e in entities)
        if ambiguous:
            return "Resolve single-word entity names by adding more context when possible."
        return ""

    def _map_entities(self, ents: List[Dict[str, Any]], source_text: str, session_id: str, message_id: Optional[str]) -> List[Entity]:
        results: List[Entity] = []
        for ent in ents:
            name = str(ent.get("name", "")).strip()
            if not name:
                continue
            etype = str(ent.get("type", "CONCEPT")).upper()
            try:
                etype_enum = EntityType[etype] if etype in EntityType.__members__ else EntityType.CONCEPT
            except Exception:
                etype_enum = EntityType.CONCEPT
            conf = float(ent.get("confidence", 0.8))
            results.append(
                Entity(
                    id=str(uuid.uuid4()),
                    name=name,
                    type=etype_enum,
                    properties={"source": "llm"},
                    confidence=max(0.0, min(1.0, conf)),
                    source_text=source_text,
                    session_id=session_id,
                    message_id=message_id,
                )
            )
        return results

    def _map_relationships(self, rels: List[Dict[str, Any]], entities: List[Entity], session_id: str, message_id: Optional[str]) -> List[Relationship]:
        results: List[Relationship] = []
        # Build name->id map
        name_map = {}
        for e in entities:
            name_map.setdefault(e.name.lower(), e.id)
        for rel in rels:
            src_name = str(rel.get("source_name", "")).lower().strip()
            tgt_name = str(rel.get("target_name", "")).lower().strip()
            if not src_name or not tgt_name or src_name not in name_map or tgt_name not in name_map:
                continue
            rtype = str(rel.get("type", "RELATED_TO")).upper()
            try:
                rtype_enum = RelationType[rtype] if rtype in RelationType.__members__ else RelationType.RELATED_TO
            except Exception:
                rtype_enum = RelationType.RELATED_TO
            conf = float(rel.get("confidence", 0.7))
            results.append(
                Relationship(
                    id=str(uuid.uuid4()),
                    source_entity_id=name_map[src_name],
                    target_entity_id=name_map[tgt_name],
                    type=rtype_enum,
                    properties={"source": "llm"},
                    confidence=max(0.0, min(1.0, conf)),
                    session_id=session_id,
                    message_id=message_id,
                )
            )
        return results


# Global instance
llm_ner_service = LLMNERService()


