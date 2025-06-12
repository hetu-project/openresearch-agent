"""
Application configuration
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    """Application settings"""
    
    # Basic application configuration
    app_name: str = Field(default="AI-Agent", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # Log configuration
    log_level: str = Field(default="DEBUG", env="LOG_LEVEL")
    log_file: Optional[str] = Field(default="logs/app.log", env="LOG_FILE")
    log_max_size: int = Field(default=10485760, env="LOG_MAX_SIZE")  # 10MB
    log_backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    # Database configuration
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    
    # Cache configuration
    cache_type: str = Field(default="memory", env="CACHE_TYPE")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")
    
    # Session configuration
    max_conversation_length: int = Field(default=100, env="MAX_CONVERSATION_LENGTH")
    
    # MCP server configuration
    mcp_server_host: str = Field(default="localhost", env="MCP_SERVER_HOST")
    mcp_server_port: int = Field(default=8000, env="MCP_SERVER_PORT")
    mcp_server_timeout: int = Field(default=30, env="MCP_SERVER_TIMEOUT")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "allow"
    }


settings = Settings()