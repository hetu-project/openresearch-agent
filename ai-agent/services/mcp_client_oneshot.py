"""
MCP Client Service - One-shot call version (Fix response parsing)
"""
import asyncio
import json
import structlog
from typing import Dict, Any, List, Optional
from datetime import datetime
import subprocess
import os

from configs.mcp_config import mcp_config
from models.task import Task, TaskResult, TaskStatus

logger = structlog.get_logger()

class MCPClient:
    """MCP Client - One-shot mode"""
    
    def __init__(self):
        self.available_tools: List[Dict[str, Any]] = []
        self._tools_loaded = False
    
    async def initialize(self):
        """Initialize MCP client"""
        try:
            logger.info("Initializing MCP client (one-shot mode)")
            
            # Check paths
            if not os.path.exists(mcp_config.mcp_cwd):
                raise Exception(f"MCP server directory not found: {mcp_config.mcp_cwd}")
            
            if not os.path.exists(mcp_config.mcp_command):
                raise Exception(f"MCP command not found: {mcp_config.mcp_command}")
            
            if not os.path.exists(mcp_config.mcp_python):
                raise Exception(f"MCP Python interpreter not found: {mcp_config.mcp_python}")
            
            # Test connection and load tools
            await self._load_available_tools()
            
            logger.info("MCP client initialized successfully", tools_count=len(self.available_tools))
            
        except Exception as e:
            logger.error("Failed to initialize MCP client", error=str(e))
            raise
    
    def _parse_mcp_responses(self, stdout: str) -> List[Dict[str, Any]]:
        """Parse MCP server output, extract all JSON-RPC responses"""
        responses = []
        if not stdout:
            return responses
        
        # Parse output by line
        lines = stdout.split('\n')
        logger.debug("Parsing MCP output", total_lines=len(lines))
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                data = json.loads(line)
                # Check if it's a JSON-RPC response (contains jsonrpc field)
                if isinstance(data, dict) and data.get("jsonrpc") == "2.0":
                    if "error" in data:
                        error = data["error"]
                        logger.error("MCP error response", 
                                line_num=line_num,
                                error_code=error.get('code'),
                                error_message=error.get('message'))
                        raise Exception(f"MCP error: {error.get('message', 'Unknown error')}")
                    elif "result" in data or "id" in data:
                        logger.debug("Found JSON-RPC response", 
                                line_num=line_num,
                                response_id=data.get("id"),
                                has_result="result" in data,
                                method=data.get("method"))
                        responses.append(data)
                    else:
                        logger.debug("JSON-RPC message without result", 
                                line_num=line_num,
                                message_type=data.get("method", "unknown"))
            except json.JSONDecodeError as e:
                # This line is not JSON, might be a log, record but continue
                logger.debug("Non-JSON line", line_num=line_num, content=line[:100])
                continue
        
        return responses

    
    async def _execute_mcp_session(self, requests: List[str], target_request_id: int = None) -> Dict[str, Any]:
        """Execute complete MCP session (multiple requests)"""
        try:
            logger.debug("Executing MCP session", request_count=len(requests))
            
            # Use correct command
            command = mcp_config.actual_server_command
            logger.debug("Using command", command=command, cwd=mcp_config.mcp_cwd)
            
            # Start process, set environment variables
            env = os.environ.copy()
            env['PYTHONDONTWRITEBYTECODE'] = '1'
            env.pop('DEBUGPY_LAUNCHER_PORT', None)
            env.pop('PYDEVD_LOAD_VALUES_ASYNC', None)
            
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=mcp_config.mcp_cwd,
                env=env
            )
            
            # Prepare input - send all requests at once
            input_data = '\n'.join(requests) + '\n'
            logger.debug("Sending requests", input_preview=input_data[:200])
            
            # Use communicate
            try:
                stdout, stderr = process.communicate(
                    input=input_data, 
                    timeout=mcp_config.timeout
                )
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                raise Exception("MCP server request timeout")
            
            logger.debug("Process completed", 
                        return_code=process.returncode,
                        stdout_lines=len(stdout.split('\n')) if stdout else 0,
                        stderr_preview=stderr[:200] if stderr else None)
            
            # Parse all responses
            responses = self._parse_mcp_responses(stdout)
            logger.debug("Found responses", response_count=len(responses))
            
            # Print all responses for debugging
            for i, response in enumerate(responses):
                logger.debug(f"Response {i}", response_id=response.get("id"), has_result="result" in response)
            
            # If target request ID is specified, return corresponding response
            if target_request_id is not None:
                for response in responses:
                    if response.get("id") == target_request_id:
                        result = response.get("result", {})
                        logger.debug("Found target response", target_id=target_request_id, result_keys=list(result.keys()) if isinstance(result, dict) else None)
                        return result
                
                # If target response not found, log error
                logger.warning("Target response not found", 
                            target_id=target_request_id,
                            available_ids=[r.get("id") for r in responses])
            
            # Otherwise return the last response with result
            for response in reversed(responses):
                if "result" in response:
                    result = response.get("result", {})
                    logger.debug("Using last response with result", response_id=response.get("id"))
                    return result
            
            # If no valid response found, return empty result
            logger.warning("No valid responses found", 
                        response_count=len(responses),
                        process_return_code=process.returncode)
            
            # If there's error output, log it
            if stderr:
                logger.error("MCP server stderr", stderr=stderr)
            
            return {}
            
        except Exception as e:
            logger.error("MCP session failed", error=str(e))
            raise

    
    async def _load_available_tools(self):
        """Load available tools list"""
        try:
            logger.info("Loading available tools...")
            
            # Build complete MCP session requests
            requests = [
                # 1. Initialize
                json.dumps({
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "clientInfo": {"name": "ai-agent", "version": "1.0.0"}
                    }
                }),
                # 2. Initialized notification (no id for notifications)
                json.dumps({
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized"
                }),
                # 3. List tools
                json.dumps({
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {}
                })
            ]
            
            logger.debug("Sending MCP initialization sequence")
            result = await self._execute_mcp_session(requests, target_request_id=2)
            logger.debug("Tools list result", result=result)
            
            self.available_tools = result.get("tools", [])
            self._tools_loaded = True
            
            logger.info("Available tools loaded", 
                       tools=[tool.get("name") for tool in self.available_tools])
                    
        except Exception as e:
            logger.error("Error loading available tools", error=str(e))
            # Set default tools list (based on server log output)
            self.available_tools = [
                {"name": "search_authors", "description": "Search for authors"},
                {"name": "get_author_details", "description": "Get author details"},
                {"name": "get_author_papers", "description": "Get author papers"},
                {"name": "search_papers", "description": "Search for papers"},
                {"name": "get_paper_details", "description": "Get paper details"},
                {"name": "get_paper_citations", "description": "Get paper citations"},
                {"name": "get_citation_network", "description": "Get citation network"},
                {"name": "get_collaboration_network", "description": "Get collaboration network"},
                {"name": "get_trending_papers", "description": "Get trending papers"},
                {"name": "get_top_keywords", "description": "Get top keywords"}
            ]
            self._tools_loaded = True
            logger.info("Using default tools list", tools=[t["name"] for t in self.available_tools])
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP tool"""
        try:
            # Build complete MCP session requests
            requests = [
                # 1. Initialize
                json.dumps({
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "clientInfo": {"name": "ai-agent", "version": "1.0.0"}
                    }
                }),
                # 2. Initialized notification
                json.dumps({
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized"
                }),
                # 3. Call tool
                json.dumps({
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                })
            ]
            
            logger.info("Calling MCP tool (one-shot)", tool_name=tool_name, arguments=arguments)
            
            result = await self._execute_mcp_session(requests, target_request_id=3)
            
            logger.info("MCP tool call successful", tool_name=tool_name)
            
            return result
                    
        except Exception as e:
            logger.error("Error calling MCP tool", tool_name=tool_name, error=str(e))
            raise
    
    async def call_tool_with_retry(self, tool_name: str, 
                                  arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Tool call with retry"""
        last_error = None
        
        for attempt in range(mcp_config.max_retries):
            try:
                return await self.call_tool(tool_name, arguments)
                
            except Exception as e:
                last_error = e
                if attempt < mcp_config.max_retries - 1:
                    wait_time = mcp_config.retry_delay * (2 ** attempt)
                    logger.warning(
                        "MCP tool call failed, retrying",
                        tool_name=tool_name,
                        attempt=attempt + 1,
                        wait_time=wait_time,
                        error=str(e)
                    )
                    await asyncio.sleep(wait_time)
        
        raise last_error
    
    # Convenience methods
    async def search_papers(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search papers"""
        return await self.call_tool_with_retry(
            "search_papers",
            {"query": query, "limit": limit}
        )
    
    async def get_paper_details(self, paper_id: str) -> Dict[str, Any]:
        """Get paper details"""
        return await self.call_tool_with_retry(
            "get_paper_details",
            {"paper_id": paper_id}
        )
    
    async def search_authors(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search authors"""
        return await self.call_tool_with_retry(
            "search_authors",
            {"query": query, "limit": limit}
        )
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get available tools list"""
        return self.available_tools.copy()
    
    def is_tool_available(self, tool_name: str) -> bool:
        """Check if tool is available"""
        return any(tool.get("name") == tool_name for tool in self.available_tools)
    
    async def cleanup(self):
        """Clean up resources"""
        logger.info("MCP client cleanup completed (one-shot mode)")

mcp_client_oneshot = MCPClient()
