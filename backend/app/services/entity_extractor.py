"""Entity extraction service using NLP with caching and Pydantic validation."""

import re
import json
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime
import uuid
from pydantic import BaseModel, Field, field_validator
from ..config import settings
from .cache import cache_service
from .llm_ner import llm_ner_service

try:
    import spacy  # Optional advanced NLP
except Exception:
    spacy = None

from ..models.knowledge_graph import (
    Entity, EntityType, Relationship, RelationType
)


class ExtractionResult(BaseModel):
    """Validated extraction result container for caching and reuse."""
    entities: List[Dict[str, Any]] = Field(default_factory=list)
    relationships: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EntityExtractor:
    """Service for extracting entities and relationships from text."""
    
    def __init__(self):
        """Initialize the entity extractor."""
        self._nlp = None
        if settings.enable_spacy and spacy is not None:
            try:
                self._nlp = spacy.load(settings.spacy_model)
            except Exception:
                self._nlp = None
        # Entity patterns for rule-based extraction
        self.entity_patterns = {
            EntityType.PERSON: [
                r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # Full names
                r'\b(?:Mr|Mrs|Ms|Dr|Prof)\.? [A-Z][a-z]+\b',  # Titles with names
            ],
            EntityType.ORGANIZATION: [
                r'\b[A-Z][A-Za-z]+(?: [A-Z][A-Za-z]+)* (?:Inc|Corp|LLC|Ltd|Company|Organization|Institute|University)\b',
                r'\b(?:Google|Microsoft|Apple|Amazon|Facebook|OpenAI|Anthropic)\b',  # Known companies
            ],
            EntityType.LOCATION: [
                r'\b[A-Z][a-z]+(?: [A-Z][a-z]+)* (?:City|Country|State|Province|Street|Avenue|Road)\b',
                r'\b(?:New York|London|Paris|Tokyo|Beijing|San Francisco|Los Angeles)\b',  # Known cities
            ],
            EntityType.DATE: [
                r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # Date formats
                r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2},? \d{4}\b',
                r'\b(?:today|tomorrow|yesterday|last week|next month)\b',
            ],
            EntityType.QUANTITY: [
                r'\b\d+(?:\.\d+)?\s*(?:dollars|euros|pounds|yen|USD|EUR|GBP)\b',
                r'\b\d+(?:\.\d+)?\s*(?:kg|g|mg|lb|oz|km|m|cm|mm|miles|feet|inches)\b',
                r'\b\d+(?:\.\d+)?%\b',  # Percentages
            ]
        }
        
        # Relationship indicators
        self.relationship_indicators = {
            RelationType.IS_A: ["is a", "is an", "are", "was a", "were"],
            RelationType.HAS: ["has", "have", "had", "contains", "includes"],
            RelationType.BELONGS_TO: ["belongs to", "owned by", "part of", "member of"],
            RelationType.LOCATED_IN: ["located in", "in", "at", "near", "from"],
            RelationType.WORKS_FOR: ["works for", "employed by", "works at", "job at"],
            RelationType.KNOWS: ["knows", "met", "friends with", "colleague of"],
            RelationType.CREATED_BY: ["created by", "made by", "built by", "designed by"],
            RelationType.CAUSES: ["causes", "leads to", "results in", "triggers"],
            RelationType.PREVENTS: ["prevents", "stops", "blocks", "inhibits"],
        }
        
        # Negation indicators
        self.negation_indicators = [
            "not", "no", "never", "neither", "nor", "nothing", "nobody",
            "isn't", "aren't", "wasn't", "weren't", "won't", "wouldn't",
            "can't", "couldn't", "shouldn't", "mustn't", "needn't",
            "doesn't", "didn't", "don't", "hasn't", "haven't", "hadn't",
            "incorrect", "false", "wrong", "actually", "correction",
            "update", "revised", "changed", "no longer", "not anymore"
        ]
    
    def extract_entities(self, text: str, session_id: str, message_id: Optional[str] = None) -> List[Entity]:
        """Extract entities from text using spaCy (if available) and patterns.

        Results are cached per (text, session_id, message_id) when caching is enabled.
        """
        cache_key = f"entities:{hash((text, session_id, message_id))}"
        cached = cache_service.get(cache_key)
        if cached:
            try:
                data = ExtractionResult.model_validate(cached)
                return [Entity(**e) for e in data.entities]
            except Exception:
                pass

        entities = []
        seen_entities = set()  # To avoid duplicates

        # LLM-based NER (optional, prioritized if enabled)
        if settings.enable_llm_ner:
            try:
                llm_entities, _ = await llm_ner_service.extract(text, session_id, message_id)
                for e in llm_entities:
                    key = (e.name.lower(), e.type)
                    if key not in seen_entities:
                        seen_entities.add(key)
                        entities.append(e)
            except Exception:
                pass

        # spaCy-based extraction for higher recall/precision if available
        if self._nlp is not None:
            doc = self._nlp(text)
            for ent in doc.ents:
                etype = self._map_spacy_label(ent.label_)
                entity_key = (ent.text.lower().strip(), etype)
                if entity_key in seen_entities:
                    continue
                seen_entities.add(entity_key)
                entity = Entity(
                    id=str(uuid.uuid4()),
                    name=ent.text.strip(),
                    type=etype,
                    properties={
                        "spacy_label": ent.label_,
                        "start_char": ent.start_char,
                        "end_char": ent.end_char,
                    },
                    confidence=0.85,
                    source_text=text,
                    session_id=session_id,
                    message_id=message_id
                )
                entities.append(entity)
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entity_text = match.group().strip()
                    
                    # Skip if already seen
                    entity_key = (entity_text.lower(), entity_type)
                    if entity_key in seen_entities:
                        continue
                    
                    seen_entities.add(entity_key)
                    
                    entity = Entity(
                        id=str(uuid.uuid4()),
                        name=entity_text,
                        type=entity_type,
                        properties={
                            "original_text": entity_text,
                            "position": match.span(),
                            "context": text[max(0, match.start()-50):min(len(text), match.end()+50)]
                        },
                        confidence=0.8,  # Rule-based extraction confidence
                        source_text=text,
                        session_id=session_id,
                        message_id=message_id
                    )
                    entities.append(entity)
        
        # Also extract general noun phrases as potential entities
        entities.extend(self._extract_noun_phrases(text, session_id, message_id, seen_entities))
        
        # Cache validated result
        try:
            payload = ExtractionResult(
                entities=[e.model_dump() for e in entities],
                relationships=[]
            ).model_dump()
            cache_service.set(cache_key, payload)
        except Exception:
            pass

        return entities
    
    def _extract_noun_phrases(self, text: str, session_id: str, message_id: Optional[str], 
                            seen_entities: set) -> List[Entity]:
        """Extract noun phrases as potential concept entities."""
        entities = []
        
        # Simple noun phrase pattern
        noun_phrase_pattern = r'\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        matches = re.finditer(noun_phrase_pattern, text)
        
        for match in matches:
            entity_text = match.group().strip()
            
            # Skip if too short or already seen
            if len(entity_text) < 3:
                continue
            
            entity_key = (entity_text.lower(), EntityType.CONCEPT)
            if entity_key in seen_entities:
                continue
            
            # Skip if it matches other entity types
            is_other_type = False
            for entity_type, patterns in self.entity_patterns.items():
                for pattern in patterns:
                    if re.match(pattern, entity_text, re.IGNORECASE):
                        is_other_type = True
                        break
                if is_other_type:
                    break
            
            if not is_other_type:
                seen_entities.add(entity_key)
                entity = Entity(
                    id=str(uuid.uuid4()),
                    name=entity_text,
                    type=EntityType.CONCEPT,
                    properties={
                        "original_text": entity_text,
                        "position": match.span()
                    },
                    confidence=0.6,  # Lower confidence for general concepts
                    source_text=text,
                    session_id=session_id,
                    message_id=message_id
                )
                entities.append(entity)
        
        return entities
    
    async def extract_relationships(self, text: str, entities: List[Entity], 
                            session_id: str, message_id: Optional[str] = None) -> List[Relationship]:
        """Extract relationships between entities from text with caching."""
        cache_key = f"rels:{hash((text, session_id, message_id, tuple(sorted(e.id for e in entities))) )}"
        cached = cache_service.get(cache_key)
        if cached:
            try:
                data = ExtractionResult.model_validate(cached)
                return [Relationship(**r) for r in data.relationships]
            except Exception:
                pass
        relationships = []
        
        # Create entity position map
        entity_positions = {}
        for entity in entities:
            if "position" in entity.properties:
                pos = entity.properties["position"]
                entity_positions[entity.id] = (pos[0], pos[1], entity)
        
        # LLM-based relationships (optional)
        if settings.enable_llm_ner:
            try:
                _, llm_relationships = await llm_ner_service.extract(text, session_id, message_id)
                relationships.extend(llm_relationships)
            except Exception:
                pass

        # Look for relationship patterns
        for rel_type, indicators in self.relationship_indicators.items():
            for indicator in indicators:
                pattern = re.compile(rf'(\b\w+(?:\s+\w+)*)\s+{re.escape(indicator)}\s+(\b\w+(?:\s+\w+)*)', re.IGNORECASE)
                matches = pattern.finditer(text)
                
                for match in matches:
                    source_text = match.group(1).strip()
                    target_text = match.group(2).strip()
                    
                    # Find matching entities
                    source_entity = self._find_matching_entity(source_text, entities)
                    target_entity = self._find_matching_entity(target_text, entities)
                    
                    if source_entity and target_entity:
                        relationship = Relationship(
                            id=str(uuid.uuid4()),
                            source_entity_id=source_entity.id,
                            target_entity_id=target_entity.id,
                            type=rel_type,
                            properties={
                                "indicator": indicator,
                                "context": match.group(),
                                "position": match.span()
                            },
                            confidence=0.7,
                            session_id=session_id,
                            message_id=message_id
                        )
                        relationships.append(relationship)
        
        # Check for negations
        relationships = self._process_negations(text, relationships)
        
        # Cache validated result
        try:
            payload = ExtractionResult(
                entities=[],
                relationships=[r.model_dump() for r in relationships]
            ).model_dump()
            cache_service.set(cache_key, payload)
        except Exception:
            pass

        return relationships

    def _map_spacy_label(self, label: str) -> EntityType:
        mapping = {
            "PERSON": EntityType.PERSON,
            "ORG": EntityType.ORGANIZATION,
            "GPE": EntityType.LOCATION,
            "LOC": EntityType.LOCATION,
            "DATE": EntityType.DATE,
            "TIME": EntityType.DATE,
            "QUANTITY": EntityType.QUANTITY,
            "PERCENT": EntityType.QUANTITY,
            "MONEY": EntityType.QUANTITY,
            "EVENT": EntityType.EVENT,
            # Default
        }
        return mapping.get(label.upper(), EntityType.CONCEPT)
    
    def _find_matching_entity(self, text: str, entities: List[Entity]) -> Optional[Entity]:
        """Find an entity that matches the given text."""
        text_lower = text.lower().strip()
        
        # Exact match
        for entity in entities:
            if entity.name.lower() == text_lower:
                return entity
        
        # Partial match
        for entity in entities:
            if text_lower in entity.name.lower() or entity.name.lower() in text_lower:
                return entity
        
        return None
    
    def _process_negations(self, text: str, relationships: List[Relationship]) -> List[Relationship]:
        """Process negations in relationships."""
        text_lower = text.lower()
        
        for relationship in relationships:
            # Check if the relationship context contains negation
            if "context" in relationship.properties:
                context = relationship.properties["context"].lower()
                
                # Check for negation indicators before the relationship
                for neg_indicator in self.negation_indicators:
                    if neg_indicator in context:
                        # Mark relationship as potentially negated
                        relationship.properties["negation_detected"] = True
                        relationship.properties["negation_indicator"] = neg_indicator
                        relationship.confidence *= 0.5  # Reduce confidence
                        break
        
        return relationships
    
    def detect_negations(self, current_text: str, previous_relationships: List[Relationship],
                        current_relationships: List[Relationship]) -> List[Tuple[Relationship, Relationship]]:
        """Detect if current relationships negate previous ones."""
        negations = []
        
        # Look for explicit negation patterns
        negation_patterns = [
            r"(?:actually|correction|update).*?not",
            r"no longer",
            r"not anymore",
            r"changed from .* to",
            r"used to .* but now",
            r"previously .* now",
        ]
        
        current_text_lower = current_text.lower()
        
        # Check each current relationship against previous ones
        for curr_rel in current_relationships:
            for prev_rel in previous_relationships:
                # Same entities but potentially different relationship
                if (curr_rel.source_entity_id == prev_rel.source_entity_id and 
                    curr_rel.target_entity_id == prev_rel.target_entity_id):
                    
                    # Check if the text indicates a negation or update
                    for pattern in negation_patterns:
                        if re.search(pattern, current_text_lower):
                            # Different relationship type or negation detected
                            if (curr_rel.type != prev_rel.type or 
                                curr_rel.properties.get("negation_detected", False)):
                                negations.append((prev_rel, curr_rel))
                                break
        
        return negations
    
    def extract_temporal_context(self, text: str) -> Dict[str, Any]:
        """Extract temporal context from text."""
        temporal_info = {
            "tense": "present",  # Default
            "time_references": [],
            "temporal_order": []
        }
        
        # Past tense indicators
        past_indicators = ["was", "were", "had", "did", "used to", "previously", "before", "ago"]
        # Future tense indicators
        future_indicators = ["will", "going to", "shall", "next", "tomorrow", "soon", "later"]
        # Present tense indicators
        present_indicators = ["is", "are", "am", "now", "currently", "today", "at present"]
        
        text_lower = text.lower()
        
        # Determine primary tense
        past_count = sum(1 for ind in past_indicators if ind in text_lower)
        future_count = sum(1 for ind in future_indicators if ind in text_lower)
        present_count = sum(1 for ind in present_indicators if ind in text_lower)
        
        if past_count > max(future_count, present_count):
            temporal_info["tense"] = "past"
        elif future_count > max(past_count, present_count):
            temporal_info["tense"] = "future"
        else:
            temporal_info["tense"] = "present"
        
        # Extract specific time references
        time_patterns = [
            r'\b\d{4}\b',  # Years
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b',
            r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b',
            r'\b\d{1,2}:\d{2}(?:\s*[AP]M)?\b',  # Times
        ]
        
        for pattern in time_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                temporal_info["time_references"].append({
                    "text": match.group(),
                    "position": match.span()
                })
        
        return temporal_info
