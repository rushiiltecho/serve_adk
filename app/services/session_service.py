"""Session management service."""
import logging
import time
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import vertexai
from config import settings
from models.requests import SessionCreateRequest, SessionStateUpdateRequest, EventAppendRequest
from models.responses import SessionResponse
from core.errors import SessionNotFoundError, InvalidStateUpdateError
from services.auth_service import auth_service
from services.event_service import EventService

logger = logging.getLogger(__name__)


class SessionService:
    """Service for session operations."""
    
    def __init__(self):
        """Initialize session service."""
        self.client = None
        self.event_service = EventService()
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
            logger.info("Session service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize session service: {e}")
            raise
    
    async def create_session(
        self,
        agent_id: str,
        request: SessionCreateRequest
    ) -> SessionResponse:
        """
        Create a new session.
        
        Args:
            agent_id: Agent ID
            request: Session creation request
        
        Returns:
            SessionResponse with created session info
        """
        try:
            agent_name = (
                f"projects/{settings.google_cloud_project}/"
                f"locations/{settings.google_cloud_location}/"
                f"reasoningEngines/{agent_id}"
            )
            
            # Create session using Vertex AI SDK
            session_response = await self.client.agent_engines.sessions.create(
                name=agent_name,
                user_id=request.user_id
            )
            
            session_id = session_response.response.name.split("/")[-1]
            
            # If initial state provided, append event with state_delta
            if request.initial_state:
                state_update = SessionStateUpdateRequest(
                    user_id=request.user_id,
                    state_delta=request.initial_state,
                    replace=False
                )
                await self.update_state(agent_id, session_id, state_update)
            
            # Get updated session
            return await self.get_session(agent_id, session_id, request.user_id)
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    async def get_session(
        self,
        agent_id: str,
        session_id: str,
        user_id: str
    ) -> SessionResponse:
        """
        Get session details.
        
        Args:
            agent_id: Agent ID
            session_id: Session ID
            user_id: User ID for verification
        
        Returns:
            SessionResponse with session details
        """
        try:
            session_name = (
                f"projects/{settings.google_cloud_project}/"
                f"locations/{settings.google_cloud_location}/"
                f"reasoningEngines/{agent_id}/"
                f"sessions/{session_id}"
            )
            
            # Get session from Vertex AI
            response = await self.client.agent_engines.sessions.get(
                name=session_name
            )
            
            session = response.response
            
            # Convert to SessionResponse
            return SessionResponse(
                session_id=session_id,
                user_id=session.user_id if hasattr(session, 'user_id') else user_id,
                app_name=agent_id,
                state=dict(session.state) if hasattr(session, 'state') and session.state else {},
                event_count=len(session.events) if hasattr(session, 'events') else 0,
                created_at=datetime.fromtimestamp(session.create_time.timestamp()) if hasattr(session, 'create_time') else datetime.utcnow(),
                updated_at=datetime.fromtimestamp(session.update_time.timestamp()) if hasattr(session, 'update_time') else datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            if "not found" in str(e).lower():
                raise SessionNotFoundError(session_id)
            raise
    
    async def list_sessions(
        self,
        agent_id: str,
        user_id: str
    ) -> List[SessionResponse]:
        """
        List all sessions for a user.
        
        Args:
            agent_id: Agent ID
            user_id: User ID
        
        Returns:
            List of SessionResponse objects
        """
        try:
            agent_name = (
                f"projects/{settings.google_cloud_project}/"
                f"locations/{settings.google_cloud_location}/"
                f"reasoningEngines/{agent_id}"
            )
            
            sessions = []
            async for session in self.client.agent_engines.sessions.list(
                name=agent_name,
                filter=f"user_id={user_id}"
            ):
                session_id = session.name.split("/")[-1]
                sessions.append(
                    await self.get_session(agent_id, session_id, user_id)
                )
            
            return sessions
            
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
        
        This is the ADK-compatible way to update state.
        
        Args:
            agent_id: Agent ID
            session_id: Session ID
            request: State update request
        
        Returns:
            SessionResponse with updated state
        """
        try:
            # Prepare state_delta
            state_delta = request.state_delta
            
            # If replace=True, we need to clear existing state first
            if request.replace:
                current_session = await self.get_session(
                    agent_id, session_id, request.user_id
                )
                # Create delta that sets values to None (clears them)
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
            
            # Append event (this updates the state)
            await self.event_service.append_event(
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
        user_id: str
    ) -> bool:
        """
        Delete a session.
        
        Args:
            agent_id: Agent ID
            session_id: Session ID
            user_id: User ID for verification
        
        Returns:
            True if deleted successfully
        """
        try:
            session_name = (
                f"projects/{settings.google_cloud_project}/"
                f"locations/{settings.google_cloud_location}/"
                f"reasoningEngines/{agent_id}/"
                f"sessions/{session_id}"
            )
            
            await self.client.agent_engines.sessions.delete(name=session_name)
            logger.info(f"Deleted session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            if "not found" in str(e).lower():
                raise SessionNotFoundError(session_id)
            raise


# Global session service instance
session_service = SessionService()