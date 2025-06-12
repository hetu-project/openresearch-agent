#!/usr/bin/env python3
import asyncio
import sys
import os

# Add project root directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.mcp_client_stdio import mcp_client_stdio
from configs.mcp_config import mcp_config

async def test_fixed_client():
    print("=== Testing Fixed MCP Client ===")
    
    # Clear log file
    with open(mcp_config.debug_log_path, 'w') as f:
        f.write("")
    print(f"Log file cleared: {mcp_config.debug_log_path}")
    
    try:
        async with mcp_client_stdio:
            print("✅ MCP Client initialized successfully")
            
            # Get available tools
            tools = mcp_client_stdio.get_available_tools()
            print(f"Number of available tools: {len(tools)}")
            for tool in tools:
                print(f"  - {tool.get('name')}: {tool.get('description', 'No description')}")
            
            # Test health check
            print("\nTesting health check...")
            health = await mcp_client_stdio.health_check()
            print(f"Health status: {health}")
            
            # Test author search
            print("\nTesting author search...")
            try:
                result = await mcp_client_stdio.search_authors("Jiajing Wu", limit=1)
                print(f"Search result type: {type(result)}")
                print(f"Search result: {result}")
            except Exception as e:
                print(f"Author search failed: {e}")
            
            print("✅ All tests completed")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Wait for logs to be written
    await asyncio.sleep(1)
    
    # Check log file
    print(f"\n=== Checking Log File ===")
    try:
        with open(mcp_config.debug_log_path, 'r') as f:
            log_content = f.read()
        
        print(f"Log file size: {len(log_content)} characters")
        if log_content:
            # Check for errors
            if "error" in log_content.lower() or "traceback" in log_content.lower():
                print("⚠️  Found error logs:")
                error_lines = [line for line in log_content.split('\n') if 'error' in line.lower() or 'traceback' in line.lower()]
                for line in error_lines[-5:]:  # Show last 5 errors
                    print(f"  {line}")
            else:
                print("✅ No errors found")
            
            print("\nLatest log content (last 300 characters):")
            print("-" * 50)
            print(log_content[-300:])
            print("-" * 50)
        else:
            print("❌ Log file is empty")
    except Exception as e:
        print(f"Failed to read log file: {e}")

if __name__ == "__main__":
    asyncio.run(test_fixed_client())