"""
Application configuration
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / ".env"

class Settings(BaseSettings):
    """Application settings"""
    
    # Basic application configuration
    app_name: str = Field(default="AI-Agent", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    
    # Server configuration
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    
    # Log configuration
    log_level: str = Field(default="DEBUG", alias="LOG_LEVEL")
    log_file: Optional[str] = Field(default="logs/app.log", alias="LOG_FILE")
    log_max_size: int = Field(default=10485760, alias="LOG_MAX_SIZE")  # 10MB
    log_backup_count: int = Field(default=5, alias="LOG_BACKUP_COUNT")
    
    # Cache configuration
    cache_type: str = Field(default="memory", alias="CACHE_TYPE")
    cache_ttl: int = Field(default=3600, alias="CACHE_TTL")
    
    # Session configuration
    max_conversation_length: int = Field(default=100, alias="MAX_CONVERSATION_LENGTH")
    
    # MCP server configuration
    mcp_server_host: str = Field(default="localhost", alias="MCP_SERVER_HOST")
    mcp_server_port: int = Field(default=8000, alias="MCP_SERVER_PORT")
    mcp_server_timeout: int = Field(default=30, alias="MCP_SERVER_TIMEOUT")
    
    model_config = {
        "env_file": env_path,
        "env_file_encoding": "utf-8",
        "extra": "allow"
    }


settings = Settings()