"""Pytest configuration and fixtures."""
import sys
from pathlib import Path
import os

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from unittest.mock import Mock, AsyncMock

# Set test environment variables BEFORE importing app modules
os.environ["GOOGLE_CLOUD_PROJECT"] = "test-project"
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
os.environ["AGENTS"] = '[{"agent_id":"test-123","name":"test_agent","display_name":"Test Agent","description":"Test","enabled":true}]'
os.environ["ENVIRONMENT"] = "test"
os.environ["CORS_ORIGINS"] = '["http://localhost:3000"]'  # Set valid CORS_ORIGINS


@pytest.fixture(scope="session")
def test_settings():
    """Test settings fixture."""
    from config import Settings, AgentConfig
    
    return Settings(
        app_name="test-agent-gateway",
        environment="test",
        google_cloud_project="test-project",
        google_cloud_location="us-central1",
        agents=[
            AgentConfig(
                agent_id="test-agent-1",
                name="test_agent_1",
                display_name="Test Agent 1",
                description="Test agent for unit tests",
                enabled=True
            )
        ],
        cors_origins=["http://localhost:3000"]
    )


@pytest.fixture
def mock_vertexai_client():
    """Mock Vertex AI client."""
    client = Mock()
    client.agent_engines = Mock()
    client.agent_engines.get = Mock()
    client.agent_engines.create = Mock()
    client.agent_engines.sessions = Mock()
    return client


@pytest.fixture
def mock_agent_engine():
    """Mock agent engine."""
    engine = Mock()
    engine.api_resource = Mock()
    engine.api_resource.name = "projects/test/locations/us-central1/reasoningEngines/test-123"
    engine.async_stream_query = AsyncMock()
    return engine


@pytest.fixture
def mock_session():
    """Mock session."""
    session = Mock()
    session.name = "projects/test/locations/us-central1/reasoningEngines/test-123/sessions/session-123"
    session.user_id = "test-user"
    session.state = {"key": "value"}
    session.events = []
    return session


@pytest.fixture
def sample_query_request():
    """Sample query request."""
    from models.requests import QueryRequest
    return QueryRequest(
        user_id="test-user",
        message="Hello, test!",
        session_id="test-session"
    )


@pytest.fixture
def sample_session_create_request():
    """Sample session create request."""
    from models.requests import SessionCreateRequest
    return SessionCreateRequest(
        user_id="test-user",
        initial_state={"language": "en"}
    )


@pytest.fixture(autouse=True)
def cleanup_env_vars():
    """Cleanup environment variables after each test."""
    yield
    # Restore default CORS_ORIGINS after test
    os.environ["CORS_ORIGINS"] = '["http://localhost:3000"]'