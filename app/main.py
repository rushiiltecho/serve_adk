"""Main FastAPI application."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import health, agents, sessions, events

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Vertex AI Agent Engine Gateway")
    logger.info(f"Version: {settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Project: {settings.google_cloud_project}")
    logger.info(f"Location: {settings.google_cloud_location}")
    logger.info(f"Configured agents: {len(settings.agents)}")
    
    yield
    
    logger.info("Shutting down Vertex AI Agent Engine Gateway")


# Create FastAPI app
app = FastAPI(
    title="Vertex AI Agent Engine Gateway",
    description="Production-ready gateway for deployed Vertex AI Agent Engine agents",
    version=settings.app_version,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1")
app.include_router(events.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Vertex AI Agent Engine Gateway",
        "version": settings.app_version,
        "status": "online"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development"
    )