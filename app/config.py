"""Configuration settings for the Natural Language → TOPdesk MCP Router."""

import os
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # MCP Server connection
    mcp_base_url: str = Field(..., env="MCP_BASE_URL", description="Base URL for the MCP server")
    mcp_api_key: Optional[str] = Field(None, env="MCP_API_KEY", description="API key for MCP server if required")
    
    # Optional LLM provider (for future enhancement)
    llm_provider: Optional[str] = Field(None, env="LLM_PROVIDER", description="LLM provider for query enhancement")
    
    # Logging configuration
    log_level: str = Field("INFO", env="LOG_LEVEL", description="Logging level")
    
    # Rate limiting configuration
    rate_limit_requests: int = Field(60, description="Maximum requests per time window")
    rate_limit_window: int = Field(300, description="Rate limit time window in seconds (5 minutes)")
    
    # Circuit breaker configuration
    circuit_breaker_failure_threshold: int = Field(5, description="Number of failures to open circuit")
    circuit_breaker_recovery_timeout: int = Field(60, description="Seconds to wait before trying half-open")
    
    # Request timeouts and retries
    mcp_timeout: int = Field(8, description="Timeout for MCP requests in seconds")
    mcp_retries: int = Field(2, description="Number of retries for MCP requests")
    
    # Default query limits
    default_max_results: int = Field(5, description="Default maximum results per query")
    max_allowed_results: int = Field(25, description="Maximum allowed results per query")
    
    # Default time filters (days)
    default_time_window: int = Field(30, description="Default time window in days for queries")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from existing .env


# Global settings instance
try:
    settings = Settings()
except Exception as e:
    # If settings fail to load (e.g., missing MCP_BASE_URL), create with defaults
    import os
    settings = Settings(
        mcp_base_url=os.getenv("MCP_BASE_URL", "http://localhost:3030")
    )