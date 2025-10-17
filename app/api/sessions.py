"""Enhanced session management endpoints with full async support."""
import logging
import traceback
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Path, Query
from app.models.requests import (
    SessionCreateRequest, 
    SessionStateUpdateRequest,
    SessionUpdateRequest
)
from app.models.responses import SessionResponse, SessionListResponse
from app.services.session_service import session_service
from app.core.errors import SessionNotFoundError, InvalidStateUpdateError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Sessions"])


@router.post(
    "/agents/{agent_id}/users/{user_id}/sessions",
    response_model=SessionResponse,
    summary="Create a new session"
)
async def create_session(
    agent_id: str = Path(..., description="Agent Engine resource ID"),
    user_id: str = Path(..., description="User ID"),
    request: Optional[SessionCreateRequest] = None
):
    """
    Create a new session for a user with an agent.
    
    The session can optionally include initial state and configuration.
    """
    try:
        if not request:
            request = SessionCreateRequest(user_id=user_id)
        
        return await session_service.create_session(agent_id, request)
    
    except Exception as e:
        logger.error(f"Failed to create session: {e}\n{traceback.print_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/agents/{agent_id}/users/{user_id}/sessions/{session_id}",
    response_model=SessionResponse,
    summary="Create session with specific ID"
)
async def create_session_with_id(
    agent_id: str = Path(..., description="Agent Engine resource ID"),
    user_id: str = Path(..., description="User ID"),
    session_id: str = Path(..., description="Session ID"),
    request: Optional[SessionCreateRequest] = None
):
    """
    Create a session with a specific session ID.
    
    This allows you to control the session ID instead of auto-generating one.
    """
    try:
        if not request:
            request = SessionCreateRequest(user_id=user_id, session_id=session_id)
        else:
            request.session_id = session_id
        
        return await session_service.create_session_with_id(agent_id, session_id, request)
    
    except Exception as e:
        logger.error(f"Failed to create session with ID {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/agents/{agent_id}/users/{user_id}/sessions/{session_id}",
    response_model=SessionResponse,
    summary="Get session details"
)
async def get_session(
    agent_id: str = Path(..., description="Agent Engine resource ID"),
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
    response_model=SessionListResponse,
    summary="List user sessions with pagination"
)
async def list_sessions(
    agent_id: str = Path(..., description="Agent Engine resource ID"),
    user_id: str = Path(..., description="User ID to filter sessions"),
    page_size: int = Query(50, ge=1, le=100, description="Number of results per page"),
    page_token: Optional[str] = Query(None, description="Token for pagination"),
    filter: Optional[str] = Query(None, description="Filter expression"),
    order_by: Optional[str] = Query(None, description="Sort order")
):
    """
    List all sessions for a user with pagination support.
    
    Supports filtering and custom sorting.
    """
    try:
        return await session_service.list_sessions(
            agent_id=agent_id,
            user_id=user_id,
            page_size=page_size,
            page_token=page_token,
            filter_expr=filter,
            order_by=order_by
        )
    
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/agents/{agent_id}/sessions",
    response_model=SessionListResponse,
    summary="List all sessions for an agent"
)
async def list_all_sessions(
    agent_id: str = Path(..., description="Agent Engine resource ID"),
    page_size: int = Query(50, ge=1, le=100, description="Number of results per page"),
    page_token: Optional[str] = Query(None, description="Token for pagination"),
    filter: Optional[str] = Query(None, description="Filter expression"),
    order_by: Optional[str] = Query(None, description="Sort order")
):
    """
    List all sessions for an agent across all users.
    
    Useful for admin views and analytics.
    """
    try:
        return await session_service.list_sessions(
            agent_id=agent_id,
            user_id=None,  # No user filter
            page_size=page_size,
            page_token=page_token,
            filter_expr=filter,
            order_by=order_by
        )
    
    except Exception as e:
        logger.error(f"Failed to list all sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/agents/{agent_id}/users/{user_id}/sessions/{session_id}",
    response_model=SessionResponse,
    summary="Update session configuration"
)
async def update_session(
    agent_id: str = Path(..., description="Agent Engine resource ID"),
    user_id: str = Path(..., description="User ID"),
    session_id: str = Path(..., description="Session ID"),
    request: SessionUpdateRequest = ...
):
    """
    Update session configuration parameters.
    
    This updates session-level settings, not the state.
    Use the /state endpoint to update session state.
    """
    try:
        return await session_service.update_session(agent_id, session_id, request)
    
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)+f"\n{traceback.print_exc()}")
    except Exception as e:
        logger.error(f"Failed to update session: {e}\n{traceback.print_exc()}")
        raise HTTPException(status_code=500, detail=str(e)+f"\n{traceback.print_exc()}")


@router.patch(
    "/agents/{agent_id}/users/{user_id}/sessions/{session_id}/state",
    response_model=SessionResponse,
    summary="Update session state"
)
async def update_session_state(
    agent_id: str = Path(..., description="Agent Engine resource ID"),
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
        return await session_service.update_state(agent_id, session_id, request)
    
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)+f"\n{traceback.print_exc()}")
    except InvalidStateUpdateError as e:
        raise HTTPException(status_code=400, detail=str(e)+f"\n{traceback.print_exc()}")
    except Exception as e:
        logger.error(f"Failed to update session state: {e}\n{traceback.print_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/agents/{agent_id}/users/{user_id}/sessions/{session_id}",
    summary="Delete session"
)
async def delete_session(
    agent_id: str = Path(..., description="Agent Engine resource ID"),
    user_id: str = Path(..., description="User ID"),
    session_id: str = Path(..., description="Session ID")
):
    """Delete a session and all its associated data."""
    try:
        success = await session_service.delete_session(agent_id, session_id, user_id)
        
        return {"success": success, "message": "Session deleted"}
    
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)+f"\n{traceback.print_exc()}")
    except Exception as e:
        logger.error(f"Failed to delete session: {e}\n{traceback.print_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/agents/{agent_id}/users",
    summary="List all users"
)
async def list_users(
    agent_id: str = Path(..., description="Agent Engine resource ID"),
    page_size: int = Query(50, ge=1, le=100, description="Number of results per page"),
    page_token: Optional[str] = Query(None, description="Token for pagination")
):
    """
    List all users who have sessions with this agent.
    
    Returns unique user IDs from all sessions.
    """
    try:
        return await session_service.list_users(
            agent_id=agent_id,
            page_size=page_size,
            page_token=page_token
        )
    
    except Exception as e:
        logger.error(f"Failed to list users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/agents/{agent_id}/users/{user_id}/sessions/{session_id}/stats",
    summary="Get session statistics"
)
async def get_session_stats(
    agent_id: str = Path(..., description="Agent Engine resource ID"),
    user_id: str = Path(..., description="User ID"),
    session_id: str = Path(..., description="Session ID")
):
    """
    Get statistics and metrics for a session.
    
    Includes event count, state size, age, idle time, etc.
    """
    try:
        return await session_service.get_session_stats(agent_id, session_id)
    
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get session stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))