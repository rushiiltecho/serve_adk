"""Custom exceptions and error handlers."""
from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class ADKProxyError(Exception):
    """Base exception for ADK Proxy Server."""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AgentNotFoundError(ADKProxyError):
    """Agent not found."""
    
    def __init__(self, agent_id: str):
        super().__init__(
            message=f"Agent with ID '{agent_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"agent_id": agent_id}
        )


class SessionNotFoundError(ADKProxyError):
    """Session not found."""
    
    def __init__(self, session_id: str):
        super().__init__(
            message=f"Session '{session_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"session_id": session_id}
        )


class InvalidStateUpdateError(ADKProxyError):
    """Invalid state update."""
    
    def __init__(self, message: str):
        super().__init__(
            message=f"Invalid state update: {message}",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class EventAppendError(ADKProxyError):
    """Error appending event to session."""
    
    def __init__(self, message: str):
        super().__init__(
            message=f"Failed to append event: {message}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class MemoryOperationError(ADKProxyError):
    """Error in memory operation."""
    
    def __init__(self, operation: str, message: str):
        super().__init__(
            message=f"Memory {operation} failed: {message}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"operation": operation}
        )


class AuthenticationError(ADKProxyError):
    """Authentication error."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AgentEngineError(ADKProxyError):
    """Error from Agent Engine API."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        details = {}
        if original_error:
            details["original_error"] = str(original_error)
        
        super().__init__(
            message=f"Agent Engine error: {message}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details
        )


async def adk_proxy_error_handler(request: Request, exc: ADKProxyError) -> JSONResponse:
    """Handle ADK Proxy errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "type": exc.__class__.__name__,
                "details": exc.details
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "message": "Internal server error",
                "type": "InternalServerError",
                "details": {
                    "exception": str(exc),
                    "path": str(request.url)
                }
            }
        }
    )