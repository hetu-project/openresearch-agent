"""
LLM Configuration - For Together.ai
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / ".env"

class LLMConfig(BaseSettings):
    """LLM Configuration - For Together.ai"""
    
    # Together.ai Configuration
    together_api_key: str = Field(..., alias="LLM_TOGETHER_API_KEY")
    together_model: str = Field(default="Qwen/Qwen2.5-VL-72B-Instruct", alias="LLM_TOGETHER_MODEL")
    together_base_url: str = Field(default="https://api.together.xyz/v1/chat/completions", alias="LLM_TOGETHER_BASE_URL")
    
    # General Configuration
    max_tokens: int = Field(default=2000, alias="LLM_MAX_TOKENS")
    temperature: float = Field(default=0.7, alias="LLM_TEMPERATURE")
    timeout: int = Field(default=30, alias="LLM_TIMEOUT")
    
    # Together.ai Specific Configuration
    context_length_exceeded_behavior: str = Field(default="error")
    
    model_config = {
        # "env_prefix": "LLM_",
        "env_file": env_path,
        "env_file_encoding": "utf-8",
        "extra": "allow"
    }
    
    def validate_config(self):
        """Validate Configuration"""
        if not self.together_api_key:
            raise ValueError("LLM_TOGETHER_API_KEY is required")
        if not self.together_model:
            raise ValueError("LLM_TOGETHER_MODEL is required")

llm_config = LLMConfig()