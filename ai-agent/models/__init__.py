"""
Business model package
"""
from .intent import (
    IntentType,
    Intent,
    IntentAnalysisResult
)
from .task import (
    TaskType,
    TaskStatus,
    Task,
    TaskPlan,
    TaskResult
)
from .request import (
    ChatRequest,
    # ConversationUpdateRequest,
    # ConversationCreateRequest
)

from .conversation import (
    MessageRole,
    Message,
    Conversation,
    ConversationWithMessages,
    CreateMessageDTO
)

from .context import (
    ConversationContext,
    QueryContext
)

from .response import (
    ChatResponse,
    MessageResponse,
    ConversationResponse,
    ConversationSummary,
    ConversationListResponse,
    ErrorResponse,
    HealthResponse
)

__all__ = [
    # Intent models
    "IntentType",
    "Intent", 
    "IntentAnalysisResult",
    
    # Task models
    "TaskType",
    "TaskStatus",
    "Task",
    "TaskPlan",
    "TaskResult",
    
    # Request models
    "ChatRequest",
    "ConversationUpdateRequest",
    "ConversationCreateRequest",
    
    # Conversation models
    "MessageRole",
    "Message",
    "Conversation",
    "ConversationWithMessages",
    "CreateConversationDTO",
    "CreateMessageDTO",

    # Context models
    "ConversationContext",
    "QueryContext",

    # Response models
    "ChatResponse",
    "MessageResponse",
    "ConversationResponse",
    "ConversationSummary",
    "ConversationListResponse",
    "ErrorResponse",
    "HealthResponse"
]