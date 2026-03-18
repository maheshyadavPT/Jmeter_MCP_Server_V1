#!/usr/bin/env python3
"""
mcp_test_client.py - Simple MCP Protocol Test Client
=====================================================
This script starts the JMeter MCP server as a subprocess and
sends MCP protocol messages to test the tools without Claude Desktop.
"""

import json
import subprocess
import sys
import threading
import time
from pathlib import Path

def send_mcp_request(process, method, params=None):
    """Send an MCP request to the server and read the response."""
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
    }
    if params:
        request["params"] = params
    
    request_json = json.dumps(request) + "\n"
    print(f"\n📤 Sending: {method}")
    print(f"   Request: {json.dumps(request, indent=2)}")
    
    try:
        process.stdin.write(request_json.encode())
        process.stdin.flush()
        
        # Read response (with timeout)
        time.sleep(0.5)  # Give server time to process
        response_line = process.stdout.readline().decode()
        
        if response_line:
            response = json.loads(response_line)
            print(f"✅ Response: {json.dumps(response, indent=2)}")
            return response
        else:
            print("❌ No response received")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    print("=" * 70)
    print("JMeter MCP Server Test Client")
    print("=" * 70)
    
    # Start the server
    print("\n🚀 Starting JMeter MCP Server...")
    server_path = Path(__file__).parent / "server.py"
    
    try:
        process = subprocess.Popen(
            [sys.executable, str(server_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,
            bufsize=1
        )
        print("✅ Server started successfully")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return
    
    # Give server time to start
    time.sleep(1)
    
    # Test 1: Initialize
    print("\n" + "=" * 70)
    print("Test 1: Initialize")
    print("=" * 70)
    send_mcp_request(process, "initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {
            "name": "test-client",
            "version": "1.0.0"
        }
    })
    
    # Test 2: List Tools
    print("\n" + "=" * 70)
    print("Test 2: List Available Tools")
    print("=" * 70)
    send_mcp_request(process, "tools/list")
    
    # Test 3: List Test Plans
    print("\n" + "=" * 70)
    print("Test 3: Call list_test_plans Tool")
    print("=" * 70)
    send_mcp_request(process, "tools/call", {
        "name": "list_test_plans",
        "arguments": {}
    })
    
    # Test 4: List Results
    print("\n" + "=" * 70)
    print("Test 4: Call list_results Tool")
    print("=" * 70)
    send_mcp_request(process, "tools/call", {
        "name": "list_results",
        "arguments": {}
    })
    
    # Test 5: Generate Test Plan
    print("\n" + "=" * 70)
    print("Test 5: Call generate_test_plan Tool")
    print("=" * 70)
    send_mcp_request(process, "tools/call", {
        "name": "generate_test_plan",
        "arguments": {
            "description": "Test a simple HTTP GET to https://httpbin.org/get with 5 users for 10 seconds"
        }
    })
    
    # Cleanup
    print("\n" + "=" * 70)
    print("Shutting down server...")
    print("=" * 70)
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
    
    print("✅ Test complete")

if __name__ == "__main__":
    main()

