"""Health check and configuration endpoints."""
import logging
from fastapi import APIRouter, Depends
from datetime import datetime
from models.responses import HealthResponse
from config import settings
from services.auth_service import auth_service
from services.agent_service import agent_service_factory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse)
@router.get("/", response_model=HealthResponse, include_in_schema=False)
async def health_check():
    """
    Health check endpoint.
    
    Returns service status and configured agents.
    """
    # Check Agent Engine connectivity
    agent_engine_status = "disconnected"
    try:
        if auth_service.verify_project_access():
            agent_engine_status = "connected"
    except Exception as e:
        logger.warning(f"Agent Engine health check failed: {e}")
    
    # Get configured agents
    agents = agent_service_factory.list_agents()
    
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        agent_engine_status=agent_engine_status,
        timestamp=datetime.utcnow(),
        agents=agents
    )