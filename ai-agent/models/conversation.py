"""
Conversation Management Related Models
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class MessageRole(Enum):
    """Message Role Enumeration"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class Message(BaseModel):
    """Message Entity Model"""
    id: str = Field(..., description="Message ID")
    conversation_id: str = Field(..., description="Conversation ID")
    role: MessageRole = Field(..., description="Message Role")
    content: str = Field(..., description="Message Content")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation Time")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Message Metadata")
    
    model_config = {
        "use_enum_values": True,
        "json_schema_extra": {
            "example": {
                "id": "msg_123456",
                "conversation_id": "conv_789",
                "role": "user",
                "content": "Please help me search for the latest papers on Transformer architecture",
                "created_at": "2024-01-15T10:30:00Z",
                "metadata": {}
            }
        }
    }


class Conversation(BaseModel):
    """Conversation Entity Model"""
    id: str = Field(..., description="Conversation ID")
    user_id: str = Field(..., description="User ID")
    title: Optional[str] = Field(None, description="Conversation Title")
    context: Optional[str] = Field(None, description="Conversation Context")
    is_active: bool = Field(default=True, description="Whether the conversation is active")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation Time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Update Time")
    message_count: int = Field(default=0, description="Total Message Count")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Conversation Metadata")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "conv_123456",
                "user_id": "user_789",
                "title": "Transformer Architecture Research",
                "context": "User is researching deep learning related content",
                "is_active": True,
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "message_count": 6,
                "metadata": {}
            }
        }
    }

class ConversationWithMessages(BaseModel):
    """Complete Conversation Model with Messages"""
    conversation: Conversation = Field(..., description="Conversation Information")
    messages: List[Message] = Field(..., description="Message List")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "conversation": {
                    "id": "conv_123456",
                    "user_id": "user_789",
                    "title": "Transformer Architecture Research",
                    "context": "User is researching deep learning related content",
                    "is_active": True,
                    "created_at": "2024-01-15T10:00:00Z",
                    "updated_at": "2024-01-15T10:30:00Z",
                    "message_count": 2,
                    "metadata": {}
                },
                "messages": []
            }
        }
    }

# Simplified DTOs
class CreateConversationDTO(BaseModel):
    """Create Conversation DTO"""
    title: Optional[str] = Field(None, description="Conversation Title", max_length=200)
    context: Optional[str] = Field(None, description="Conversation Context", max_length=1000)
    initial_message: Optional[str] = Field(None, description="Initial Message", max_length=2000)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Deep Learning Paper Research",
                "context": "User wants to learn about the latest developments in deep learning research",
                "initial_message": "I want to learn about the latest deep learning papers"
            }
        }
    }

class CreateMessageDTO(BaseModel):
    """Create Message DTO"""
    conversation_id: str = Field(..., description="Conversation ID")
    role: MessageRole = Field(..., description="Message Role")
    content: str = Field(..., description="Message Content", min_length=1, max_length=50000)
    
    model_config = {
        "use_enum_values": True,
        "json_schema_extra": {
            "example": {
                "conversation_id": "conv_123456",
                "role": "user",
                "content": "Please search for papers about the BERT model"
            }
        }
    }