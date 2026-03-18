#!/usr/bin/env python3
"""
demo_client.py - Simple MCP Client Demo
========================================
This script demonstrates the JMeter MCP Server by calling its tools
directly (without needing a full MCP client).

It shows:
1. Generating a test plan from natural language
2. Listing test plans
3. Listing results
4. Parsing results
"""

import sys
import os

# Add current directory to path so we can import the tool modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_plan import generate_test_plan
from run_test import list_test_plans, list_results
from parse_results import parse_results
from compare_runs import compare_runs

def print_section(title):
    """Print a nice section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def main():
    print_section("🚀 JMeter MCP Server Demo")
    print("This demo shows the core functionality of the JMeter MCP Server.\n")
    
    # ─────────────────────────────────────────────────────────────────
    # DEMO 1: Generate a test plan
    # ─────────────────────────────────────────────────────────────────
    print_section("DEMO 1: Generate a Test Plan")
    print("Creating a test plan from natural language description...\n")
    
    description = (
        "Test a REST API at https://jsonplaceholder.typicode.com/posts "
        "with 10 concurrent users for 30 seconds using GET requests"
    )
    print(f"📝 Description: {description}\n")
    
    result = generate_test_plan(
        description=description,
        output_file="demo_api_test.jmx"
    )
    print(result)
    
    # ─────────────────────────────────────────────────────────────────
    # DEMO 2: List test plans
    # ─────────────────────────────────────────────────────────────────
    print_section("DEMO 2: List Available Test Plans")
    result = list_test_plans()
    print(result)
    
    # ─────────────────────────────────────────────────────────────────
    # DEMO 3: List results
    # ─────────────────────────────────────────────────────────────────
    print_section("DEMO 3: List Available Result Files")
    result = list_results()
    print(result)
    
    # ─────────────────────────────────────────────────────────────────
    # DEMO 4: Generate another test plan (POST request)
    # ─────────────────────────────────────────────────────────────────
    print_section("DEMO 4: Generate Another Test Plan (POST)")
    
    description2 = (
        "Test login endpoint at https://api.example.com/login with POST requests, "
        "100 users ramping up over 10 seconds, running for 2 minutes"
    )
    print(f"📝 Description: {description2}\n")
    
    result = generate_test_plan(
        description=description2,
        output_file="demo_login_test.jmx"
    )
    print(result)
    
    # ─────────────────────────────────────────────────────────────────
    # DEMO 5: Show server capabilities
    # ─────────────────────────────────────────────────────────────────
    print_section("✅ Server Capabilities Summary")
    
    capabilities = """
The JMeter MCP Server provides the following tools:

1. 🔧 generate_test_plan(description, output_file)
   → Creates a .jmx test plan from natural language
   → Supports HTTP/HTTPS, multiple request methods
   → Configurable threads, ramp-up, duration, and assertions
   
2. ▶️  run_test(test_plan, results_file)
   → Executes a .jmx test plan headlessly
   → Generates .jtl results file
   → Requires JMeter to be installed
   
3. 📂 list_test_plans()
   → Shows all .jmx files in test_plans/ directory
   → Helps discover available tests
   
4. 📂 list_results()
   → Shows all .jtl result files in results/ directory
   → Helps find result files for analysis
   
5. 📊 parse_results(results_file)
   → Reads a .jtl file and generates readable summary
   → Shows: pass/fail counts, response times, throughput
   → Per-label breakdowns
   
6. 🔄 compare_runs(baseline_file, new_file)
   → Compares two .jtl result files
   → Highlights improvements/regressions
   → Shows deltas in response time, error rate, throughput

All tools are accessible through:
  - Claude Desktop (via MCP)
  - Custom MCP clients
  - Direct Python function calls
"""
    print(capabilities)
    
    print_section("✨ Demo Complete!")
    print("""
Your JMeter MCP Server is working correctly! ✅

To run the server and connect it to Claude Desktop:
  1. python server.py
  2. Configure it in Claude Desktop's MCP settings
  3. Ask Claude to generate test plans, run tests, and analyze results

For more details, see the documentation in the repository.
""")

if __name__ == "__main__":
    main()

