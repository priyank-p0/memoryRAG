"""Neo4j graph database manager for knowledge graphs."""

from neo4j import GraphDatabase, AsyncGraphDatabase
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import uuid
import json
import logging

from ..models.knowledge_graph import (
    Entity, Relationship, EpisodicGraph, Community, 
    CommunityGraph, NegationEvent, GraphUpdate,
    EntityType, RelationType
)
from ..config import settings

logger = logging.getLogger(__name__)


class GraphManager:
    """Manager for Neo4j graph database operations."""
    
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        """Initialize the graph manager."""
        self.uri = uri or getattr(settings, 'neo4j_uri', 'bolt://localhost:7687')
        self.user = user or getattr(settings, 'neo4j_user', 'neo4j')
        self.password = password or getattr(settings, 'neo4j_password', 'password')
        
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            self._initialize_constraints()
            logger.info("Successfully connected to Neo4j")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {str(e)}")
            self.driver = None
    
    def _initialize_constraints(self):
        """Initialize database constraints and indexes."""
        if not self.driver:
            return
        
        with self.driver.session() as session:
            # Create constraints for unique IDs
            constraints = [
                "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
                "CREATE CONSTRAINT relationship_id IF NOT EXISTS FOR ()-[r:RELATES_TO]-() REQUIRE r.id IS UNIQUE",
                "CREATE CONSTRAINT episode_id IF NOT EXISTS FOR (ep:Episode) REQUIRE ep.id IS UNIQUE",
                "CREATE CONSTRAINT community_id IF NOT EXISTS FOR (c:Community) REQUIRE c.id IS UNIQUE",
                "CREATE CONSTRAINT session_id IF NOT EXISTS FOR (s:Session) REQUIRE s.id IS UNIQUE"
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    logger.debug(f"Constraint might already exist: {e}")
            
            # Create indexes for better query performance
            indexes = [
                "CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)",
                "CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)",
                "CREATE INDEX entity_session IF NOT EXISTS FOR (e:Entity) ON (e.session_id)",
                "CREATE INDEX relationship_type IF NOT EXISTS FOR ()-[r:RELATES_TO]-() ON (r.type)",
                "CREATE INDEX relationship_active IF NOT EXISTS FOR ()-[r:RELATES_TO]-() ON (r.is_active)",
                "CREATE INDEX community_name IF NOT EXISTS FOR (c:Community) ON (c.name)"
            ]
            
            for index in indexes:
                try:
                    session.run(index)
                except Exception as e:
                    logger.debug(f"Index might already exist: {e}")
    
    def close(self):
        """Close the database connection."""
        if self.driver:
            self.driver.close()
    
    async def store_entity(self, entity: Entity) -> bool:
        """Store an entity in the graph database."""
        if not self.driver:
            return False
        
        with self.driver.session() as session:
            query = """
            MERGE (e:Entity {id: $id})
            SET e.name = $name,
                e.type = $type,
                e.properties = $properties,
                e.confidence = $confidence,
                e.source_text = $source_text,
                e.extracted_at = $extracted_at,
                e.session_id = $session_id,
                e.message_id = $message_id
            RETURN e
            """
            
            result = session.run(
                query,
                id=entity.id,
                name=entity.name,
                type=entity.type.value,
                properties=json.dumps(entity.properties),
                confidence=entity.confidence,
                source_text=entity.source_text,
                extracted_at=entity.extracted_at.isoformat(),
                session_id=entity.session_id,
                message_id=entity.message_id
            )
            
            return result.single() is not None
    
    async def store_relationship(self, relationship: Relationship) -> bool:
        """Store a relationship in the graph database."""
        if not self.driver:
            return False
        
        with self.driver.session() as session:
            query = """
            MATCH (source:Entity {id: $source_id})
            MATCH (target:Entity {id: $target_id})
            MERGE (source)-[r:RELATES_TO {id: $id}]->(target)
            SET r.type = $type,
                r.properties = $properties,
                r.confidence = $confidence,
                r.extracted_at = $extracted_at,
                r.session_id = $session_id,
                r.message_id = $message_id,
                r.is_active = $is_active,
                r.negates_relationship_id = $negates_id,
                r.negated_by_relationship_id = $negated_by_id
            RETURN r
            """
            
            result = session.run(
                query,
                id=relationship.id,
                source_id=relationship.source_entity_id,
                target_id=relationship.target_entity_id,
                type=relationship.type.value,
                properties=json.dumps(relationship.properties),
                confidence=relationship.confidence,
                extracted_at=relationship.extracted_at.isoformat(),
                session_id=relationship.session_id,
                message_id=relationship.message_id,
                is_active=relationship.is_active,
                negates_id=relationship.negates_relationship_id,
                negated_by_id=relationship.negated_by_relationship_id
            )
            
            return result.single() is not None
    
    async def store_episodic_graph(self, episodic_graph: EpisodicGraph) -> bool:
        """Store an episodic graph in the database."""
        if not self.driver:
            return False
        
        # Store all entities
        for entity in episodic_graph.entities:
            await self.store_entity(entity)
        
        # Store all relationships
        for relationship in episodic_graph.relationships:
            await self.store_relationship(relationship)
        
        # Create episode node
        with self.driver.session() as session:
            query = """
            MERGE (ep:Episode {id: $id})
            SET ep.session_id = $session_id,
                ep.created_at = $created_at,
                ep.updated_at = $updated_at,
                ep.message_ids = $message_ids
            WITH ep
            MATCH (e:Entity {session_id: $session_id})
            MERGE (ep)-[:CONTAINS]->(e)
            RETURN ep
            """
            
            result = session.run(
                query,
                id=episodic_graph.id,
                session_id=episodic_graph.session_id,
                created_at=episodic_graph.created_at.isoformat(),
                updated_at=episodic_graph.updated_at.isoformat(),
                message_ids=json.dumps(episodic_graph.message_ids)
            )
            
            return result.single() is not None
    
    async def handle_negation(self, original_rel_id: str, negating_rel_id: str, 
                            session_id: str, message_id: str) -> NegationEvent:
        """Handle relationship negation in the graph."""
        if not self.driver:
            return None
        
        negation_event = NegationEvent(
            id=str(uuid.uuid4()),
            original_relationship_id=original_rel_id,
            negating_relationship_id=negating_rel_id,
            negation_timestamp=datetime.utcnow(),
            session_id=session_id,
            message_id=message_id
        )
        
        with self.driver.session() as session:
            # Mark original relationship as negated
            query_deactivate = """
            MATCH ()-[r:RELATES_TO {id: $original_id}]-()
            SET r.is_active = false,
                r.negated_by_relationship_id = $negating_id,
                r.negated_at = $timestamp
            RETURN r
            """
            
            session.run(
                query_deactivate,
                original_id=original_rel_id,
                negating_id=negating_rel_id,
                timestamp=negation_event.negation_timestamp.isoformat()
            )
            
            # Update negating relationship
            query_update = """
            MATCH ()-[r:RELATES_TO {id: $negating_id}]-()
            SET r.negates_relationship_id = $original_id
            RETURN r
            """
            
            session.run(
                query_update,
                negating_id=negating_rel_id,
                original_id=original_rel_id
            )
            
            # Store negation event
            query_event = """
            CREATE (n:NegationEvent {
                id: $id,
                original_relationship_id: $original_id,
                negating_relationship_id: $negating_id,
                timestamp: $timestamp,
                session_id: $session_id,
                message_id: $message_id
            })
            RETURN n
            """
            
            session.run(
                query_event,
                id=negation_event.id,
                original_id=original_rel_id,
                negating_id=negating_rel_id,
                timestamp=negation_event.negation_timestamp.isoformat(),
                session_id=session_id,
                message_id=message_id
            )
        
        # Trigger community graph update
        await self.update_community_graph_after_negation(original_rel_id, negating_rel_id)
        
        return negation_event
    
    async def detect_communities(self) -> List[Community]:
        """Detect communities in the graph using Louvain algorithm simulation."""
        if not self.driver:
            return []
        
        communities = []
        
        with self.driver.session() as session:
            # Get connected components as basic communities
            query = """
            MATCH (e:Entity)
            WHERE e.is_active <> false
            WITH collect(e) as entities
            UNWIND entities as entity
            MATCH path = (entity)-[:RELATES_TO*]-(connected:Entity)
            WHERE all(r in relationships(path) WHERE r.is_active = true)
            WITH entity, collect(DISTINCT connected) as component
            WITH collect({root: entity, members: component}) as components
            UNWIND components as comp
            WITH comp.root as root, comp.members as members
            WHERE size(members) > 1
            RETURN root.id as root_id, 
                   [m IN members | m.id] as member_ids,
                   [m IN members | m.name] as member_names
            LIMIT 100
            """
            
            result = session.run(query)
            
            seen_entities = set()
            for record in result:
                root_id = record["root_id"]
                member_ids = record["member_ids"]
                member_names = record["member_names"]
                
                # Skip if we've seen these entities
                if root_id in seen_entities:
                    continue
                
                for mid in member_ids:
                    seen_entities.add(mid)
                
                # Create community
                community = Community(
                    id=str(uuid.uuid4()),
                    name=f"Community_{member_names[0][:20]}",
                    description=f"Community centered around {', '.join(member_names[:3])}",
                    entity_ids=set(member_ids),
                    central_entities=[root_id],
                    properties={
                        "size": len(member_ids),
                        "detected_at": datetime.utcnow().isoformat()
                    }
                )
                communities.append(community)
        
        return communities
    
    async def build_community_graph(self) -> CommunityGraph:
        """Build a higher-level community graph."""
        if not self.driver:
            return None
        
        communities = await self.detect_communities()
        
        community_graph = CommunityGraph(
            id=str(uuid.uuid4()),
            communities=communities
        )
        
        # Detect inter-community relationships
        with self.driver.session() as session:
            for i, comm1 in enumerate(communities):
                for comm2 in communities[i+1:]:
                    # Check for relationships between communities
                    query = """
                    MATCH (e1:Entity)-[r:RELATES_TO]->(e2:Entity)
                    WHERE e1.id IN $comm1_ids AND e2.id IN $comm2_ids
                       AND r.is_active = true
                    RETURN count(r) as rel_count,
                           collect(DISTINCT r.type) as rel_types
                    """
                    
                    result = session.run(
                        query,
                        comm1_ids=list(comm1.entity_ids),
                        comm2_ids=list(comm2.entity_ids)
                    )
                    
                    record = result.single()
                    if record and record["rel_count"] > 0:
                        inter_rel = {
                            "source_community_id": comm1.id,
                            "target_community_id": comm2.id,
                            "relationship_count": record["rel_count"],
                            "relationship_types": record["rel_types"]
                        }
                        community_graph.inter_community_relationships.append(inter_rel)
        
        # Store community graph in database
        await self.store_community_graph(community_graph)
        
        return community_graph
    
    async def store_community_graph(self, community_graph: CommunityGraph) -> bool:
        """Store community graph in the database."""
        if not self.driver:
            return False
        
        with self.driver.session() as session:
            # Store each community
            for community in community_graph.communities:
                query = """
                MERGE (c:Community {id: $id})
                SET c.name = $name,
                    c.description = $description,
                    c.entity_ids = $entity_ids,
                    c.central_entities = $central_entities,
                    c.properties = $properties,
                    c.created_at = $created_at,
                    c.updated_at = $updated_at,
                    c.confidence = $confidence
                WITH c
                UNWIND $entity_ids as entity_id
                MATCH (e:Entity {id: entity_id})
                MERGE (c)-[:INCLUDES]->(e)
                RETURN c
                """
                
                session.run(
                    query,
                    id=community.id,
                    name=community.name,
                    description=community.description,
                    entity_ids=list(community.entity_ids),
                    central_entities=community.central_entities,
                    properties=json.dumps(community.properties),
                    created_at=community.created_at.isoformat(),
                    updated_at=community.updated_at.isoformat(),
                    confidence=community.confidence
                )
            
            # Store inter-community relationships
            for inter_rel in community_graph.inter_community_relationships:
                query = """
                MATCH (c1:Community {id: $source_id})
                MATCH (c2:Community {id: $target_id})
                MERGE (c1)-[r:CONNECTED_TO]->(c2)
                SET r.relationship_count = $rel_count,
                    r.relationship_types = $rel_types
                RETURN r
                """
                
                session.run(
                    query,
                    source_id=inter_rel["source_community_id"],
                    target_id=inter_rel["target_community_id"],
                    rel_count=inter_rel["relationship_count"],
                    rel_types=json.dumps(inter_rel["relationship_types"])
                )
        
        return True
    
    async def update_community_graph_after_negation(self, original_rel_id: str, negating_rel_id: str):
        """Update community graph after a negation event."""
        if not self.driver:
            return
        
        with self.driver.session() as session:
            # Find affected communities
            query = """
            MATCH ()-[r:RELATES_TO {id: $original_id}]-()
            MATCH (r)-[:RELATES_TO]-(e:Entity)<-[:INCLUDES]-(c:Community)
            RETURN DISTINCT c.id as community_id
            """
            
            result = session.run(query, original_id=original_rel_id)
            affected_communities = [record["community_id"] for record in result]
            
            # Recompute affected communities
            for comm_id in affected_communities:
                # Check if community still has valid relationships
                query_check = """
                MATCH (c:Community {id: $comm_id})-[:INCLUDES]->(e:Entity)
                MATCH (e)-[r:RELATES_TO]-(other:Entity)
                WHERE r.is_active = true
                RETURN count(r) as active_rel_count
                """
                
                result = session.run(query_check, comm_id=comm_id)
                record = result.single()
                
                if record and record["active_rel_count"] == 0:
                    # Dissolve community if no active relationships
                    query_dissolve = """
                    MATCH (c:Community {id: $comm_id})
                    SET c.dissolved_at = $timestamp,
                        c.dissolved_reason = 'No active relationships after negation'
                    """
                    
                    session.run(
                        query_dissolve,
                        comm_id=comm_id,
                        timestamp=datetime.utcnow().isoformat()
                    )
                else:
                    # Update community confidence
                    query_update = """
                    MATCH (c:Community {id: $comm_id})
                    SET c.updated_at = $timestamp,
                        c.confidence = c.confidence * 0.9
                    """
                    
                    session.run(
                        query_update,
                        comm_id=comm_id,
                        timestamp=datetime.utcnow().isoformat()
                    )
        
        # Rebuild community graph if significant changes
        if len(affected_communities) > 0:
            await self.build_community_graph()
    
    async def get_entity_history(self, entity_id: str) -> List[Dict[str, Any]]:
        """Get the history of an entity including all relationships and negations."""
        if not self.driver:
            return []
        
        with self.driver.session() as session:
            query = """
            MATCH (e:Entity {id: $entity_id})
            OPTIONAL MATCH (e)-[r:RELATES_TO]-()
            OPTIONAL MATCH (n:NegationEvent)
            WHERE n.original_relationship_id = r.id 
               OR n.negating_relationship_id = r.id
            RETURN e, collect(DISTINCT r) as relationships, 
                   collect(DISTINCT n) as negations
            """
            
            result = session.run(query, entity_id=entity_id)
            record = result.single()
            
            if not record:
                return []
            
            history = {
                "entity": dict(record["e"]),
                "relationships": [dict(r) for r in record["relationships"]],
                "negations": [dict(n) for n in record["negations"]]
            }
            
            return [history]
    
    async def query_graph(self, cypher_query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a custom Cypher query."""
        if not self.driver:
            return []
        
        with self.driver.session() as session:
            result = session.run(cypher_query, parameters or {})
            return [dict(record) for record in result]
