"""Unit tests for configuration."""
import pytest
import os
from app.config import Settings, AgentConfig


def test_agent_config_validation():
    """Test agent configuration validation."""
    config = AgentConfig(
        agent_id="test-123",
        name="test_agent",
        display_name="Test Agent",
        description="A test agent",
        enabled=True
    )
    
    assert config.agent_id == "test-123"
    assert config.name == "test_agent"
    assert config.enabled is True


def test_settings_from_env():
    """Test settings loading from environment."""
    # Save original values
    orig_cors = os.environ.get('CORS_ORIGINS')
    
    # Set test values
    os.environ["GOOGLE_CLOUD_PROJECT"] = "test-project"
    os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
    os.environ["AGENTS"] = '[{"agent_id":"test","name":"test","display_name":"Test","description":"Test","enabled":true}]'
    os.environ["CORS_ORIGINS"] = '["http://localhost:3000"]'
    
    try:
        settings = Settings()
        
        assert settings.google_cloud_project == "test-project"
        assert settings.google_cloud_location == "us-central1"
        assert len(settings.agents) == 1
        assert len(settings.cors_origins) > 0
    finally:
        # Restore original
        if orig_cors is not None:
            os.environ['CORS_ORIGINS'] = orig_cors
        elif 'CORS_ORIGINS' in os.environ:
            del os.environ['CORS_ORIGINS']


def test_get_agent_config():
    """Test getting agent config by ID."""
    settings = Settings(
        google_cloud_project="test-project",
        agents=[
            AgentConfig(
                agent_id="agent-1",
                name="agent_1",
                display_name="Agent 1",
                enabled=True
            ),
            AgentConfig(
                agent_id="agent-2",
                name="agent_2",
                display_name="Agent 2",
                enabled=True
            )
        ]
    )
    
    agent = settings.get_agent_config("agent-1")
    assert agent is not None
    assert agent.agent_id == "agent-1"
    
    agent = settings.get_agent_config("non-existent")
    assert agent is None


def test_cors_origins_default():
    """Test CORS origins default value."""
    # Ensure no CORS_ORIGINS in environment
    if 'CORS_ORIGINS' in os.environ:
        del os.environ['CORS_ORIGINS']
    
    settings = Settings(
        google_cloud_project="test-project",
        agents=[
            AgentConfig(
                agent_id="test",
                name="test",
                display_name="Test",
                enabled=True
            )
        ]
    )
    
    assert len(settings.cors_origins) > 0
    assert "http://localhost:3000" in settings.cors_origins
    assert "http://localhost:3000" in settings.cors_origins