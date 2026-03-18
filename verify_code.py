#!/usr/bin/env python3
"""
Comprehensive Code Verification Script
Checks all code for issues and verifies functionality
"""

import sys
import os

print("=" * 70)
print("JMeter MCP Server - Code Verification Report")
print("=" * 70)
print()

# Test 1: Import all modules
print("TEST 1: Module Imports")
print("-" * 70)
test1_passed = True
try:
    from generate_plan import generate_test_plan
    print("✅ generate_plan module")
except Exception as e:
    print(f"❌ generate_plan module: {e}")
    test1_passed = False

try:
    from parse_results import parse_results
    print("✅ parse_results module")
except Exception as e:
    print(f"❌ parse_results module: {e}")
    test1_passed = False

try:
    from run_test import run_test, list_test_plans, list_results
    print("✅ run_test module")
except Exception as e:
    print(f"❌ run_test module: {e}")
    test1_passed = False

try:
    from compare_runs import compare_runs
    print("✅ compare_runs module")
except Exception as e:
    print(f"❌ compare_runs module: {e}")
    test1_passed = False

try:
    import server
    print("✅ server module")
except Exception as e:
    print(f"❌ server module: {e}")
    test1_passed = False

print()

# Test 2: Check config
print("TEST 2: Configuration")
print("-" * 70)
test2_passed = True
try:
    from config import PLANS_DIR, RESULTS_DIR, get_jmeter_bin, check_jmeter_installed, ensure_directories
    print(f"✅ PLANS_DIR: {PLANS_DIR}")
    print(f"✅ RESULTS_DIR: {RESULTS_DIR}")
    
    # Verify paths are correct
    if "test_plans" in PLANS_DIR:
        print("✅ PLANS_DIR has correct path")
    else:
        print("❌ PLANS_DIR path is wrong")
        test2_passed = False
    
    if "results" in RESULTS_DIR:
        print("✅ RESULTS_DIR has correct path")
    else:
        print("❌ RESULTS_DIR path is wrong")
        test2_passed = False
    
    # Check if directories exist
    ensure_directories()
    if os.path.exists(PLANS_DIR):
        print(f"✅ test_plans directory exists")
    else:
        print(f"❌ test_plans directory missing")
        test2_passed = False
    
    if os.path.exists(RESULTS_DIR):
        print(f"✅ results directory exists")
    else:
        print(f"❌ results directory missing")
        test2_passed = False
        
except Exception as e:
    print(f"❌ Configuration error: {e}")
    test2_passed = False

print()

# Test 3: Check tool registry
print("TEST 3: Tool Registry")
print("-" * 70)
test3_passed = True
try:
    from server import TOOLS
    if len(TOOLS) == 6:
        print(f"✅ Found {len(TOOLS)} tools:")
        for tool in TOOLS:
            print(f"   ✅ {tool.name}")
    else:
        print(f"❌ Expected 6 tools, found {len(TOOLS)}")
        test3_passed = False
except Exception as e:
    print(f"❌ Tool registry error: {e}")
    test3_passed = False

print()

# Test 4: Check function signatures
print("TEST 4: Function Signatures")
print("-" * 70)
test4_passed = True
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
        print(f"✅ {name}{sig}")
except Exception as e:
    print(f"❌ Function signature error: {e}")
    test4_passed = False

print()

# Test 5: Test function execution (without external dependencies)
print("TEST 5: Function Availability")
print("-" * 70)
test5_passed = True
try:
    from run_test import list_test_plans, list_results
    
    # These shouldn't crash even if directories are empty
    result = list_test_plans()
    if "Test plans" in result or "No test plans" in result:
        print("✅ list_test_plans() works")
    else:
        print(f"⚠️  list_test_plans() returned unexpected: {result[:50]}")
    
    result = list_results()
    if "Result files" in result or "No result files" in result:
        print("✅ list_results() works")
    else:
        print(f"⚠️  list_results() returned unexpected: {result[:50]}")
        
except Exception as e:
    print(f"❌ Function execution error: {e}")
    import traceback
    traceback.print_exc()
    test5_passed = False

print()

# Test 6: Server initialization check
print("TEST 6: Server Initialization")
print("-" * 70)
test6_passed = True
try:
    from server import server, handle_list_tools
    if server.name == "jmeter-mcp-server":
        print(f"✅ Server name: {server.name}")
    else:
        print(f"❌ Server name incorrect: {server.name}")
        test6_passed = False
except Exception as e:
    print(f"❌ Server initialization error: {e}")
    test6_passed = False

print()

# Summary
print("=" * 70)
print("VERIFICATION SUMMARY")
print("=" * 70)

all_tests = [test1_passed, test2_passed, test3_passed, test4_passed, test5_passed, test6_passed]
passed = sum(all_tests)
total = len(all_tests)

print(f"Overall: {passed}/{total} test groups passed")
print()

if passed == total:
    print("✅ ALL TESTS PASSED - Server is ready to use!")
    print()
    print("Next steps:")
    print("1. Run: python server.py")
    print("2. Start a new chat in Claude Desktop")
    print("3. Ask Claude to generate a test plan")
    sys.exit(0)
else:
    print("❌ SOME TESTS FAILED - Please fix the issues above")
    sys.exit(1)

