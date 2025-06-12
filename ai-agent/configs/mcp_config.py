"""
MCP Server Configuration
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import json
import os

class MCPConfig(BaseSettings):
    """MCP Server Configuration"""
    
    server_command: List[str] = Field(
        default=["python", "../../../openresearch-mcp-server/src/main.py"],
        env="MCP_SERVER_COMMAND"
    )

    host: str = Field(default="localhost", env="MCP_SERVER_HOST")
    port: int = Field(default=8000, env="MCP_SERVER_PORT")
    timeout: int = Field(default=60, env="MCP_SERVER_TIMEOUT")
    max_retries: int = Field(default=3, env="MCP_MAX_RETRIES")
    retry_delay: float = Field(default=1.0, env="MCP_RETRY_DELAY")
    
    enable_debug_log: bool = Field(default=True, env="MCP_ENABLE_DEBUG_LOG")
    debug_log_file: str = Field(default="logs/mcp_debug.log", env="MCP_DEBUG_LOG_FILE")
    
    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"
    
    @property
    def mcp_cwd(self) -> str:
        """MCP Server Working Directory"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.normpath(os.path.join(current_dir, "../../../openresearch-mcp-server"))
    
    @property
    def mcp_command(self) -> str:
        """MCP Server Main File Path"""
        return os.path.join(self.mcp_cwd, "src/main.py")
    
    @property
    def mcp_python(self) -> str:
        """MCP Server Python Interpreter Path"""
        return os.path.join(self.mcp_cwd, "venv/bin/python")
    
    @property
    def debug_log_path(self) -> str:
        """Full Path of Debug Log File"""
        if os.path.isabs(self.debug_log_file):
            return self.debug_log_file
        
        full_path = os.path.join(self.mcp_cwd, self.debug_log_file)
        
        log_dir = os.path.dirname(full_path)
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
                print(f"Created log directory: {log_dir}")
            except Exception as e:
                print(f"Failed to create log directory {log_dir}: {e}")
        
        return full_path

    @property
    def actual_server_command(self) -> List[str]:
        """Actual Server Command (Using Correct Python Path)"""
        return [self.mcp_python, self.mcp_command]
        
    @property
    def server_command_with_log_redirect(self) -> List[str]:
        """Server Command with Log Redirection"""
        if self.enable_debug_log:
            log_path = self.debug_log_path
            print(f"Using log file: {log_path}")
            
            return [
                "bash", "-c", 
                f'"{self.mcp_python}" "{self.mcp_command}" 2>> "{log_path}"'
            ]
        return self.actual_server_command

    def model_post_init(self, __context):
        """Post-initialization Processing"""
        if hasattr(self, '_env_server_command'):
            try:
                if isinstance(self._env_server_command, str):
                    self.server_command = json.loads(self._env_server_command)
            except:
                pass
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "allow"
    }
    
mcp_config = MCPConfig()
