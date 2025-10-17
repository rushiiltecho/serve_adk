"""Event management endpoints."""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Path, Query
from models.requests import EventAppendRequest
from models.responses import EventResponse
from services.event_service import event_service
from core.errors import EventAppendError, SessionNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Events"])


@router.post(
    "/agents/{agent_id}/users/{user_id}/sessions/{session_id}/events",
    response_model=EventResponse,
    summary="Append event to session"
)
async def append_event(
    agent_id: str = Path(..., description="Agent ID"),
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
        return await event_service.append_event(
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
    response_model=List[Dict[str, Any]],
    summary="List session events"
)
async def list_events(
    agent_id: str = Path(..., description="Agent ID"),
    user_id: str = Path(..., description="User ID"),
    session_id: str = Path(..., description="Session ID"),
    limit: Optional[int] = Query(None, description="Max events to return"),
    offset: Optional[int] = Query(None, description="Number of events to skip")
):
    """
    List events in a session.
    
    Events represent the conversation history and state changes.
    """
    try:
        return await event_service.list_events(
            agent_id, session_id, limit, offset
        )
    
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to list events: {e}")
        raise HTTPException(status_code=500, detail=str(e))