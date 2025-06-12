"""
Database configuration
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class DatabaseConfig(BaseSettings):
    """Database configuration"""
    
    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    database: str = Field(default="openrearch", env="DB_NAME")
    username: str = Field(default="postgres", env="DB_USER")
    password: str = Field(default="123456", env="DB_PASSWORD")
    
    # Connection pool configuration
    min_connections: int = Field(default=1, env="DB_MIN_CONNECTIONS")
    max_connections: int = Field(default=10, env="DB_MAX_CONNECTIONS")
    connection_timeout: int = Field(default=30, env="DB_CONNECTION_TIMEOUT")
    skip_in_dev: bool = Field(default=False, env="DB_SKIP_IN_DEV")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "allow"  # Allow extra fields
    }
    
    @property
    def database_url(self) -> str:
        """Build database URL"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

database_config = DatabaseConfig()