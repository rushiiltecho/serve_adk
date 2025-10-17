"""Basic sanity tests."""
import pytest
import os


def test_python_path():
    """Test that Python path is set correctly."""
    import sys
    assert any(p.endswith('ciena_adk_server') or p == '.' for p in sys.path)


def test_environment_loaded():
    """Test that environment is loaded."""
    assert os.getenv('GOOGLE_CLOUD_PROJECT') is not None
    assert os.getenv('GOOGLE_CLOUD_LOCATION') is not None
    assert os.getenv('AGENTS') is not None


def test_agents_config():
    """Test that AGENTS config is valid."""
    import json
    agents_str = os.getenv('AGENTS')
    assert agents_str is not None
    agents = json.loads(agents_str)
    assert isinstance(agents, list)
    assert len(agents) > 0
    
    # Verify agent structure (no project_id or location)
    agent = agents[0]
    assert 'agent_id' in agent
    assert 'name' in agent
    assert 'display_name' in agent
    # Should NOT have project_id or location
    assert 'project_id' not in agent
    assert 'location' not in agent


def test_settings_creation():
    """Test that Settings can be created."""
    from app.config import Settings, AgentConfig
    
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
        ]
    )
    
    assert settings.google_cloud_project == "test-project"
    assert settings.google_cloud_location == "us-central1"
    assert len(settings.agents) == 1
    assert settings.agents[0].agent_id == "test-123"


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
    assert not hasattr(agent, 'project_id')
    assert not hasattr(agent, 'location')