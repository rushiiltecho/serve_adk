"""Session management endpoints."""
import logging
from typing import List
from fastapi import APIRouter, HTTPException, Path, Query
from models.requests import SessionCreateRequest, SessionStateUpdateRequest
from models.responses import SessionResponse
from services.session_service import session_service
from core.errors import SessionNotFoundError, InvalidStateUpdateError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Sessions"])


@router.post(
    "/agents/{agent_id}/users/{user_id}/sessions",
    response_model=SessionResponse,
    summary="Create a new session"
)
async def create_session(
    agent_id: str = Path(..., description="Agent ID"),
    user_id: str = Path(..., description="User ID"),
    request: SessionCreateRequest = None
):
    """
    Create a new session for a user with an agent.
    
    The session can optionally include initial state.
    """
    try:
        if not request:
            request = SessionCreateRequest(user_id=user_id)
        
        return await session_service.create_session(agent_id, request)
    
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/agents/{agent_id}/users/{user_id}/sessions/{session_id}",
    response_model=SessionResponse,
    summary="Create session with specific ID"
)
async def create_session_with_id(
    agent_id: str = Path(..., description="Agent ID"),
    user_id: str = Path(..., description="User ID"),
    session_id: str = Path(..., description="Session ID"),
    initial_state: dict = None
):
    """
    Create a session with a specific session ID.
    
    This allows you to control the session ID instead of auto-generating one.
    """
    try:
        request = SessionCreateRequest(
            user_id=user_id,
            session_id=session_id,
            initial_state=initial_state or {}
        )
        
        return await session_service.create_session(agent_id, request)
    
    except Exception as e:
        logger.error(f"Failed to create session with ID {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/agents/{agent_id}/users/{user_id}/sessions/{session_id}",
    response_model=SessionResponse,
    summary="Get session details"
)
async def get_session(
    agent_id: str = Path(..., description="Agent ID"),
    user_id: str = Path(..., description="User ID"),
    session_id: str = Path(..., description="Session ID")
):
    """Get details of a specific session."""
    try:
        return await session_service.get_session(agent_id, session_id, user_id)
    
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/agents/{agent_id}/users/{user_id}/sessions",
    response_model=List[SessionResponse],
    summary="List user sessions"
)
async def list_sessions(
    agent_id: str = Path(..., description="Agent ID"),
    user_id: str = Path(..., description="User ID")
):
    """List all sessions for a user with an agent."""
    try:
        return await session_service.list_sessions(agent_id, user_id)
    
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/agents/{agent_id}/users/{user_id}/sessions/{session_id}/state",
    response_model=SessionResponse,
    summary="Update session state"
)
async def update_session_state(
    agent_id: str = Path(..., description="Agent ID"),
    user_id: str = Path(..., description="User ID"),
    session_id: str = Path(..., description="Session ID"),
    request: SessionStateUpdateRequest = ...
):
    """
    Update session state using state_delta.
    
    This is the ADK-compatible way to modify session state.
    The state_delta contains key-value pairs to update.
    Set replace=True to clear existing state first.
    """
    try:
        return await session_service.update_state(
            agent_id, session_id, request
        )
    
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidStateUpdateError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update session state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/agents/{agent_id}/users/{user_id}/sessions/{session_id}",
    summary="Delete session"
)
async def delete_session(
    agent_id: str = Path(..., description="Agent ID"),
    user_id: str = Path(..., description="User ID"),
    session_id: str = Path(..., description="Session ID")
):
    """Delete a session and all its associated data."""
    try:
        success = await session_service.delete_session(
            agent_id, session_id, user_id
        )
        
        return {"success": success, "message": "Session deleted"}
    
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete session: {e}")
        raise HTTPException(status_code=500, detail=str(e))