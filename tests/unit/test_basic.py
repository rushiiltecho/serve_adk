"""Basic sanity tests."""
import pytest
import os


def test_python_path():
    """Test that Python path is set correctly."""
    import sys
    assert any(p.endswith('ciena_adk_server') or p == '.' for p in sys.path)


def test_app_import():
    """Test that app module can be imported."""
    try:
        from app.config import Settings
        assert Settings is not None
    except ImportError as e:
        pytest.fail(f"Failed to import app module: {e}")


def test_environment_loaded():
    """Test that environment is loaded."""
    assert os.getenv('GOOGLE_CLOUD_PROJECT') is not None


def test_agents_config():
    """Test that AGENTS config is valid."""
    import json
    agents_str = os.getenv('AGENTS')
    assert agents_str is not None
    agents = json.loads(agents_str)
    assert isinstance(agents, list)
    assert len(agents) > 0


def test_settings_creation():
    """Test that Settings can be created."""
    from app.config import Settings, AgentConfig
    
    # Temporarily unset CORS_ORIGINS to avoid interference
    cors_backup = os.environ.get('CORS_ORIGINS')
    if 'CORS_ORIGINS' in os.environ:
        del os.environ['CORS_ORIGINS']
    
    try:
        # Create settings with test values
        settings = Settings(
            google_cloud_project="test-project",
            google_cloud_location="us-central1",
            agents=[
                AgentConfig(
                    agent_id="test-123",
                    name="test_agent",
                    display_name="Test Agent",
                    description="Test",
                    enabled=True
                )
            ],
            cors_origins=["http://localhost:3000"]  # Explicitly set
        )
        
        assert settings.google_cloud_project == "test-project"
        assert settings.google_cloud_location == "us-central1"
        assert len(settings.agents) == 1
        assert settings.agents[0].agent_id == "test-123"
        assert len(settings.cors_origins) > 0
    finally:
        # Restore CORS_ORIGINS
        if cors_backup is not None:
            os.environ['CORS_ORIGINS'] = cors_backup


def test_agent_config_no_extra_fields():
    """Test that AgentConfig doesn't require project_id or location."""
    from app.config import AgentConfig
    
    # This should work without project_id or location
    agent = AgentConfig(
        agent_id="test-123",
        name="test_agent",
        display_name="Test Agent",
        description="A test agent",
        enabled=True
    )
    
    assert agent.agent_id == "test-123"
    assert agent.name == "test_agent"
