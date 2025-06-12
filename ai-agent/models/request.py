"""
API Request Model
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
import re

class ChatRequest(BaseModel):
    """Chat Request Model"""
    message: str = Field(
        ..., 
        description="User message", 
        min_length=1, 
        max_length=2000
    )
    conversation_id: Optional[str] = Field(
        None, 
        description="Conversation ID, empty for new conversation",
        max_length=100
    )
    user_id: str = Field(
        ...,
        description="User ID",
        max_length=100
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, 
        description="Additional metadata"
    )
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        """Validate message content"""
        if not v.strip():
            raise ValueError('Message cannot be empty or whitespace only')
        return v.strip()
    
    @field_validator('conversation_id')
    @classmethod
    def validate_conversation_id(cls, v):
        if v is not None and not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Conversation ID can only contain letters, numbers, underscores and hyphens')
        return v
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        if not v.strip():
            raise ValueError('User ID cannot be empty')
        return v.strip()
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Please help me search for the latest papers on Transformer architecture",
                "conversation_id": "conv_123456",
                "user_id": "user_789",
                "metadata": {
                    "source": "web_ui",
                    "timestamp": "2024-01-15T10:30:00Z"
                }
            }
        }
    }
