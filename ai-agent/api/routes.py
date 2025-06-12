"""
API route unified management - Support multiple versions
"""
from fastapi import APIRouter

from .v1 import chat as chat_v1
from .v1 import conversation as conversation_v1
from .v2 import chat as chat_v2
from .v2 import conversation as conversation_v2
from .health import router as health_router

api_v1_router = APIRouter()
api_v2_router = APIRouter()

api_v1_router.include_router(
    health_router,
    prefix="/health",
    tags=["health-v1"],
    responses={
        200: {"description": "Success"},
        503: {"description": "Service Unavailable"}
    }
)

api_v1_router.include_router(
    chat_v1.router,
    # prefix="/chat",
    tags=["chat-v1"],
    responses={
        200: {"description": "Success"},
        400: {"description": "Bad Request"},
        500: {"description": "Internal Server Error"}
    }
)

api_v1_router.include_router(
    conversation_v1.router,
    # prefix="/conversations",
    tags=["conversation-v1"], 
    responses={
        200: {"description": "Success"},
        404: {"description": "Not Found"},
        400: {"description": "Bad Request"},
        500: {"description": "Internal Server Error"}
    }
)

api_v2_router.include_router(
    health_router,
    prefix="/health",
    tags=["health-v2"],
    responses={
        200: {"description": "Success"},
        503: {"description": "Service Unavailable"}
    }
)

api_v2_router.include_router(
    chat_v2.router,
    # prefix="/chat",
    tags=["chat-v2"],
    responses={
        200: {"description": "Success"},
        400: {"description": "Bad Request"},
        500: {"description": "Internal Server Error"}
    }
)

api_v2_router.include_router(
    conversation_v2.router,
    # prefix="/conversations",
    tags=["conversation-v2"], 
    responses={
        200: {"description": "Success"},
        404: {"description": "Not Found"},
        400: {"description": "Bad Request"},
        500: {"description": "Internal Server Error"}
    }
)

__all__ = ["api_v1_router", "api_v2_router"]