"""Event management service."""
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from google.genai import types as genai_types
from google.adk.events import EventActions
import vertexai
from config import settings
from models.requests import EventAppendRequest
from models.responses import EventResponse
from core.errors import EventAppendError
from services.auth_service import auth_service
from utils.converters import adk_event_to_dict, create_adk_event

logger = logging.getLogger(__name__)


class EventService:
    """Service for event operations."""
    
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
            logger.info("Event service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize event service: {e}")
            raise
    
    async def append_event(
        self,
        agent_id: str,
        session_id: str,
        request: EventAppendRequest
    ) -> EventResponse:
        """
        Append event to session.
        
        CRITICAL: This is how state updates work in ADK.
        Events with EventActions.state_delta update the session state.
        
        Args:
            agent_id: Agent ID
            session_id: Session ID
            request: Event append request
        
        Returns:
            EventResponse with event_id and updated session state
        """
        try:
            session_name = (
                f"projects/{settings.google_cloud_project}/"
                f"locations/{settings.google_cloud_location}/"
                f"reasoningEngines/{agent_id}/"
                f"sessions/{session_id}"
            )
            
            # Build content if provided
            content = None
            if request.content_text:
                content = genai_types.Content(
                    role=request.content_role,
                    parts=[genai_types.Part(text=request.content_text)]
                )
            
            # Build actions
            actions = EventActions()
            if request.state_delta:
                actions.state_delta = request.state_delta
            if request.artifact_delta:
                actions.artifact_delta = request.artifact_delta
            if request.transfer_to_agent:
                actions.transfer_to_agent = request.transfer_to_agent
            if request.escalate is not None:
                actions.escalate = request.escalate
            
            # Create ADK event
            timestamp = request.timestamp or time.time()
            adk_event = create_adk_event(
                author=request.author,
                invocation_id=request.invocation_id,
                timestamp=timestamp,
                content=content,
                actions=actions
            )
            
            # Prepare config for API call
            config = {}
            
            if content:
                config["content"] = {
                    "role": content.role,
                    "parts": [{"text": part.text} for part in content.parts if hasattr(part, 'text')]
                }
            
            if actions.state_delta or actions.artifact_delta or actions.transfer_to_agent or actions.escalate:
                config["actions"] = {}
                if actions.state_delta:
                    config["actions"]["state_delta"] = dict(actions.state_delta)
                if actions.artifact_delta:
                    config["actions"]["artifact_delta"] = dict(actions.artifact_delta)
                if actions.transfer_to_agent:
                    config["actions"]["transfer_to_agent"] = actions.transfer_to_agent
                if actions.escalate is not None:
                    config["actions"]["escalate"] = actions.escalate
            
            # Append event using Vertex AI SDK
            await self.client.agent_engines.sessions.events.append(
                name=session_name,
                author=request.author,
                invocation_id=request.invocation_id,
                timestamp=datetime.fromtimestamp(timestamp),
                config=config if config else None
            )
            
            logger.info(f"Appended event to session {session_id}")
            
            # Get updated session to return current state
            session_response = await self.client.agent_engines.sessions.get(
                name=session_name
            )
            
            updated_state = dict(session_response.response.state) if hasattr(session_response.response, 'state') and session_response.response.state else {}
            
            return EventResponse(
                event_id=adk_event.id,
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
        List events in a session.
        
        Args:
            agent_id: Agent ID
            session_id: Session ID
            limit: Maximum number of events to return
            offset: Number of events to skip
        
        Returns:
            List of event dictionaries
        """
        try:
            session_name = (
                f"projects/{settings.google_cloud_project}/"
                f"locations/{settings.google_cloud_location}/"
                f"reasoningEngines/{agent_id}/"
                f"sessions/{session_id}"
            )
            
            events = []
            count = 0
            
            async for event in self.client.agent_engines.list_session_events(
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
            raise


# Global event service instance
event_service = EventService()