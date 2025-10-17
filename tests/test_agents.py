"""Tests for agent endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_agents():
    """Test listing agents."""
    response = client.get("/api/v1/agents")
    assert response.status_code == 200
    agents = response.json()
    assert isinstance(agents, list)


def test_query_agent_invalid_id():
    """Test querying non-existent agent."""
    response = client.post(
        "/api/v1/agents/invalid-agent/query",
        json={
            "user_id": "test-user",
            "message": "Hello",
            "session_id": "test-session"
        }
    )
    assert response.status_code == 404