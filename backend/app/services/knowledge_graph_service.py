"""Main knowledge graph service integrating entity extraction and graph management."""

import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

from ..models.knowledge_graph import (
    Entity, Relationship, EpisodicGraph, 
    CommunityGraph, NegationEvent, GraphUpdate
)
from ..models.storage import ChatRecord
from .entity_extractor import EntityExtractor
from .graph_manager import GraphManager

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """Service for managing knowledge graph operations."""
    
    def __init__(self):
        """Initialize the knowledge graph service."""
        self.entity_extractor = EntityExtractor()
        self.graph_manager = GraphManager()
        self.episodic_graphs: Dict[str, EpisodicGraph] = {}
        self.community_graph: Optional[CommunityGraph] = None
        self.graph_updates: List[GraphUpdate] = []
    
    async def process_chat_interaction(self, user_text: str, response_text: str, 
                                      session_id: str, message_id: Optional[str] = None) -> Dict[str, Any]:
        """Process a chat interaction and update the knowledge graph."""
        
        # Create or get episodic graph for this session
        if session_id not in self.episodic_graphs:
            self.episodic_graphs[session_id] = EpisodicGraph(
                id=str(uuid.uuid4()),
                session_id=session_id
            )
        
        episodic_graph = self.episodic_graphs[session_id]
        
        # Extract entities from user input
        user_entities = self.entity_extractor.extract_entities(
            user_text, session_id, f"{message_id}_user"
        )
        
        # Extract entities from model response
        response_entities = self.entity_extractor.extract_entities(
            response_text, session_id, f"{message_id}_response"
        )
        
        # Combine and deduplicate entities
        all_entities = self._merge_entities(user_entities + response_entities)
        
        # Extract relationships from user input
        user_relationships = self.entity_extractor.extract_relationships(
            user_text, all_entities, session_id, f"{message_id}_user"
        )
        
        # Extract relationships from response
        response_relationships = self.entity_extractor.extract_relationships(
            response_text, all_entities, session_id, f"{message_id}_response"
        )
        
        all_relationships = user_relationships + response_relationships
        
        # Check for negations against existing relationships
        existing_relationships = episodic_graph.relationships
        negations = await self._detect_and_handle_negations(
            user_text + " " + response_text,
            existing_relationships,
            all_relationships,
            session_id,
            message_id
        )
        
        # Add entities and relationships to episodic graph
        for entity in all_entities:
            episodic_graph.add_entity(entity)
            await self.graph_manager.store_entity(entity)
        
        for relationship in all_relationships:
            episodic_graph.add_relationship(relationship)
            await self.graph_manager.store_relationship(relationship)
        
        # Store episodic graph
        await self.graph_manager.store_episodic_graph(episodic_graph)
        
        # Update community graph
        await self._update_community_graph(session_id, message_id)
        
        # Create graph update record
        update = GraphUpdate(
            id=str(uuid.uuid4()),
            update_type="process_interaction",
            affected_entities=[e.id for e in all_entities],
            affected_relationships=[r.id for r in all_relationships],
            session_id=session_id,
            message_id=message_id,
            details={
                "user_entities": len(user_entities),
                "response_entities": len(response_entities),
                "relationships": len(all_relationships),
                "negations": len(negations)
            }
        )
        self.graph_updates.append(update)
        
        # Extract temporal context
        temporal_context = self.entity_extractor.extract_temporal_context(
            user_text + " " + response_text
        )
        
        return {
            "entities_extracted": len(all_entities),
            "relationships_extracted": len(all_relationships),
            "negations_detected": len(negations),
            "episodic_graph_id": episodic_graph.id,
            "community_graph_updated": self.community_graph is not None,
            "temporal_context": temporal_context,
            "entities": [e.model_dump() for e in all_entities[:5]],  # Sample entities
            "relationships": [r.model_dump() for r in all_relationships[:5]]  # Sample relationships
        }
    
    def _merge_entities(self, entities: List[Entity]) -> List[Entity]:
        """Merge duplicate entities based on name and type."""
        merged = {}
        
        for entity in entities:
            key = (entity.name.lower(), entity.type)
            if key not in merged:
                merged[key] = entity
            else:
                # Merge properties and update confidence
                existing = merged[key]
                existing.properties.update(entity.properties)
                existing.confidence = max(existing.confidence, entity.confidence)
        
        return list(merged.values())
    
    async def _detect_and_handle_negations(self, text: str, 
                                          existing_relationships: List[Relationship],
                                          new_relationships: List[Relationship],
                                          session_id: str, message_id: str) -> List[NegationEvent]:
        """Detect and handle relationship negations."""
        negations = []
        
        # Use entity extractor to detect potential negations
        negation_pairs = self.entity_extractor.detect_negations(
            text, existing_relationships, new_relationships
        )
        
        for original_rel, negating_rel in negation_pairs:
            # Handle the negation in the graph
            negation_event = await self.graph_manager.handle_negation(
                original_rel.id,
                negating_rel.id,
                session_id,
                message_id
            )
            
            if negation_event:
                negations.append(negation_event)
                
                # Update the relationships
                original_rel.is_active = False
                original_rel.negated_by_relationship_id = negating_rel.id
                negating_rel.negates_relationship_id = original_rel.id
                
                logger.info(f"Negation detected: {original_rel.id} negated by {negating_rel.id}")
        
        return negations
    
    async def _update_community_graph(self, session_id: str, message_id: str):
        """Update the community graph based on new information."""
        # Build or rebuild community graph
        self.community_graph = await self.graph_manager.build_community_graph()
        
        if self.community_graph:
            # Create update record
            update = GraphUpdate(
                id=str(uuid.uuid4()),
                update_type="update_community",
                affected_communities=[c.id for c in self.community_graph.communities],
                session_id=session_id,
                message_id=message_id,
                details={
                    "communities_count": len(self.community_graph.communities),
                    "inter_community_relationships": len(
                        self.community_graph.inter_community_relationships
                    )
                }
            )
            self.graph_updates.append(update)
    
    async def get_entity_context(self, entity_name: str) -> Dict[str, Any]:
        """Get full context for an entity including relationships and history."""
        # Query the graph for entity information
        query = """
        MATCH (e:Entity {name: $name})
        OPTIONAL MATCH (e)-[r:RELATES_TO]-(related:Entity)
        WHERE r.is_active = true
        OPTIONAL MATCH (e)<-[:INCLUDES]-(c:Community)
        RETURN e, collect(DISTINCT {
            relationship: r,
            related_entity: related
        }) as relationships,
        collect(DISTINCT c) as communities
        """
        
        results = await self.graph_manager.query_graph(
            query, {"name": entity_name}
        )
        
        if not results:
            return {"error": "Entity not found"}
        
        result = results[0]
        return {
            "entity": dict(result["e"]) if result["e"] else None,
            "relationships": [
                {
                    "type": rel["relationship"]["type"],
                    "related_entity": rel["related_entity"]["name"],
                    "confidence": rel["relationship"]["confidence"]
                }
                for rel in result["relationships"] if rel["relationship"]
            ],
            "communities": [
                dict(c) for c in result["communities"] if c
            ]
        }
    
    async def get_session_graph(self, session_id: str) -> Dict[str, Any]:
        """Get the complete graph for a session."""
        if session_id not in self.episodic_graphs:
            return {"error": "Session not found"}
        
        episodic_graph = self.episodic_graphs[session_id]
        
        return {
            "episodic_graph_id": episodic_graph.id,
            "entities_count": len(episodic_graph.entities),
            "relationships_count": len(episodic_graph.relationships),
            "entities": [e.model_dump() for e in episodic_graph.entities],
            "relationships": [r.model_dump() for r in episodic_graph.relationships],
            "created_at": episodic_graph.created_at.isoformat(),
            "updated_at": episodic_graph.updated_at.isoformat()
        }
    
    async def get_community_insights(self) -> Dict[str, Any]:
        """Get insights from the community graph."""
        if not self.community_graph:
            # Try to build it
            self.community_graph = await self.graph_manager.build_community_graph()
        
        if not self.community_graph:
            return {"error": "No community graph available"}
        
        insights = {
            "total_communities": len(self.community_graph.communities),
            "inter_community_connections": len(
                self.community_graph.inter_community_relationships
            ),
            "communities": []
        }
        
        for community in self.community_graph.communities:
            insights["communities"].append({
                "id": community.id,
                "name": community.name,
                "description": community.description,
                "size": len(community.entity_ids),
                "central_entities": community.central_entities,
                "confidence": community.confidence
            })
        
        return insights
    
    async def query_knowledge(self, query: str) -> Dict[str, Any]:
        """Query the knowledge graph with natural language."""
        # Extract entities from the query
        query_entities = self.entity_extractor.extract_entities(
            query, "query_session", "query"
        )
        
        results = {
            "query": query,
            "entities_found": [],
            "relationships_found": [],
            "insights": []
        }
        
        # For each entity in the query, get its context
        for entity in query_entities:
            context = await self.get_entity_context(entity.name)
            if "entity" in context and context["entity"]:
                results["entities_found"].append(context)
        
        # Get temporal context
        temporal_context = self.entity_extractor.extract_temporal_context(query)
        results["temporal_context"] = temporal_context
        
        return results
    
    async def get_graph_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph."""
        stats_query = """
        MATCH (e:Entity)
        WITH count(e) as entity_count
        MATCH ()-[r:RELATES_TO]->()
        WITH entity_count, count(r) as relationship_count
        MATCH (c:Community)
        WITH entity_count, relationship_count, count(c) as community_count
        MATCH (n:NegationEvent)
        RETURN entity_count, relationship_count, community_count, 
               count(n) as negation_count
        """
        
        results = await self.graph_manager.query_graph(stats_query)
        
        if results:
            return results[0]
        
        return {
            "entity_count": 0,
            "relationship_count": 0,
            "community_count": 0,
            "negation_count": 0
        }
    
    def close(self):
        """Close the knowledge graph service."""
        if self.graph_manager:
            self.graph_manager.close()


# Global knowledge graph service instance
knowledge_graph_service = KnowledgeGraphService()
