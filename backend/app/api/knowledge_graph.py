"""Knowledge Graph API endpoints."""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Query
from ..services.knowledge_graph_service import knowledge_graph_service

router = APIRouter(prefix="/api/knowledge-graph", tags=["knowledge-graph"])


@router.get("/entity/{entity_name}")
async def get_entity_context(entity_name: str):
    """Get full context for an entity including relationships and history."""
    try:
        context = await knowledge_graph_service.get_entity_context(entity_name)
        return context
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/session/{session_id}/graph")
async def get_session_graph(session_id: str):
    """Get the complete graph for a session."""
    try:
        graph = await knowledge_graph_service.get_session_graph(session_id)
        return graph
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/communities")
async def get_community_insights():
    """Get insights from the community graph."""
    try:
        insights = await knowledge_graph_service.get_community_insights()
        return insights
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/query")
async def query_knowledge(query: Dict[str, str]):
    """Query the knowledge graph with natural language."""
    try:
        if "query" not in query:
            raise ValueError("Query text is required")
        
        results = await knowledge_graph_service.query_knowledge(query["query"])
        return results
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/statistics")
async def get_graph_statistics():
    """Get statistics about the knowledge graph."""
    try:
        stats = await knowledge_graph_service.get_graph_statistics()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/process")
async def process_text_for_knowledge(data: Dict[str, Any]):
    """Process text to extract entities and relationships."""
    try:
        required_fields = ["user_text", "response_text", "session_id"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"{field} is required")
        
        result = await knowledge_graph_service.process_chat_interaction(
            user_text=data["user_text"],
            response_text=data["response_text"],
            session_id=data["session_id"],
            message_id=data.get("message_id")
        )
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/entity/{entity_id}/history")
async def get_entity_history(entity_id: str):
    """Get the complete history of an entity including negations."""
    try:
        if not knowledge_graph_service.graph_manager.driver:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Neo4j connection not available"
            )
        
        history = await knowledge_graph_service.graph_manager.get_entity_history(entity_id)
        return {"entity_id": entity_id, "history": history}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/rebuild-communities")
async def rebuild_community_graph():
    """Manually trigger community graph rebuild."""
    try:
        if not knowledge_graph_service.graph_manager.driver:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Neo4j connection not available"
            )
        
        community_graph = await knowledge_graph_service.graph_manager.build_community_graph()
        
        if community_graph:
            return {
                "success": True,
                "communities_count": len(community_graph.communities),
                "inter_community_relationships": len(community_graph.inter_community_relationships)
            }
        else:
            return {"success": False, "message": "Failed to build community graph"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
