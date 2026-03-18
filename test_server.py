#!/usr/bin/env python3
"""
test_server.py - Test script for JMeter MCP Server functions
===========================================================
This script tests each tool function directly without the MCP protocol.
Run this to verify that the underlying functions work correctly.
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from generate_plan import generate_test_plan
from run_test import run_test, list_test_plans, list_results
from parse_results import parse_results
from compare_runs import compare_runs

def test_generate_plan():
    print("Testing generate_test_plan...")
    try:
        result = generate_test_plan(
            description="Test a simple HTTP GET request to http://httpbin.org/get with 10 users for 30 seconds"
        )
        print(f"[OK] Success: {result}")
    except Exception as e:
        print(f"[ERROR] Error: {e}")

def test_list_test_plans():
    print("Testing list_test_plans...")
    try:
        result = list_test_plans()
        print(f"[OK] Success: {result}")
    except Exception as e:
        print(f"[ERROR] Error: {e}")

def test_list_results():
    print("Testing list_results...")
    try:
        result = list_results()
        print(f"[OK] Success: {result}")
    except Exception as e:
        print(f"[ERROR] Error: {e}")

# Note: run_test and parse_results require actual files, so we'll skip them unless files exist
# compare_runs also requires two result files

if __name__ == "__main__":
    print("Starting JMeter MCP Server function tests...\n")
    test_generate_plan()
    print()
    test_list_test_plans()
    print()
    test_list_results()
    print("\nTest complete. Check for any errors above.")
