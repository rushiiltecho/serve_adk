"""Agent query endpoints."""
import logging
from fastapi import APIRouter, HTTPException, Depends
from sse_starlette.sse import EventSourceResponse
from models.requests import QueryRequest
from models.responses import QueryResponse
from services.agent_service import agent_service_factory
from core.streaming import create_sse_event, SSEEventType
from core.errors import AgentNotFoundError, AgentEngineError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.get("", response_model=list)
async def list_agents():
    """List all configured agents."""
    return agent_service_factory.list_agents()


@router.post("/{agent_id}/query", response_model=QueryResponse)
async def query_agent(agent_id: str, request: QueryRequest):
    """
    Query a deployed agent (non-streaming).
    
    Args:
        agent_id: The agent's ID
        request: Query request with user message
    
    Returns:
        Complete query response with agent's reply
    """
    try:
        agent_service = agent_service_factory.get_agent_service(agent_id)
        response = await agent_service.query(request)
        return response
    
    except AgentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AgentEngineError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{agent_id}/stream_query")
async def stream_query_agent(agent_id: str, request: QueryRequest):
    """
    Query a deployed agent with streaming (SSE).
    
    Args:
        agent_id: The agent's ID
        request: Query request with user message
    
    Returns:
        Server-Sent Events stream of agent responses
    """
    try:
        agent_service = agent_service_factory.get_agent_service(agent_id)
        
        async def event_generator():
            """Generate SSE events from agent stream."""
            try:
                # Send start event
                yield await create_sse_event(
                    event_type=SSEEventType.MESSAGE_START,
                    data={"session_id": request.session_id, "user_id": request.user_id}
                )
                
                # Stream events from agent
                async for event_dict in agent_service.stream_query(request):
                    # Determine event type
                    event_type = SSEEventType.CONTENT_DELTA
                    
                    if "actions" in event_dict:
                        actions = event_dict["actions"]
                        if actions.get("state_delta"):
                            event_type = "state_update"
                    
                    if "content" in event_dict:
                        content = event_dict["content"]
                        if content and "parts" in content:
                            for part in content["parts"]:
                                if "function_call" in part:
                                    event_type = SSEEventType.FUNCTION_CALL
                                elif "function_response" in part:
                                    event_type = SSEEventType.FUNCTION_RESPONSE
                    
                    # Send event
                    yield await create_sse_event(
                        event_type=event_type,
                        data=event_dict,
                        event_id=event_dict.get("id")
                    )
                
                # Send complete event
                yield await create_sse_event(
                    event_type=SSEEventType.MESSAGE_COMPLETE,
                    data={"status": "completed"}
                )
            
            except Exception as e:
                logger.error(f"Stream error: {e}")
                yield await create_sse_event(
                    event_type=SSEEventType.ERROR,
                    data={"error": str(e)}
                )
        
        return EventSourceResponse(event_generator())
    
    except AgentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AgentEngineError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Stream query failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")