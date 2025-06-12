"""
API Response Models
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChatResponse(BaseModel):
    """Chat Response Model"""
    message: str = Field(..., description="AI reply message")
    conversation_id: str = Field(..., description="Conversation ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")
    processing_time: float = Field(0, description="Processing time (seconds)")
    intent_type: Optional[str] = Field(None, description="Recognized intent type")
    confidence: Optional[float] = Field(None, description="Intent recognition confidence")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "I found the following latest papers about Transformer architecture:\n\n1. **Attention Is All You Need** - Vaswani et al. (2017)\n   - Citations: 50,000+\n   - Abstract: Proposed the Transformer model based entirely on attention mechanism...",
                "conversation_id": "conv_123456",
                "metadata": {
                    "sources_count": 5,
                    "search_terms": ["transformer", "attention mechanism"],
                    "tools_used": ["search_papers"]
                },
                "processing_time": 2.5,
                "intent_type": "search_papers",
                "confidence": 0.95
            }
        }
    }

class MessageResponse(BaseModel):
    """Message Response Model"""
    id: str = Field(..., description="Message ID")
    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Message content")
    timestamp: str = Field(..., description="Message timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Message metadata")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "msg_123",
                "role": "user",
                "content": "Please help me search for papers about deep learning",
                "timestamp": "2024-01-15T10:30:00Z",
                "metadata": {
                    "intent_type": "search_papers",
                    "confidence": 0.9
                }
            }
        }
    }

class ConversationResponse(BaseModel):
    """Conversation Response Model"""
    conversation_id: str = Field(..., description="Conversation ID")
    title: Optional[str] = Field(None, description="Conversation title")
    created_at: str = Field(..., description="Creation time")
    updated_at: str = Field(..., description="Update time")
    message_count: int = Field(..., description="Total message count")
    messages: List[MessageResponse] = Field(..., description="Message list")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "conversation_id": "conv_123",
                "title": "Deep Learning Paper Search",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "message_count": 4,
                "messages": []
            }
        }
    }

class ConversationSummary(BaseModel):
    """Conversation Summary Model"""
    conversation_id: str = Field(..., description="Conversation ID")
    title: Optional[str] = Field(None, description="Conversation title")
    created_at: str = Field(..., description="Creation time")
    updated_at: str = Field(..., description="Update time")
    message_count: int = Field(..., description="Total message count")
    last_message: Optional[str] = Field(None, description="Last message")
    last_message_role: Optional[str] = Field(None, description="Role of last message")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "conversation_id": "conv_123",
                "title": "Deep Learning Paper Search",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "message_count": 4,
                "last_message": "Thank you for your help!",
                "last_message_role": "user"
            }
        }
    }

class ConversationListResponse(BaseModel):
    """Conversation List Response Model"""
    conversations: List[ConversationSummary] = Field(..., description="Conversation list")
    total: int = Field(..., description="Total conversations")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=20, description="Page size")
    has_more: bool = Field(default=False, description="Whether there is more data")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "conversations": [],
                "total": 25,
                "page": 1,
                "page_size": 20,
                "has_more": True
            }
        }
    }

class ErrorResponse(BaseModel):
    """Error Response Model"""
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    error_type: str = Field(default="general_error", description="Error type")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Error time")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "Intent analysis failed",
                "error_code": "INTENT_001",
                "error_type": "intent_error",
                "details": {
                    "query": "User query content",
                    "confidence": 0.3
                },
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    }

class HealthResponse(BaseModel):
    """Health Check Response Model"""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: Optional[str] = Field(None, description="Service version")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Check time")
    details: Optional[Dict[str, Any]] = Field(None, description="Detailed information")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "service": "openresearch-agent",
                "version": "1.0.0",
                "timestamp": "2024-01-15T10:30:00Z",
                "details": {
                    "mcp_server": "connected",
                    "llm_service": "ready"
                }
            }
        }
    }