"""Session management service with correct Vertex AI SDK methods."""
import logging
import time
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import vertexai
from app.config import settings
from app.models.requests import (
    SessionCreateRequest, 
    SessionStateUpdateRequest, 
    EventAppendRequest,
    SessionUpdateRequest
)
from app.models.responses import SessionResponse, SessionListResponse
from app.core.errors import SessionNotFoundError, InvalidStateUpdateError
from app.services.auth_service import auth_service

logger = logging.getLogger(__name__)


class SessionService:
    """Service for session operations using correct Vertex AI SDK."""
    
    def __init__(self):
        """Initialize session service."""
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Vertex AI client."""
        try:
            credentials = auth_service.get_credentials()
            self.client = vertexai.Client(
                project=settings.google_cloud_project,
                location=settings.google_cloud_location,
                credentials=credentials
            )
            
            if not self.client:
                raise RuntimeError("Vertex AI Client initialization returned None.")
            
            logger.info("Session service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize session service: {e}")
            raise
    
    def _build_session_name(self, agent_id: str, session_id: str = None) -> str:
        """Build session resource name."""
        base = (
            f"projects/{settings.google_cloud_project}/"
            f"locations/{settings.google_cloud_location}/"
            f"reasoningEngines/{agent_id}"
        )
        if session_id:
            return f"{base}/sessions/{session_id}"
        return base
    
    async def create_session(
        self,
        agent_id: str,
        request: SessionCreateRequest
    ) -> SessionResponse:
        """
        Create a new session.
        
        Args:
            agent_id: Agent Engine resource ID
            request: Session creation request
        
        Returns:
            SessionResponse with created session info
        """
        try:
            agent_name = self._build_session_name(agent_id)
            
            # Prepare config
            config = None
            if request.initial_state or (hasattr(request, 'session_config') and request.session_config):
                config = {}
                if request.initial_state:
                    config["state"] = request.initial_state
                if hasattr(request, 'session_config') and request.session_config:
                    config.update(request.session_config)
            
            # Create session - this is SYNCHRONOUS
            session_operation = self.client.agent_engines.sessions.create(
                name=agent_name,
                user_id=request.user_id,
                config=config
            )
            
            # Get the session from the operation response
            session = session_operation.response
            session_id = session.name.split("/")[-1]
            
            logger.info(f"Created session {session_id} for user {request.user_id}")
            
            return self._session_to_response(session, agent_id)
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    async def create_session_with_id(
        self,
        agent_id: str,
        session_id: str,
        request: SessionCreateRequest
    ) -> SessionResponse:
        """
        Create a session with a specific session ID.
        
        Note: The Vertex AI SDK doesn't support creating sessions with specific IDs directly.
        This creates a regular session and returns it.
        """
        # Vertex AI automatically assigns session IDs
        # We'll create a regular session
        return await self.create_session(agent_id, request)
    
    async def get_session(
        self,
        agent_id: str,
        session_id: str,
        user_id: Optional[str] = None
    ) -> SessionResponse:
        """
        Get session details.
        
        Args:
            agent_id: Agent Engine resource ID
            session_id: Session ID
            user_id: Optional user ID for verification
        
        Returns:
            SessionResponse with session details
        """
        try:
            session_name = self._build_session_name(agent_id, session_id)
            
            # Get session - SYNCHRONOUS
            get_response = self.client.agent_engines.sessions.get(
                name=session_name
            )
            
            # Access the session from response
            session = get_response.response if hasattr(get_response, 'response') else get_response
            
            # Verify user_id if provided
            if user_id and hasattr(session, 'user_id') and session.user_id != user_id:
                raise PermissionError(f"User {user_id} does not own session {session_id}")
            
            return self._session_to_response(session, agent_id)
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            if "not found" in str(e).lower():
                raise SessionNotFoundError(session_id)
            raise
    
    async def list_sessions(
        self,
        agent_id: str,
        user_id: Optional[str] = None,
        page_size: int = 50,
        page_token: Optional[str] = None,
        filter_expr: Optional[str] = None,
        order_by: Optional[str] = None
    ) -> SessionListResponse:
        """
        List sessions with filtering and pagination.
        
        Args:
            agent_id: Agent Engine resource ID
            user_id: Optional filter by user ID
            page_size: Number of results per page
            page_token: Token for pagination
            filter_expr: Filter expression
            order_by: Sort order
        
        Returns:
            SessionListResponse with sessions and pagination info
        """
        try:
            agent_name = self._build_session_name(agent_id)
            
            # Build config for list
            config = {}
            
            # Build filter
            filters = []
            if user_id:
                filters.append(f"user_id={user_id}")
            if filter_expr:
                filters.append(filter_expr)
            
            if filters:
                config["filter"] = " AND ".join(filters)
            
            if page_size:
                config["page_size"] = page_size
            if page_token:
                config["page_token"] = page_token
            if order_by:
                config["order_by"] = order_by
            
            sessions = []
            
            # List sessions - SYNCHRONOUS, returns iterator
            for session in self.client.agent_engines.sessions.list(
                name=agent_name,
                config=config if config else None
            ):
                session_response = self._session_to_response(session, agent_id)
                sessions.append(session_response)
            
            return SessionListResponse(
                sessions=sessions,
                next_page_token=None,  # SDK doesn't expose page token directly
                total_count=len(sessions)
            )
            
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            raise
    
    async def update_state(
        self,
        agent_id: str,
        session_id: str,
        request: SessionStateUpdateRequest
    ) -> SessionResponse:
        """
        Update session state using EventActions.state_delta.
        
        Args:
            agent_id: Agent Engine resource ID
            session_id: Session ID
            request: State update request
        
        Returns:
            SessionResponse with updated state
        """
        try:
            # Import here to avoid circular import
            from app.services.event_service import event_service
            
            # Prepare state_delta
            state_delta = request.state_delta
            
            # If replace=True, clear existing state first
            if request.replace:
                current_session = await self.get_session(agent_id, session_id, request.user_id)
                clear_delta = {k: None for k in current_session.state.keys()}
                state_delta = {**clear_delta, **request.state_delta}
            
            # Create event with state_delta
            event_request = EventAppendRequest(
                user_id=request.user_id,
                author="system",
                invocation_id=f"state-update-{uuid.uuid4().hex[:8]}",
                timestamp=time.time(),
                content_text=f"State updated: {len(state_delta)} keys",
                content_role="system",
                state_delta=state_delta
            )
            
            # Append event (updates state)
            await event_service.append_event(
                agent_id, session_id, event_request
            )
            
            # Return updated session
            return await self.get_session(agent_id, session_id, request.user_id)
            
        except Exception as e:
            logger.error(f"Failed to update session state: {e}")
            raise InvalidStateUpdateError(str(e))
    
    async def delete_session(
        self,
        agent_id: str,
        session_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Delete a session.
        
        Args:
            agent_id: Agent Engine resource ID
            session_id: Session ID
            user_id: Optional user ID for verification
        
        Returns:
            True if deleted successfully
        """
        try:
            # Verify ownership if user_id provided
            if user_id:
                await self.get_session(agent_id, session_id, user_id)
            
            session_name = self._build_session_name(agent_id, session_id)
            
            # Delete session - SYNCHRONOUS
            self.client.agent_engines.sessions.delete(
                name=session_name
            )
            
            logger.info(f"Deleted session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            if "not found" in str(e).lower():
                raise SessionNotFoundError(session_id)
            raise
    
    async def list_users(
        self,
        agent_id: str,
        page_size: int = 50,
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """List all users who have sessions with this agent."""
        try:
            sessions_response = await self.list_sessions(
                agent_id=agent_id,
                page_size=page_size,
                page_token=page_token
            )
            
            # Extract unique user IDs
            user_ids = set()
            for session in sessions_response.sessions:
                user_ids.add(session.user_id)
            
            return {
                "user_ids": sorted(list(user_ids)),
                "count": len(user_ids),
                "next_page_token": sessions_response.next_page_token
            }
            
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            raise
    
    async def get_session_stats(
        self,
        agent_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Get statistics for a session."""
        try:
            session = await self.get_session(agent_id, session_id)
            
            stats = {
                "session_id": session_id,
                "user_id": session.user_id,
                "event_count": session.event_count,
                "state_size": len(session.state),
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "age_seconds": (datetime.now(timezone.utc) - session.created_at).total_seconds(),
                "idle_seconds": (datetime.now(timezone.utc) - session.updated_at).total_seconds()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            raise
    
    def _session_to_response(
        self,
        session: Any,
        agent_id: str
    ) -> SessionResponse:
        """Convert Vertex AI Session to SessionResponse."""
        session_id = session.name.split("/")[-1]
        
        return SessionResponse(
            session_id=session_id,
            user_id=session.user_id if hasattr(session, 'user_id') else "",
            app_name=agent_id,
            state=dict(session.state) if hasattr(session, 'state') and session.state else {},
            event_count=len(session.events) if hasattr(session, 'events') else 0,
            created_at=datetime.fromtimestamp(
                session.create_time.timestamp(), 
                tz=timezone.utc
            ) if hasattr(session, 'create_time') else datetime.now(timezone.utc),
            updated_at=datetime.fromtimestamp(
                session.update_time.timestamp(),
                tz=timezone.utc
            ) if hasattr(session, 'update_time') else datetime.now(timezone.utc)
        )


# Global session service instance
session_service = SessionService()