"""
Context-related models - MVP version
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

class ConversationContext(BaseModel):
    """Conversation Context Model"""
    conversation_id: str = Field(..., description="Conversation ID")
    recent_queries: List[str] = Field(default_factory=list, description="Recent Queries")
    search_history: List[Dict[str, Any]] = Field(default_factory=list, description="Search History")
    mentioned_entities: Dict[str, List[str]] = Field(default_factory=dict, description="Mentioned Entities")
    research_focus: Optional[str] = Field(None, description="Current Research Focus")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "conversation_id": "conv_123",
                "recent_queries": [
                    "transformer architecture",
                    "attention mechanism papers"
                ],
                "search_history": [
                    {
                        "query": "transformer",
                        "timestamp": "2024-01-15T10:00:00Z",
                        "results_count": 25
                    }
                ],
                "mentioned_entities": {
                    "authors": ["Vaswani", "Attention"],
                    "papers": ["Attention Is All You Need"],
                    "concepts": ["transformer", "attention"]
                },
                "research_focus": "transformer_architecture"
            }
        }
    }

class QueryContext(BaseModel):
    """Query Context Model"""
    query: str = Field(..., description="User Query")
    conversation_context: Optional[ConversationContext] = Field(None, description="Conversation Context")
    previous_results: List[Dict[str, Any]] = Field(default_factory=list, description="Previous Results")
    
    model_config = {
        "arbitrary_types_allowed": True,
        "json_schema_extra": {
            "example": {
                "query": "Find some recent papers about transformers",
                "conversation_context": None,
                "previous_results": []
            }
        }
    }