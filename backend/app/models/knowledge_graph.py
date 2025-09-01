"""Data models for knowledge graph components."""

from datetime import datetime
from typing import List, Optional, Dict, Any, Set
from pydantic import BaseModel, Field
from enum import Enum


class EntityType(str, Enum):
    """Types of entities in the knowledge graph."""
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    CONCEPT = "concept"
    EVENT = "event"
    OBJECT = "object"
    DATE = "date"
    QUANTITY = "quantity"
    UNKNOWN = "unknown"


class RelationType(str, Enum):
    """Types of relationships between entities."""
    IS_A = "is_a"
    HAS = "has"
    BELONGS_TO = "belongs_to"
    LOCATED_IN = "located_in"
    WORKS_FOR = "works_for"
    KNOWS = "knows"
    CREATED_BY = "created_by"
    PART_OF = "part_of"
    RELATED_TO = "related_to"
    CAUSES = "causes"
    PREVENTS = "prevents"
    NEGATES = "negates"
    UPDATES = "updates"
    TEMPORAL_BEFORE = "temporal_before"
    TEMPORAL_AFTER = "temporal_after"
    UNKNOWN = "unknown"


class Entity(BaseModel):
    """Entity in the knowledge graph."""
    id: str
    name: str
    type: EntityType
    properties: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_text: Optional[str] = None
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    session_id: str
    message_id: Optional[str] = None


class Relationship(BaseModel):
    """Relationship between entities."""
    id: str
    source_entity_id: str
    target_entity_id: str
    type: RelationType
    properties: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    session_id: str
    message_id: Optional[str] = None
    negates_relationship_id: Optional[str] = None  # ID of relationship this negates
    negated_by_relationship_id: Optional[str] = None  # ID of relationship that negates this
    is_active: bool = True  # False if negated


class EpisodicGraph(BaseModel):
    """Episodic graph for a specific conversation or time period."""
    id: str
    session_id: str
    entities: List[Entity] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    message_ids: List[str] = Field(default_factory=list)
    
    def add_entity(self, entity: Entity):
        """Add an entity to the episodic graph."""
        if entity not in self.entities:
            self.entities.append(entity)
            self.updated_at = datetime.utcnow()
    
    def add_relationship(self, relationship: Relationship):
        """Add a relationship to the episodic graph."""
        if relationship not in self.relationships:
            self.relationships.append(relationship)
            self.updated_at = datetime.utcnow()


class Community(BaseModel):
    """Community of related entities in the graph."""
    id: str
    name: str
    description: Optional[str] = None
    entity_ids: Set[str] = Field(default_factory=set)
    central_entities: List[str] = Field(default_factory=list)  # Most important entities
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class CommunityGraph(BaseModel):
    """Higher-level community graph."""
    id: str
    communities: List[Community] = Field(default_factory=list)
    inter_community_relationships: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def add_community(self, community: Community):
        """Add a community to the graph."""
        if community not in self.communities:
            self.communities.append(community)
            self.updated_at = datetime.utcnow()


class NegationEvent(BaseModel):
    """Event representing a negation in the knowledge graph."""
    id: str
    original_relationship_id: str
    negating_relationship_id: str
    negation_timestamp: datetime
    session_id: str
    message_id: str
    reason: Optional[str] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class GraphUpdate(BaseModel):
    """Update event for the knowledge graph."""
    id: str
    update_type: str  # "add_entity", "add_relationship", "negate_relationship", "update_community"
    affected_entities: List[str] = Field(default_factory=list)
    affected_relationships: List[str] = Field(default_factory=list)
    affected_communities: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: str
    message_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
