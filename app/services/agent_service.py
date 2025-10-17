"""Agent service for interacting with deployed agents."""
import logging
import os
from typing import AsyncGenerator, Dict, Any, Optional
import vertexai
from google.genai import types as genai_types
from app.config import AgentConfig, settings
from app.models.requests import QueryRequest
from app.models.responses import QueryResponse
from app.core.errors import AgentEngineError, AgentNotFoundError
from app.services.auth_service import auth_service
from app.utils.converters import adk_event_to_dict, content_to_dict

logger = logging.getLogger(__name__)


class AgentService:
    """Service for deployed agent operations."""
    
    def __init__(self, agent_config: AgentConfig):
        """Initialize agent service."""
        self.agent_config = agent_config
        self.client = None
        self.agent = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Vertex AI client and agent."""
        try:
            # Get credentials
            credentials = auth_service.get_credentials()
            
            # Initialize Vertex AI client
            self.client = vertexai.Client(
                project=self.agent_config.project_id,
                location=getattr(
                    self.agent_config, 
                    "location",
                    os.getenv("GOOGLE_CLOUD_LOCATION","us-central1")
                ),
                credentials=credentials
            )
            
            # Get agent engine instance
            agent_name = (
                f"projects/{self.agent_config.project_id}/"
                f"locations/{self.agent_config.location}/"
                f"reasoningEngines/{self.agent_config.agent_id}"
            )
            
            self.agent = self.client.agent_engines.get(name=agent_name)
            logger.info(f"Initialized agent: {self.agent_config.name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent {self.agent_config.name}: {e}")
            raise AgentEngineError(f"Agent initialization failed: {str(e)}", e)
    
    async def query(self, request: QueryRequest) -> QueryResponse:
        """
        Query the deployed agent (non-streaming).
        
        Args:
            request: Query request with user_id, message, etc.
        
        Returns:
            QueryResponse with agent's response and events
        """
        if not self.agent:
            raise AgentNotFoundError(self.agent_config.agent_id)
        
        try:
            # Convert message to Content
            user_content = genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=request.message)]
            )
            
            # Query the agent
            events_list = []
            final_response = ""
            session_id = request.session_id
            
            # Use async_stream_query and collect all events
            async for event in self.agent.async_stream_query(
                user_id=request.user_id,
                session_id=session_id,
                new_message=user_content
            ):
                # Convert event to dict
                event_dict = adk_event_to_dict(event)
                events_list.append(event_dict)
                
                # Extract text from content
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            final_response += part.text
                
                # Get session_id from first event
                if not session_id and hasattr(event, 'session_id'):
                    session_id = event.session_id
            
            # Extract usage metadata from events
            usage_metadata = self._extract_usage_metadata(events_list)
            
            return QueryResponse(
                session_id=session_id or f"new-session-{request.user_id}",
                response=final_response,
                events=events_list,
                usage_metadata=usage_metadata
            )
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise AgentEngineError(f"Query failed: {str(e)}", e)
    
    async def stream_query(
        self,
        request: QueryRequest
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream query results from deployed agent.
        
        Args:
            request: Query request
        
        Yields:
            Event dictionaries as they arrive
        """
        if not self.agent:
            raise AgentNotFoundError(self.agent_config.agent_id)
        
        try:
            # Convert message to Content
            user_content = genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=request.message)]
            )
            
            # Stream events from agent
            async for event in self.agent.async_stream_query(
                user_id=request.user_id,
                session_id=request.session_id,
                new_message=user_content
            ):
                # Convert and yield event
                event_dict = adk_event_to_dict(event)
                yield event_dict
                
        except Exception as e:
            logger.error(f"Stream query failed: {e}")
            raise AgentEngineError(f"Stream query failed: {str(e)}", e)
    
    def _extract_usage_metadata(self, events: list) -> Optional[Dict[str, Any]]:
        """Extract usage metadata from events."""
        for event in reversed(events):  # Check from latest event
            if "usage_metadata" in event:
                return event["usage_metadata"]
        return None


class AgentServiceFactory:
    """Factory for creating agent services."""
    
    def __init__(self):
        self._services: Dict[str, AgentService] = {}
    
    def get_agent_service(self, agent_id: str) -> AgentService:
        """Get or create agent service for given agent_id."""
        if agent_id in self._services:
            return self._services[agent_id]
        
        # Get agent config
        agent_config = settings.get_agent_config(agent_id)
        if not agent_config:
            raise AgentNotFoundError(agent_id)
        
        if not agent_config.enabled:
            raise AgentEngineError(f"Agent {agent_id} is disabled")
        
        # Create and cache service
        service = AgentService(agent_config)
        self._services[agent_id] = service
        return service
    
    def list_agents(self) -> list[Dict[str, Any]]:
        """List all configured agents."""
        return [
            {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "display_name": agent.display_name,
                "description": agent.description,
                "enabled": agent.enabled
            }
            for agent in settings.agents
        ]


# Global factory instance
agent_service_factory = AgentServiceFactory()