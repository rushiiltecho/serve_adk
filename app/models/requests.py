"""Request models using google.genai.types where possible."""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request to query a deployed agent."""
    user_id: str = Field(..., description="User ID for session management")
    session_id: Optional[str] = Field(None, description="Session ID to continue conversation")
    message: str = Field(..., description="User message to send to agent")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "session_id": "session_456",
                "message": "What's the weather in San Francisco?",
                "metadata": {"source": "web_ui"}
            }
        }


class SessionCreateRequest(BaseModel):
    """Request to create a new session."""
    user_id: str = Field(..., description="User ID for the session")
    session_id: Optional[str] = Field(None, description="Optional specific session ID")
    initial_state: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Initial state for the session"
    )
    session_config: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional session configuration"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "initial_state": {
                    "user_preferences": {"language": "en", "timezone": "UTC"}
                },
                "session_config": {
                    "max_events": 1000,
                    "timeout_seconds": 3600
                }
            }
        }


class SessionUpdateRequest(BaseModel):
    """Request to update session configuration."""
    user_id: str = Field(..., description="User ID for verification")
    config_updates: Dict[str, Any] = Field(
        ...,
        description="Configuration updates to apply"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "config_updates": {
                    "max_events": 2000,
                    "timeout_seconds": 7200
                }
            }
        }


class SessionStateUpdateRequest(BaseModel):
    """
    Request to update session state.
    This will be converted to EventActions with state_delta.
    """
    user_id: str = Field(..., description="User ID for verification")
    state_delta: Dict[str, Any] = Field(
        ...,
        description="State changes to apply (merged with existing state)"
    )
    replace: bool = Field(
        default=False,
        description="If True, replace entire state instead of merging"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "state_delta": {
                    "counter": 5,
                    "last_action": "increment"
                },
                "replace": False
            }
        }


class EventAppendRequest(BaseModel):
    """
    Request to append an event to a session.
    Uses google.genai.types.Content and google.adk.events.EventActions internally.
    """
    user_id: str = Field(..., description="User ID for verification")
    author: str = Field(..., description="Event author: 'user', 'agent', 'system', 'tool'")
    invocation_id: str = Field(..., description="Invocation ID for grouping events")
    timestamp: Optional[float] = Field(None, description="Event timestamp (epoch seconds)")
    
    # Content (optional) - will be converted to genai_types.Content
    content_text: Optional[str] = Field(None, description="Text content")
    content_role: str = Field(default="user", description="Content role")
    
    # Actions (optional) - for state updates
    state_delta: Optional[Dict[str, Any]] = Field(
        None,
        description="State changes to apply via EventActions"
    )
    artifact_delta: Optional[Dict[str, int]] = Field(
        None,
        description="Artifact version updates"
    )
    transfer_to_agent: Optional[str] = Field(None, description="Transfer to another agent")
    escalate: Optional[bool] = Field(None, description="Escalate to human")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "author": "system",
                "invocation_id": "inv_789",
                "content_text": "Session state updated",
                "state_delta": {
                    "step": "completed",
                    "result": "success"
                }
            }
        }


class MemoryGenerateRequest(BaseModel):
    """Request to generate memories from session or content."""
    user_id: str = Field(..., description="User ID for memory scope")
    session_id: Optional[str] = Field(
        None,
        description="Generate memories from this session"
    )
    scope: Optional[Dict[str, str]] = Field(
        None,
        description="Custom scope for memories"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "session_id": "session_456",
                "scope": {"context": "customer_support"}
            }
        }


class MemorySearchRequest(BaseModel):
    """Request to search memories."""
    query: str = Field(..., description="Search query")
    user_id: str = Field(..., description="User ID to search memories for")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to return")
    scope: Optional[Dict[str, str]] = Field(None, description="Filter by scope")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "user's favorite color",
                "user_id": "user_123",
                "top_k": 5
            }
        }