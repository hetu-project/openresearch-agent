#!/usr/bin/env python3
import subprocess
import sys
import os

def cleanup_mcp_processes():
    print("=== Cleaning up MCP processes ===")
    
    try:
        # Find MCP related processes
        result = subprocess.run([
            'pgrep', '-f', 'openresearch-mcp-server'
        ], capture_output=True, text=True)
        
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            print(f"Found MCP processes: {pids}")
            
            for pid in pids:
                try:
                    print(f"Terminating process {pid}")
                    subprocess.run(['kill', '-9', pid], check=True)
                    print(f"✅ Process {pid} terminated")
                except Exception as e:
                    print(f"❌ Cannot terminate process {pid}: {e}")
        else:
            print("No MCP processes found")
            
    except Exception as e:
        print(f"Cleanup process error: {e}")
    
    # Clear log file
    log_path = "/Users/zhouxin/Workspace/ai-space/openresearch/openresearch-mcp-server/logs/mcp_debug.log"
    try:
        with open(log_path, 'w') as f:
            f.write("")
        print(f"✅ Log file cleared: {log_path}")
    except Exception as e:
        print(f"❌ Failed to clear log file: {e}")

if __name__ == "__main__":
    cleanup_mcp_processes()