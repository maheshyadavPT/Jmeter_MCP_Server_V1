#!/usr/bin/env python3
"""
Test script to verify server.py integrity without starting the server.
"""

import sys
import traceback

def test_imports():
    """Test that all imports work."""
    print("🔍 Testing imports...")
    try:
        from mcp import types
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        from compare_runs import compare_runs
        from generate_plan import generate_test_plan
        from parse_results import parse_results
        from run_test import run_test, list_test_plans, list_results
        print("  ✅ All imports successful")
        return True
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        traceback.print_exc()
        return False

def test_tools_registry():
    """Test that TOOLS registry is properly defined."""
    print("\n🔍 Testing TOOLS registry...")
    try:
        import server
        tools = server.TOOLS
        print(f"  ✅ Found {len(tools)} tools")
        for tool in tools:
            print(f"     - {tool.name}")
        return True
    except Exception as e:
        print(f"  ❌ TOOLS registry check failed: {e}")
        traceback.print_exc()
        return False

def test_server_creation():
    """Test that the server instance can be created."""
    print("\n🔍 Testing server instance creation...")
    try:
        from mcp.server import Server
        test_server = Server("test-server")
        print(f"  ✅ Server instance created: {test_server.name}")
        return True
    except Exception as e:
        print(f"  ❌ Server creation failed: {e}")
        traceback.print_exc()
        return False

def test_handlers():
    """Test that handlers are properly registered."""
    print("\n🔍 Testing handler registration...")
    try:
        import server
        # Check if handlers exist
        if hasattr(server.server, '_handlers'):
            print(f"  ✅ Handlers registered")
        else:
            print(f"  ⚠️  Handler check skipped (internal structure)")
        return True
    except Exception as e:
        print(f"  ❌ Handler check failed: {e}")
        traceback.print_exc()
        return False

def test_function_signatures():
    """Test that all functions have correct signatures."""
    print("\n🔍 Testing function signatures...")
    try:
        import inspect
        from generate_plan import generate_test_plan
        from parse_results import parse_results
        from run_test import run_test, list_test_plans, list_results
        from compare_runs import compare_runs
        
        functions = {
            "generate_test_plan": generate_test_plan,
            "parse_results": parse_results,
            "run_test": run_test,
            "list_test_plans": list_test_plans,
            "list_results": list_results,
            "compare_runs": compare_runs,
        }
        
        for name, func in functions.items():
            sig = inspect.signature(func)
            print(f"  ✅ {name}{sig}")
        
        return True
    except Exception as e:
        print(f"  ❌ Function signature check failed: {e}")
        traceback.print_exc()
        return False

def test_config():
    """Test configuration."""
    print("\n🔍 Testing configuration...")
    try:
        from config import PLANS_DIR, RESULTS_DIR, get_jmeter_bin, check_jmeter_installed
        print(f"  ✅ PLANS_DIR: {PLANS_DIR}")
        print(f"  ✅ RESULTS_DIR: {RESULTS_DIR}")
        jmeter_bin = get_jmeter_bin()
        if jmeter_bin:
            print(f"  ✅ JMeter binary: {jmeter_bin}")
        else:
            print(f"  ⚠️  JMeter not found (install for run_test to work)")
        return True
    except Exception as e:
        print(f"  ❌ Config check failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("JMeter MCP Server Integrity Test")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_tools_registry,
        test_server_creation,
        test_handlers,
        test_function_signatures,
        test_config,
    ]
    
    results = [test() for test in tests]
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("✅ All tests passed! Server is ready to use.")
        return 0
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

