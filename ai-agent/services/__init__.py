"""
Service Layer Package - MVP Version
"""
from .llm_service import llm_service, LLMService
from .conversation_service import conversation_service, ConversationService

# MCP Client - Two Protocol Versions
from .mcp_client_http import mcp_client as mcp_client_http, MCPClient as MCPClientHTTP
from .mcp_client_stdio import mcp_client_stdio, MCPClient as MCPClientStdio
from .mcp_client_oneshot import mcp_client_oneshot,MCPClient as MCPClientOneshot

# Default using stdio protocol (recommended)
mcp_client = mcp_client_stdio
MCPClient = MCPClientStdio

__all__ = [
    # LLM Service
    "llm_service",
    "LLMService",
    
    # MCP Client - Default stdio version
    "mcp_client_http", 
    "MCPClient",
    
    # MCP Client - HTTP version (backup)
    "mcp_client_http",
    "MCPClientHTTP",
    
    # MCP Client - stdio version
    "mcp_client_stdio",
    "MCPClientStdio",
    
    # Conversation Service
    "conversation_service",
    "ConversationService"
]