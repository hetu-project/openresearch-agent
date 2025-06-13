"""
Database configuration
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / ".env"

class DatabaseConfig(BaseSettings):
    """Database configuration"""
    
    host: str = Field(default="localhost", alias="DB_HOST")
    port: int = Field(default=5432, alias="DB_PORT")
    database: str = Field(default="openrearch", alias="DB_NAME")
    username: str = Field(default="postgres", alias="DB_USER")
    password: str = Field(default="123456", alias="DB_PASSWORD")
    
    # Connection pool configuration
    min_connections: int = Field(default=1, alias="DB_MIN_CONNECTIONS")
    max_connections: int = Field(default=10, alias="DB_MAX_CONNECTIONS")
    connection_timeout: int = Field(default=30, alias="DB_CONNECTION_TIMEOUT")
    skip_in_dev: bool = Field(default=False, alias="DB_SKIP_IN_DEV")

    model_config = {
        # "env_prefix": "DB_",
        "env_file": env_path,
        "env_file_encoding": "utf-8",
        "extra": "allow"  # Allow extra fields
    }
    
    @property
    def database_url(self) -> str:
        """Build database URL"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

database_config = DatabaseConfig()