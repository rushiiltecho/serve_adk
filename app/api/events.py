"""Enhanced event management endpoints with full async support."""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Path, Query
from sse_starlette.sse import EventSourceResponse
from app.models.requests import EventAppendRequest
from app.models.responses import EventResponse, EventListResponse
from app.services.event_service import event_service
from app.core.errors import EventAppendError, SessionNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Events"])


@router.post(
    "/agents/{agent_id}/users/{user_id}/sessions/{session_id}/events",
    response_model=EventResponse,
    summary="Append event to session"
)
async def append_event(
    agent_id: str = Path(..., description="Agent Engine resource ID"),
    user_id: str = Path(..., description="User ID"),
    session_id: str = Path(..., description="Session ID"),
    request: EventAppendRequest = ...
):
    """
    Append an event to a session.
    
    Events are the primary way to update session state in ADK.
    Use the state_delta field in actions to update session state.
    
    This endpoint is critical for:
    - Recording user messages
    - Recording agent responses
    - Updating session state via state_delta
    - Recording function calls and responses
    """
    try:
        return await event_service.append_event_async(
            agent_id, session_id, request
        )

    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except EventAppendError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to append event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/agents/{agent_id}/users/{user_id}/sessions/{session_id}/events",
    response_model=EventListResponse,
    summary="List session events with pagination"
)
async def list_events(
    agent_id: str = Path(..., description="Agent Engine resource ID"),
    user_id: str = Path(..., description="User ID"),
    session_id: str = Path(..., description="Session ID"),
    page_size: int = Query(50, ge=1, le=100, description="Number of results per page"),
    page_token: Optional[str] = Query(None, description="Token for pagination"),
    filter: Optional[str] = Query(None, description="Filter expression (e.g., author='user')"),
    order_by: Optional[str] = Query(None, description="Sort order (e.g., timestamp desc)")
):
    """
    List events in a session with filtering and pagination.
    
    Events represent the conversation history and state changes.
    
    Filter examples:
    - author='user' - Only user messages
    - author='agent' - Only agent responses
    - timestamp > 1234567890 - Events after timestamp
    """
    try:
        return await event_service.list_events_async(
            agent_id=agent_id,
            session_id=session_id,
            page_size=page_size,
            page_token=page_token,
            filter_expr=filter,
            order_by=order_by
        )

    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to list events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/agents/{agent_id}/users/{user_id}/sessions/{session_id}/events/{event_id}",
    summary="Get a specific event"
)
async def get_event(
    agent_id: str = Path(..., description="Agent Engine resource ID"),
    user_id: str = Path(..., description="User ID"),
    session_id: str = Path(..., description="Session ID"),
    event_id: str = Path(..., description="Event ID")
):
    """
    Get details of a specific event by ID.
    """
    try:
        return await event_service.get_event(agent_id, session_id, event_id)

    except Exception as e:
        logger.error(f"Failed to get event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/agents/{agent_id}/users/{user_id}/sessions/{session_id}/events/{event_id}",
    summary="Delete an event"
)
async def delete_event(
    agent_id: str = Path(..., description="Agent Engine resource ID"),
    user_id: str = Path(..., description="User ID"),
    session_id: str = Path(..., description="Session ID"),
    event_id: str = Path(..., description="Event ID")
):
    """
    Delete a specific event from a session.
    """
    try:
        success = await event_service.delete_event(agent_id, session_id, event_id)
        
        return {"success": success, "message": "Event deleted"}

    except Exception as e:
        logger.error(f"Failed to delete event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/agents/{agent_id}/users/{user_id}/sessions/{session_id}/events/stream",
    summary="Stream events in real-time"
)
async def stream_events(
    agent_id: str = Path(..., description="Agent Engine resource ID"),
    user_id: str = Path(..., description="User ID"),
    session_id: str = Path(..., description="Session ID"),
    start_timestamp: Optional[float] = Query(None, description="Start from this timestamp")
):
    """
    Stream events from a session in real-time using Server-Sent Events.
    
    This is useful for monitoring active sessions or building real-time UIs.
    """
    try:
        async def event_generator():
            """Generate SSE events from event stream."""
            try:
                async for event in event_service.stream_events(
                    agent_id, session_id, start_timestamp
                ):
                    yield {
                        "event": "event",
                        "data": event
                    }
            except Exception as e:
                logger.error(f"Stream error: {e}")
                yield {
                    "event": "error",
                    "data": {"error": str(e)}
                }
        
        return EventSourceResponse(event_generator())
    
    except Exception as e:
        logger.error(f"Failed to stream events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/agents/{agent_id}/users/{user_id}/sessions/{session_id}/conversation",
    summary="Get formatted conversation history"
)
async def get_conversation_history(
    agent_id: str = Path(..., description="Agent Engine resource ID"),
    user_id: str = Path(..., description="User ID"),
    session_id: str = Path(..., description="Session ID"),
    max_turns: Optional[int] = Query(None, description="Maximum number of conversation turns")
):
    """
    Get formatted conversation history with user and agent messages paired.
    
    This endpoint formats events into conversational turns for easier display.
    """
    try:
        return await event_service.get_conversation_history(
            agent_id, session_id, max_turns
        )

    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))