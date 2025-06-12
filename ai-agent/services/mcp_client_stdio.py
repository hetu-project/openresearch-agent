"""
MCP Client Service - stdio protocol version - simplified version
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
    """MCP Client - stdio protocol"""
    
    def __init__(self):
        self.process: Optional[asyncio.subprocess.Process] = None
        self.available_tools: List[Dict[str, Any]] = []
        self._tools_loaded = False
        self._request_id = 0
        self._initialized = False
        self._lock = asyncio.Lock()  # Add lock to prevent concurrency issues
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()
    
    def _get_next_request_id(self) -> int:
        """Get next request ID"""
        self._request_id += 1
        return self._request_id
    
    async def initialize(self):
        """Initialize MCP client"""
        async with self._lock:
            if self._initialized:
                return
                
            try:
                # Use command with log redirection
                # if mcp_config.enable_debug_log:
                #     command = mcp_config.server_command_with_log_redirect
                #     # Ensure log directory exists
                #     log_dir = os.path.dirname(mcp_config.debug_log_path)
                #     os.makedirs(log_dir, exist_ok=True)
                #     logger.info("Using log redirection", 
                #             log_file=mcp_config.debug_log_path)
                # else:
                command = mcp_config.actual_server_command
                
                logger.info("Starting MCP server process", 
                        command=command,
                        cwd=mcp_config.mcp_cwd,
                        debug_log_enabled=mcp_config.enable_debug_log)
                
                # Check if working directory exists
                if not os.path.exists(mcp_config.mcp_cwd):
                    raise Exception(f"MCP server directory not found: {mcp_config.mcp_cwd}")
                
                # Check if command file exists
                if not os.path.exists(mcp_config.mcp_command):
                    raise Exception(f"MCP command not found: {mcp_config.mcp_command}")
                
                # Set environment variables
                env = os.environ.copy()
                env['PYTHONDONTWRITEBYTECODE'] = '1'
                env['PYTHONUNBUFFERED'] = '1'

                # Remove debug variables that may affect MCP process
                env.pop('DEBUGPY_LAUNCHER_PORT', None)
                env.pop('PYDEVD_LOAD_VALUES_ASYNC', None)
                
                # Start MCP server process
                self.process = await asyncio.create_subprocess_exec(
                    *command,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,  # Keep for error handling
                    cwd=mcp_config.mcp_cwd,
                    env=env
                )
                
                logger.info("Process started", pid=self.process.pid)
                
                # Wait for process to start
                await asyncio.sleep(1)
                
                # Check if process started normally
                if self.process.returncode is not None:
                    stderr_output = ""
                    if self.process.stderr:
                        try:
                            stderr_data = await asyncio.wait_for(
                                self.process.stderr.read(1024), timeout=1.0
                            )
                            stderr_output = stderr_data.decode()
                        except:
                            pass
                    
                    logger.error("Process failed to start", 
                            stderr=stderr_output, 
                            return_code=self.process.returncode)
                    
                    raise Exception(f"MCP server process failed to start: {stderr_output}")
                
                # Send initialization request
                await self._send_initialize()
                
                # Load available tools
                await self._load_available_tools()
                
                self._initialized = True
                
                logger.info(
                    "MCP client initialized successfully",
                    tools_count=len(self.available_tools),
                    available_tools=[tool.get("name") for tool in self.available_tools],
                    log_file=mcp_config.debug_log_path if mcp_config.enable_debug_log else None
                )
                
            except Exception as e:
                logger.error("Failed to initialize MCP client", error=str(e))
                await self.cleanup()
                raise

    
    async def _read_stderr(self) -> str:
        """Read stderr output"""
        if not self.process or not self.process.stderr:
            return ""
        
        try:
            stderr_data = await asyncio.wait_for(
                self.process.stderr.read(2048), timeout=1.0
            )
            return stderr_data.decode()
        except:
            return ""
        
    async def _read_json_response(self) -> Dict[str, Any]:
        """Read JSON response, filter out log lines"""
        if not self.process or not self.process.stdout:
            raise Exception("Process not available")
        
        # First check process status
        if self.process.returncode is not None:
            logger.error("Process already terminated", return_code=self.process.returncode)
            raise Exception(f"MCP server process terminated: {self.process.returncode}")
        
        collected_lines = []
        start_time = asyncio.get_event_loop().time()
        max_wait_time = min(mcp_config.timeout, 60.0)  # Wait up to 60 seconds
        
        logger.debug("Starting to read JSON response", max_wait_time=max_wait_time)
        
        # Simplified logic: loop until response is found or timeout
        while True:
            # Check if total time exceeded
            elapsed_time = asyncio.get_event_loop().time() - start_time
            if elapsed_time >= max_wait_time:
                logger.error("Total timeout exceeded while waiting for JSON-RPC response",
                            elapsed_time=elapsed_time,
                            max_wait_time=max_wait_time,
                            lines_collected=len(collected_lines))
                break
            
            try:
                # Remaining time
                remaining_time = max_wait_time - elapsed_time
                # Single read timeout: max 5 seconds but not exceeding remaining time
                line_timeout = min(5.0, remaining_time)
                
                if line_timeout <= 0:
                    logger.warning("No time remaining")
                    break
                
                logger.debug("Reading line from stdout", 
                            timeout=line_timeout,
                            elapsed_time=elapsed_time)
                
                line = await asyncio.wait_for(
                    self.process.stdout.readline(),
                    timeout=line_timeout
                )
                
                # Check if there is data
                if not line:
                    # No data, check process status
                    if self.process.returncode is not None:
                        stderr_output = await self._read_stderr()
                        logger.error("MCP server process terminated", 
                            return_code=self.process.returncode,
                            stderr=stderr_output)
                        raise Exception(f"MCP server process terminated: {self.process.returncode}")
                    else:
                        # Process is alive but no data, might be temporary
                        logger.debug("No data available, continuing...")
                        await asyncio.sleep(0.1)  # Brief wait
                        continue
                
                line_str = line.decode().strip()
                
                # Skip empty lines
                if not line_str:
                    continue
                
                # Record non-empty lines
                collected_lines.append(line_str)
                logger.debug("Received line", 
                            line_preview=line_str[:100],
                            total_lines=len(collected_lines))
                
                # Try to parse JSON
                try:
                    data = json.loads(line_str)
                    logger.debug("Successfully parsed JSON", data_type=type(data).__name__)
                    
                    # Check if it's a valid response
                    if isinstance(data, dict):
                        # Standard JSON-RPC response
                        if data.get("jsonrpc") == "2.0":
                            logger.info("Found JSON-RPC response", 
                                    response_id=data.get("id"),
                                    elapsed_time=elapsed_time)
                            return data  # Found valid response, exit loop
                        
                        # MCP tool response format
                        elif ("content" in data and isinstance(data.get("content"), list)) or \
                            ("isError" in data) or \
                            ("result" in data and "error" not in data and "jsonrpc" not in data):
                            logger.info("Found MCP response, wrapping as JSON-RPC",
                                    elapsed_time=elapsed_time)
                            return {  # Found valid response, exit loop
                                "jsonrpc": "2.0",
                                "id": getattr(self, '_current_request_id', 1),
                                "result": data
                            }
                        else:
                            # Is JSON but not expected format, continue reading
                            logger.debug("JSON found but not expected format")
                            
                except json.JSONDecodeError:
                    # Not JSON, might be log, continue reading
                    logger.debug("Skipping non-JSON line", 
                            line_preview=line_str[:50])
                
                # Output status every 20 lines
                if len(collected_lines) % 20 == 0:
                    logger.info("Still reading lines", 
                            lines_read=len(collected_lines),
                            elapsed_time=elapsed_time)
                
            except asyncio.TimeoutError:
                logger.debug("Timeout reading line", 
                            timeout=line_timeout,
                            elapsed_time=elapsed_time)
                
                # Check process status
                if self.process.returncode is not None:
                    stderr_output = await self._read_stderr()
                    logger.error("Process died during timeout", 
                                return_code=self.process.returncode)
                    raise Exception(f"MCP server process died: {self.process.returncode}")
                
                # Timeout but process is alive, continue trying
                continue
            
            except Exception as e:
                logger.error("Unexpected error while reading", error=str(e))
                break
        
        # If we get here, timeout or error occurred
        stderr_output = await self._read_stderr()
        elapsed_time = asyncio.get_event_loop().time() - start_time
        
        logger.error("Failed to get JSON-RPC response", 
                    elapsed_time=elapsed_time,
                    lines_collected=len(collected_lines),
                    process_alive=self.process.returncode is None)
        
        # Output debug information
        if collected_lines:
            logger.error("Sample collected lines",
                        first_3=collected_lines[:3],
                        last_3=collected_lines[-3:] if len(collected_lines) > 3 else [])
        
        if stderr_output:
            logger.error("Stderr output", stderr=stderr_output[:500])
        
        raise Exception(f"No JSON-RPC response received within {max_wait_time}s. "
                    f"Read {len(collected_lines)} lines. "
                    f"Process alive: {self.process.returncode is None}")

    
    async def _send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send JSON-RPC request"""
        if not self.process or not self.process.stdin:
            raise RuntimeError("MCP server process is not running")
        
        request_id = self._get_next_request_id()
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {}
        }
        
        try:
            # Send request
            request_line = json.dumps(request) + "\n"
            logger.debug("Sending MCP request", 
                        method=method, 
                        request_id=request_id,
                        params=params)
            
            self.process.stdin.write(request_line.encode())
            await self.process.stdin.drain()
            
            # Check process status
            if self.process.returncode is not None:
                stderr_output = await self._read_stderr()
                logger.error("Process died before response", 
                            return_code=self.process.returncode,
                            stderr=stderr_output)
                raise Exception(f"MCP server process died: {self.process.returncode}")
            
            # Read response - use more reasonable timeout
            try:
                # Use longer timeout for initialization and important operations
                if method in ["initialize", "tools/list"]:
                    timeout = 45.0  # Increase initialization timeout
                elif method == "tools/call":
                    timeout = min(mcp_config.timeout * 2, 60.0)  # Longer timeout for tool calls
                else:
                    timeout = min(mcp_config.timeout, 30.0)
                
                response = await asyncio.wait_for(
                    self._read_json_response(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                # Enhanced timeout error handling
                stderr_output = await self._read_stderr()
                process_alive = self.process.returncode is None
                
                logger.error("MCP server response timeout", 
                            method=method, 
                            timeout=timeout,
                            process_alive=process_alive,
                            stderr=stderr_output[:500] if stderr_output else None,
                            request_id=request_id)
                
                # Throw more specific error if process died
                if not process_alive:
                    raise Exception(f"MCP server process died during {method} request (return code: {self.process.returncode})")
                else:
                    raise Exception(f"MCP server response timeout for method: {method} (timeout: {timeout}s)")
            
            # Check for errors
            if "error" in response:
                error = response["error"]
                logger.error("MCP server returned error", error=error, method=method)
                raise Exception(f"MCP error: {error.get('message', 'Unknown error')}")
            
            return response.get("result", {})
            
        except Exception as e:
            logger.error("Error sending MCP request", 
                        method=method, 
                        error=str(e),
                        process_alive=self.process.returncode is None if self.process else False)
            raise

    
    async def _send_notification(self, method: str, params: Dict[str, Any] = None):
        """Send notification (no response)"""
        if not self.process or not self.process.stdin:
            raise RuntimeError("MCP server process is not running")
        
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }
        
        try:
            notification_line = json.dumps(notification) + "\n"
            logger.debug("Sending MCP notification", method=method)
            
            self.process.stdin.write(notification_line.encode())
            await self.process.stdin.drain()
            
        except Exception as e:
            logger.error("Error sending MCP notification", method=method, error=str(e))
            raise
    
    async def _send_initialize(self):
        """Send initialization request"""
        params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "ai-agent",
                "version": "1.0.0"
            }
        }
        
        result = await self._send_request("initialize", params)
        logger.info("MCP server initialized", capabilities=result.get("capabilities", {}))
        
        # Send initialization complete notification
        await self._send_notification("notifications/initialized")
    
    async def _load_available_tools(self):
        """Load available tools list"""
        try:
            result = await self._send_request("tools/list")
            self.available_tools = result.get("tools", [])
            self._tools_loaded = True
            
            logger.info(
                "Available tools loaded",
                tools=[tool.get("name") for tool in self.available_tools]
            )
                    
        except Exception as e:
            logger.error("Error loading available tools", error=str(e))
            # Set default tools list as fallback
            self.available_tools = []
            self._tools_loaded = True
            logger.warning("Using empty tools list due to error")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP tool - directly call MCP server"""
        if not self._initialized:
            await self.initialize()
        
        logger.info("Calling MCP tool", 
                   tool_name=tool_name, 
                   arguments=arguments)
        
        try:
            # Build MCP tool call parameters
            params = {
                "name": tool_name,
                "arguments": arguments,
            }
            
            # Send tool call request to MCP server
            result = await self._send_request("tools/call", params)
            
            logger.info("MCP tool call successful", 
                       tool_name=tool_name,
                       result_type=type(result).__name__)
            
            return result
                    
        except Exception as e:
            logger.error("Error calling MCP tool", 
                        tool_name=tool_name, 
                        arguments=arguments,
                        error=str(e))
            raise
    
    # Convenience methods (optional, for backward compatibility and ease of use)
    async def search_papers(self, query: str, limit: int = 10, fields: List[str] = None) -> Dict[str, Any]:
        """Search papers - convenience method"""
        arguments = {
            "query": query,
            "limit": limit
        }
        if fields:
            arguments["fields"] = fields
        
        return await self.call_tool("search_papers", arguments)
    
    async def get_paper_details(self, paper_id: str) -> Dict[str, Any]:
        """Get paper details - convenience method"""
        return await self.call_tool("get_paper_details", {"paper_id": paper_id})
    
    async def search_authors(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search authors - convenience method"""
        # Depending on MCP server's expectations, may need to send both query and name parameters
        arguments = {
            "query": query,      # Main parameter
            "name": query,       # Backup parameter, in case server expects this field
            "limit": limit,
            "include_coauthors": True
        }
        
        result = await self.call_tool("search_authors", arguments)
        
        # If in MCP format, extract actual data
        if result.get("mcp_format") and "authors" in result:
            return {
                "authors": result["authors"],
                "count": result.get("count", len(result.get("authors", []))),
                "query": query,
                "limit": limit
            }
        
        return result
    
    async def get_author_details(self, author_id: str) -> Dict[str, Any]:
        """Get author details - convenience method"""
        return await self.search_authors(query=author_id, limit=1)
    
    async def get_citation_network(self, paper_id: str, depth: int = 2) -> Dict[str, Any]:
        """Get citation network - convenience method"""
        return await self.call_tool("get_citation_network", {"paper_id": paper_id, "depth": depth})
    
    async def get_collaboration_network(self, author_id: str, depth: int = 2) -> Dict[str, Any]:
        """Get collaboration network - convenience method"""
        return await self.call_tool("get_collaboration_network", {"author_id": author_id, "depth": depth})
    
    async def get_trending_papers(self, field: str = "", time_range: str = "1year") -> Dict[str, Any]:
        """Get trending papers - convenience method"""
        return await self.call_tool("get_trending_papers", {"field": field, "time_range": time_range})
    
    # Retry mechanism
    async def call_tool_with_retry(self, tool_name: str, arguments: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
        """Tool call with retry mechanism"""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.debug("Attempting tool call", 
                           tool_name=tool_name, 
                           attempt=attempt + 1,
                           arguments=arguments)
                
                result = await self.call_tool(tool_name, arguments)
                
                if attempt > 0:
                    logger.info("Tool call succeeded after retry", 
                              tool_name=tool_name, 
                              attempt=attempt + 1)
                
                return result
                
            except Exception as e:
                last_error = e
                logger.warning("Tool call failed", 
                             tool_name=tool_name, 
                             attempt=attempt + 1, 
                             error=str(e))
                
                if attempt < max_retries - 1:
                    # Wait before retrying
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info("Retrying after delay", delay=wait_time)
                    await asyncio.sleep(wait_time)
                    
                    # If process died, try to reinitialize
                    if self.process and self.process.returncode is not None:
                        logger.warning("Process died, reinitializing...")
                        await self.cleanup()
                        await self.initialize()
        
        logger.error("Tool call failed after all retries", 
                    tool_name=tool_name, 
                    error=str(last_error))
        raise last_error
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get available tools list"""
        return self.available_tools.copy()
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check"""
        try:
            if not self._initialized:
                await self.initialize()
            
            # Check process status
            process_running = self.process is not None and self.process.returncode is None
            
            # Try to get tools list
            tools_accessible = False
            try:
                await self._send_request("tools/list")
                tools_accessible = True
            except:
                pass
            
            status = "healthy" if process_running and tools_accessible else "unhealthy"
            
            return {
                "status": status,
                "tools_count": len(self.available_tools),
                "process_running": process_running,
                "tools_accessible": tools_accessible,
                "available_tools": [tool.get("name") for tool in self.available_tools]
            }
            
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "process_running": False,
                "tools_accessible": False
            }
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            logger.info("Cleaning up MCP client")
            
            if self.process:
                # Try graceful shutdown
                if self.process.returncode is None:
                    try:
                        # Send shutdown notification
                        await asyncio.wait_for(
                            self._send_notification("notifications/shutdown"),
                            timeout=2.0
                        )
                    except:
                        pass
                    
                    # Close stdin
                    if self.process.stdin:
                        self.process.stdin.close()
                        await self.process.stdin.wait_closed()
                    
                    # Wait for process to end
                    try:
                        await asyncio.wait_for(self.process.wait(), timeout=5.0)
                    except asyncio.TimeoutError:
                        logger.warning("Process did not terminate gracefully, killing")
                        self.process.kill()
                        await self.process.wait()
                
                self.process = None
            
            self._initialized = False
            self._tools_loaded = False
            
            logger.info("MCP client cleanup completed")
            
        except Exception as e:
            logger.error("Error during MCP client cleanup", error=str(e))
            
mcp_client_stdio = MCPClient()

