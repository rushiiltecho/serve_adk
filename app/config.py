"""Application configuration."""
import json
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentConfig(BaseSettings):
    """Configuration for a single agent."""
    
    agent_id: str = Field(..., description="Vertex AI Agent Engine ID")
    project_id: Optional[str] = Field(default=None, description="GCP Project ID (defaults to global)")
    location: Optional[str] = Field(default=None, description="GCP Location (defaults to global)")
    name: str = Field(..., description="Internal agent name")
    display_name: str = Field(..., description="Display name for the agent")
    description: str = Field(default="", description="Agent description")
    enabled: bool = Field(default=True, description="Whether agent is enabled")
    
    model_config = SettingsConfigDict(
        extra="allow",
        validate_assignment=True
    )


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = Field(default="vertex-ai-agent-gateway")
    app_version: str = Field(default="1.0.0")
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")
    
    # Google Cloud
    google_cloud_project: str = Field(..., description="GCP Project ID")
    google_cloud_location: str = Field(default="us-central1", description="GCP Location")
    google_application_credentials: Optional[str] = Field(
        default=None,
        description="Path to service account JSON"
    )
    
    # Agents - loaded from JSON string in environment
    agents: List[AgentConfig] = Field(default_factory=list)
    
    # CORS
    cors_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8000"]
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )
    
    @field_validator("agents", mode="before")
    @classmethod
    def parse_agents(cls, v):
        """Parse agents from JSON string or list."""
        if isinstance(v, str):
            try:
                agents_data = json.loads(v)
                if not isinstance(agents_data, list):
                    raise ValueError("AGENTS must be a JSON array")
                return [AgentConfig(**agent) for agent in agents_data]
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in AGENTS: {e}")
        elif isinstance(v, list):
            return [AgentConfig(**agent) if isinstance(agent, dict) else agent for agent in v]
        return v
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from JSON string or list."""
        # Handle None or empty string
        if not v or v == "":
            return ["http://localhost:3000", "http://localhost:8000"]
        
        if isinstance(v, str):
            # Try to parse as JSON first
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, ValueError):
                # If not valid JSON, treat as comma-separated
                origins = [origin.strip() for origin in v.split(",") if origin.strip()]
                return origins if origins else ["http://localhost:3000", "http://localhost:8000"]
        
        if isinstance(v, list):
            return v
        
        # Default fallback
        return ["http://localhost:3000", "http://localhost:8000"]
    
    def get_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """Get agent configuration by ID."""
        for agent in self.agents:
            if agent.agent_id == agent_id:
                return agent
        return None


# Create settings instance
settings = Settings()