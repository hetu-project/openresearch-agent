#!/usr/bin/env python3
"""
Test the search_authors tool of MCP server
"""
import asyncio
import json
import sys
import os
from datetime import datetime
import subprocess

# MCP Server Configuration
MCP_SERVER_PATH = "/Users/zhouxin/Workspace/ai-space/openresearch/openresearch-mcp-server"
MCP_PYTHON = os.path.join(MCP_SERVER_PATH, "venv/bin/python")
MCP_COMMAND = os.path.join(MCP_SERVER_PATH, "src/main.py")

class MCPTester:
    def __init__(self):
        self.process = None
        self.request_id = 0
    
    def get_next_id(self):
        self.request_id += 1
        return self.request_id
    
    async def start_server(self):
        """Start MCP server"""
        print(f"🚀 Starting MCP server...")
        print(f"   Python: {MCP_PYTHON}")
        print(f"   Command: {MCP_COMMAND}")
        print(f"   CWD: {MCP_SERVER_PATH}")
        
        # Check if files exist
        if not os.path.exists(MCP_PYTHON):
            raise Exception(f"Python interpreter not found: {MCP_PYTHON}")
        if not os.path.exists(MCP_COMMAND):
            raise Exception(f"MCP command not found: {MCP_COMMAND}")
        
        # Set environment variables
        env = os.environ.copy()
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        env.pop('DEBUGPY_LAUNCHER_PORT', None)
        env.pop('PYDEVD_LOAD_VALUES_ASYNC', None)
        
        # Start process
        self.process = await asyncio.create_subprocess_exec(
            MCP_PYTHON, MCP_COMMAND,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=MCP_SERVER_PATH,
            env=env
        )
        
        print(f"✅ Process started, PID: {self.process.pid}")
        
        # Wait for server to start
        await asyncio.sleep(2)
        
        # Check process status
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
            raise Exception(f"Process failed to start: {stderr_output}")
    
    async def send_request(self, method: str, params: dict = None) -> dict:
        """Send JSON-RPC request"""
        if not self.process or not self.process.stdin:
            raise Exception("Process not started")
        
        request_id = self.get_next_id()
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {}
        }
        
        print(f"📤 Sending request: {method}")
        print(f"   ID: {request_id}")
        print(f"   Parameters: {json.dumps(params, indent=2, ensure_ascii=False)}")
        
        # Send request
        request_line = json.dumps(request, ensure_ascii=False) + "\n"
        self.process.stdin.write(request_line.encode('utf-8'))
        await self.process.stdin.drain()
        
        # Read response
        response = await self.read_response()
        
        if "error" in response:
            print(f"❌ Error response: {response['error']}")
            raise Exception(f"MCP error: {response['error']}")
        
        print(f"✅ Success response")
        return response.get("result", {})
    
    async def send_notification(self, method: str, params: dict = None):
        """Send notification (no response)"""
        if not self.process or not self.process.stdin:
            raise Exception("Process not started")
        
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }
        
        print(f"📢 Sending notification: {method}")
        
        notification_line = json.dumps(notification, ensure_ascii=False) + "\n"
        self.process.stdin.write(notification_line.encode('utf-8'))
        await self.process.stdin.drain()
    
    async def read_response(self, timeout: float = 30.0) -> dict:
        """Read JSON response"""
        if not self.process or not self.process.stdout:
            raise Exception("Process not available")
        
        max_attempts = 50
        attempt = 0
        collected_lines = []
        
        while attempt < max_attempts:
            try:
                line = await asyncio.wait_for(
                    self.process.stdout.readline(),
                    timeout=timeout if attempt == 0 else 5.0
                )
                
                if not line:
                    raise Exception("Server connection lost")
                
                line_str = line.decode('utf-8').strip()
                collected_lines.append(line_str)
                
                print(f"📥 Received data: {line_str[:100]}{'...' if len(line_str) > 100 else ''}")
                
                if not line_str:
                    attempt += 1
                    continue
                
                try:
                    data = json.loads(line_str)
                    if isinstance(data, dict) and data.get("jsonrpc") == "2.0":
                        return data
                except json.JSONDecodeError:
                    print(f"   ⚠️  Non-JSON data, continue reading...")
                
                attempt += 1
                
            except asyncio.TimeoutError:
                print(f"   ⏰ Read timeout, attempt {attempt + 1}/{max_attempts}")
                attempt += 1
                continue
        
        print(f"❌ No valid response found, collected lines:")
        for i, line in enumerate(collected_lines[-10:]):
            print(f"   {i}: {line}")
        
        raise Exception("No valid JSON-RPC response found")
    
    async def initialize(self):
        """Initialize MCP connection"""
        print("\n🔧 Initializing MCP connection...")
        
        params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "mcp-tester",
                "version": "1.0.0"
            }
        }
        
        result = await self.send_request("initialize", params)
        print(f"   Server capabilities: {json.dumps(result.get('capabilities', {}), indent=2, ensure_ascii=False)}")
        
        # Send initialized notification
        await self.send_notification("notifications/initialized")
        print("✅ Initialization complete")
    
    async def list_tools(self):
        """Get tool list"""
        print("\n🔍 Getting tool list...")
        
        result = await self.send_request("tools/list")
        tools = result.get("tools", [])
        
        print(f"   Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool.get('name')}: {tool.get('description', 'N/A')}")
        
        return tools
    
    async def test_search_authors(self, query: str = "Jiajing Wu", limit: int = 10):
        """Test search_authors tool"""
        print(f"\n🔎 Testing search_authors tool...")
        print(f"   Query: {query}")
        print(f"   Limit: {limit}")
        
        params = {
            "name": "search_authors",
            "arguments": {
                "query": query,
                "limit": limit
            }
        }
        
        result = await self.send_request("tools/call", params)
        
        print(f"📊 Search results:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Parse results
        if "content" in result:
            for content_item in result["content"]:
                if content_item.get("type") == "text":
                    try:
                        data = json.loads(content_item["text"])
                        if "authors" in data:
                            authors = data["authors"]
                            print(f"\n   Found {len(authors)} authors:")
                            for i, author in enumerate(authors[:5], 1):  # Only show first 5
                                print(f"   {i}. {author.get('name', 'N/A')}")
                                print(f"      ID: {author.get('authorId', 'N/A')}")
                                print(f"      Papers: {author.get('paperCount', 'N/A')}")
                                print(f"      Citations: {author.get('citationCount', 'N/A')}")
                                if author.get('affiliations'):
                                    print(f"      Affiliation: {author['affiliations'][0] if author['affiliations'] else 'N/A'}")
                                print()
                    except json.JSONDecodeError:
                        print(f"   Text content: {content_item['text'][:200]}...")
        
        return result
    
    async def cleanup(self):
        """Clean up resources"""
        print("\n🧹 Cleaning up resources...")
        
        if self.process:
            try:
                # Try graceful shutdown
                if self.process.returncode is None:
                    await self.send_notification("notifications/shutdown")
                    
                    if self.process.stdin:
                        self.process.stdin.close()
                        await self.process.stdin.wait_closed()
                    
                    # Wait for process to end
                    try:
                        await asyncio.wait_for(self.process.wait(), timeout=5.0)
                    except asyncio.TimeoutError:
                        print("   ⚠️  Process did not end normally, force terminating")
                        self.process.kill()
                        await self.process.wait()
                
                print("✅ Cleanup complete")
            except Exception as e:
                print(f"⚠️  Error during cleanup: {e}")

async def main():
    """Main test function"""
    print("🧪 MCP search_authors Tool Test")
    print("=" * 50)
    
    tester = MCPTester()
    
    try:
        # Start server
        await tester.start_server()
        
        # Initialize connection
        await tester.initialize()
        
        # Get tool list
        tools = await tester.list_tools()
        
        # Check if search_authors tool exists
        search_authors_tool = None
        for tool in tools:
            if tool.get("name") == "search_authors":
                search_authors_tool = tool
                break
        
        if not search_authors_tool:
            print("❌ search_authors tool not found")
            return
        
        print(f"✅ Found search_authors tool:")
        print(f"   Description: {search_authors_tool.get('description', 'N/A')}")
        print(f"   Parameters: {json.dumps(search_authors_tool.get('inputSchema', {}), indent=2, ensure_ascii=False)}")
        
        # Test different queries
        test_queries = [
            ("Jiajing Wu", 10),
            ("Andrew Ng", 5),
            ("Geoffrey Hinton", 3)
        ]
        
        for query, limit in test_queries:
            try:
                await tester.test_search_authors(query, limit)
                print(f"✅ Query '{query}' successful")
            except Exception as e:
                print(f"❌ Query '{query}' failed: {e}")
            
            print("-" * 30)
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher required")
        sys.exit(1)
    
    # Run test
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  User interrupted test")
    except Exception as e:
        print(f"❌ Runtime error: {e}")
        sys.exit(1)