"""Event management service with correct Vertex AI SDK methods."""
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from google.genai import types as genai_types
from google.adk.events import EventActions
import vertexai
from app.config import settings
from app.models.requests import EventAppendRequest
from app.models.responses import EventResponse, EventListResponse
from app.core.errors import EventAppendError, SessionNotFoundError
from app.services.auth_service import auth_service
from app.utils.converters import adk_event_to_dict

logger = logging.getLogger(__name__)


class EventService:
    """Service for event operations using correct Vertex AI SDK."""
    
    def __init__(self):
        """Initialize event service."""
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
            
            logger.info("Event service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize event service: {e}")
            raise
    
    def _build_session_name(self, agent_id: str, session_id: str) -> str:
        """Build session resource name."""
        return (
            f"projects/{settings.google_cloud_project}/"
            f"locations/{settings.google_cloud_location}/"
            f"reasoningEngines/{agent_id}/"
            f"sessions/{session_id}"
        )
    
    async def append_event(
        self,
        agent_id: str,
        session_id: str,
        request: EventAppendRequest
    ) -> EventResponse:
        """
        Append event to session.
        
        Args:
            agent_id: Agent Engine resource ID
            session_id: Session ID
            request: Event append request
        
        Returns:
            EventResponse with event_id and updated session state
        """
        try:
            session_name = self._build_session_name(agent_id, session_id)
            
            # Build config
            config = {}
            
            # Add content if provided
            if request.content_text:
                config["content"] = {
                    "role": request.content_role,
                    "parts": [{"text": request.content_text}]
                }
            
            # Add actions if provided
            if any([request.state_delta, request.artifact_delta, 
                    request.transfer_to_agent, request.escalate is not None]):
                config["actions"] = {}
                if request.state_delta:
                    config["actions"]["state_delta"] = dict(request.state_delta)
                if request.artifact_delta:
                    config["actions"]["artifact_delta"] = dict(request.artifact_delta)
                if request.transfer_to_agent:
                    config["actions"]["transfer_to_agent"] = request.transfer_to_agent
                if request.escalate is not None:
                    config["actions"]["escalate"] = request.escalate
            
            timestamp = request.timestamp or time.time()
            
            # Append event - SYNCHRONOUS (no await)
            append_response = self.client.agent_engines.sessions.events.append(
                name=session_name,
                author=request.author,
                invocation_id=request.invocation_id,
                timestamp=datetime.fromtimestamp(timestamp, timezone.utc),
                config=config if config else None
            )
            
            logger.info(f"Appended event to session {session_id}")
            
            # Get updated session state - SYNCHRONOUS (no await)
            get_response = self.client.agent_engines.sessions.get(
                name=session_name
            )
            
            # Access the session from response
            session = get_response.response if hasattr(get_response, 'response') else get_response
            
            updated_state = dict(session.state) if hasattr(session, 'state') and session.state else {}
            
            # Generate event ID
            event_id = f"{request.invocation_id}-{int(timestamp * 1000)}"
            
            return EventResponse(
                event_id=event_id,
                session_state=updated_state,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Failed to append event: {e}")
            raise EventAppendError(str(e))
    
    async def list_events(
        self,
        agent_id: str,
        session_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List events with simple limit/offset pagination.
        
        Args:
            agent_id: Agent Engine resource ID
            session_id: Session ID
            limit: Maximum number of events
            offset: Number of events to skip
        
        Returns:
            List of event dictionaries
        """
        try:
            session_name = self._build_session_name(agent_id, session_id)
            
            events = []
            count = 0
            
            # List events - SYNCHRONOUS, returns iterator
            for event in self.client.agent_engines.list_session_events(
                name=session_name
            ):
                # Apply offset
                if offset and count < offset:
                    count += 1
                    continue
                
                # Convert to dict
                event_dict = adk_event_to_dict(event)
                events.append(event_dict)
                count += 1
                
                # Apply limit
                if limit and len(events) >= limit:
                    break
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to list events: {e}")
            if "not found" in str(e).lower():
                raise SessionNotFoundError(session_id)
            raise
    
    async def list_events_async(
        self,
        agent_id: str,
        session_id: str,
        page_size: Optional[int] = 50,
        page_token: Optional[str] = None,
        filter_expr: Optional[str] = None,
        order_by: Optional[str] = None
    ) -> EventListResponse:
        """
        List events in a session with filtering and pagination.
        
        Args:
            agent_id: Agent Engine resource ID
            session_id: Session ID
            page_size: Number of events per page
            page_token: Token for pagination
            filter_expr: Filter expression
            order_by: Sort order
        
        Returns:
            EventListResponse with events and pagination info
        """
        try:
            session_name = self._build_session_name(agent_id, session_id)
            
            events = []
            count = 0
            
            # List events - SYNCHRONOUS
            for event in self.client.agent_engines.list_session_events(
                name=session_name
            ):
                event_dict = adk_event_to_dict(event)
                events.append(event_dict)
                count += 1
                
                if page_size and count >= page_size:
                    break
            
            return EventListResponse(
                events=events,
                next_page_token=None,
                total_count=len(events)
            )
            
        except Exception as e:
            logger.error(f"Failed to list events: {e}")
            if "not found" in str(e).lower():
                raise SessionNotFoundError(session_id)
            raise
    
    async def get_conversation_history(
        self,
        agent_id: str,
        session_id: str,
        max_turns: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get formatted conversation history.
        
        Args:
            agent_id: Agent Engine resource ID
            session_id: Session ID
            max_turns: Maximum number of conversation turns
        
        Returns:
            List of conversation turns with user and agent messages
        """
        try:
            # Get all events
            events = await self.list_events(agent_id, session_id)
            
            # Group events by invocation and extract conversations
            conversations = []
            current_turn = {"user": None, "agent": None}
            
            for event in events:
                if event["author"] == "user":
                    if current_turn["user"] is not None:
                        conversations.append(current_turn)
                        current_turn = {"user": None, "agent": None}
                    current_turn["user"] = event
                elif event["author"] in ["agent", "model"]:
                    current_turn["agent"] = event
            
            # Add last turn
            if current_turn["user"] is not None:
                conversations.append(current_turn)
            
            # Apply max_turns limit
            if max_turns:
                conversations = conversations[-max_turns:]
            
            return conversations
            
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            raise


# Global event service instance
event_service = EventService()