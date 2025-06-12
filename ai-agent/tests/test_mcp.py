"""
Test MCP Connection
"""
import asyncio
import sys
from pathlib import Path

# Add project root directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services import mcp_client

async def test_mcp():
    try:
        print("=== Testing MCP Single Call ===")
        
        # Initialize
        await mcp_client.initialize()
        print("✅ Initialization successful")
        
        # Get tool list
        tools = mcp_client.get_available_tools()
        print(f"✅ Available tools: {[t.get('name') for t in tools]}")
        
        # Test paper search
        result = await mcp_client.search_papers("machine learning", limit=3)
        print(f"✅ Search results: {result}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp())