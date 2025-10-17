"""Response models."""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class QueryResponse(BaseModel):
    """Response from agent query."""
    session_id: str = Field(..., description="Session ID used for the query")
    response: str = Field(..., description="Agent's text response")
    events: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of events generated"
    )
    usage_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Token usage and other metadata"
    )
    trace_id: Optional[str] = Field(None, description="Trace ID for debugging")


class SessionResponse(BaseModel):
    """Response with session information."""
    session_id: str
    user_id: str
    app_name: str
    state: Dict[str, Any]
    event_count: int
    created_at: datetime
    updated_at: datetime


class EventResponse(BaseModel):
    """Response after appending an event."""
    event_id: str = Field(..., description="ID of the appended event")
    session_state: Dict[str, Any] = Field(..., description="Updated session state")
    success: bool = Field(default=True, description="Whether operation succeeded")


class MemoryResponse(BaseModel):
    """Response with memory information."""
    memory_id: str
    content: str
    scope: Dict[str, str]
    created_at: datetime


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    agent_engine_status: str = Field(..., description="Agent Engine connectivity status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agents: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Configured agents"
    )


class ErrorResponse(BaseModel):
    """Error response."""
    error: Dict[str, Any] = Field(..., description="Error details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": {
                    "message": "Session not found",
                    "type": "SessionNotFoundError",
                    "details": {"session_id": "invalid_id"}
                }
            }
        }