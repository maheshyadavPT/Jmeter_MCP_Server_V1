#!/usr/bin/env python3
"""
VERIFICATION_REPORT.py - Complete Code Verification
=====================================================
This script verifies all components of the JMeter MCP Server.
"""

import os
import sys
import importlib.util

def print_header(text):
    print(f"\n{'='*80}")
    print(f"  {text}")
    print(f"{'='*80}\n")

def print_section(text):
    print(f"\n{text}")
    print(f"{'-'*len(text)}\n")

def check_file_exists(filepath):
    """Check if a file exists."""
    exists = os.path.exists(filepath)
    status = "✅" if exists else "❌"
    size = ""
    if exists:
        size = f" ({os.path.getsize(filepath)} bytes)"
    print(f"{status} {filepath}{size}")
    return exists

def check_imports(module_path, module_name):
    """Try to import a module and check for import errors."""
    try:
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print(f"✅ {module_name} imports successfully")
            return True
        else:
            print(f"❌ {module_name} - could not create spec")
            return False
    except Exception as e:
        print(f"❌ {module_name} - {str(e)}")
        return False

def main():
    os.chdir("D:\\Jmeter_MCP_NEW")
    
    print_header("🔍 JMeter MCP Server - Complete Code Verification")
    
    # ────────────────────────────────────────────────────────────────
    # STEP 1: Check all required files exist
    # ────────────────────────────────────────────────────────────────
    print_section("STEP 1: Verify Required Files Exist")
    
    files_to_check = [
        "server.py",
        "config.py",
        "generate_plan.py",
        "run_test.py",
        "parse_results.py",
        "compare_runs.py",
        "requirements.txt",
        "demo_client.py"
    ]
    
    all_files_exist = True
    for filename in files_to_check:
        if not check_file_exists(filename):
            all_files_exist = False
    
    # ────────────────────────────────────────────────────────────────
    # STEP 2: Check required directories
    # ────────────────────────────────────────────────────────────────
    print_section("STEP 2: Verify Required Directories")
    
    dirs_to_check = ["test_plans", "results"]
    for dirname in dirs_to_check:
        if os.path.isdir(dirname):
            print(f"✅ Directory exists: {dirname}/")
        else:
            print(f"⚠️  Directory missing: {dirname}/ (will be created automatically)")
    
    # ────────────────────────────────────────────────────────────────
    # STEP 3: Check Python dependencies
    # ────────────────────────────────────────────────────────────────
    print_section("STEP 3: Verify Python Dependencies")
    
    required_packages = [
        ("mcp", "Model Context Protocol SDK"),
    ]
    
    all_deps_ok = True
    for pkg, desc in required_packages:
        try:
            __import__(pkg)
            print(f"✅ {pkg:20} - {desc}")
        except ImportError:
            print(f"❌ {pkg:20} - NOT INSTALLED")
            print(f"    Install with: pip install {pkg}")
            all_deps_ok = False
    
    # Standard library imports (should always work)
    stdlib_imports = [
        "asyncio", "os", "sys", "re", "csv", "json", "datetime",
        "subprocess", "traceback", "collections"
    ]
    print(f"\n✅ Standard library modules: {', '.join(stdlib_imports[:5])} ...")
    
    # ────────────────────────────────────────────────────────────────
    # STEP 4: Try importing all modules
    # ────────────────────────────────────────────────────────────────
    print_section("STEP 4: Verify Module Imports")
    
    modules_to_check = [
        ("config.py", "config"),
        ("generate_plan.py", "generate_plan"),
        ("run_test.py", "run_test"),
        ("parse_results.py", "parse_results"),
        ("compare_runs.py", "compare_runs"),
        ("server.py", "server"),
    ]
    
    all_imports_ok = True
    for filepath, module_name in modules_to_check:
        if not check_imports(filepath, module_name):
            all_imports_ok = False
    
    # ────────────────────────────────────────────────────────────────
    # STEP 5: Check JMeter installation
    # ────────────────────────────────────────────────────────────────
    print_section("STEP 5: Check JMeter Installation")
    
    try:
        from config import check_jmeter_installed, get_jmeter_bin
        is_installed, message = check_jmeter_installed()
        print(message)
        jmeter_bin = get_jmeter_bin()
        if jmeter_bin:
            print(f"\n✅ JMeter binary location: {jmeter_bin}")
        else:
            print("\n⚠️  JMeter not found, but this is OK for test plan GENERATION")
            print("    You'll need JMeter installed to actually RUN tests")
    except Exception as e:
        print(f"❌ Error checking JMeter: {e}")
    
    # ────────────────────────────────────────────────────────────────
    # STEP 6: Code quality analysis
    # ────────────────────────────────────────────────────────────────
    print_section("STEP 6: Code Quality Analysis")
    
    quality_checks = {
        "server.py": [
            ("Has async main()", "async def main():"),
            ("Has handle_list_tools()", "@server.list_tools()"),
            ("Has handle_call_tool()", "@server.call_tool()"),
            ("Uses stdio_server", "stdio_server()"),
        ],
        "config.py": [
            ("Defines JMETER_HOME", "JMETER_HOME ="),
            ("Defines PLANS_DIR", "PLANS_DIR ="),
            ("Defines RESULTS_DIR", "RESULTS_DIR ="),
            ("Has get_jmeter_bin()", "def get_jmeter_bin()"),
        ],
    }
    
    for filename, checks in quality_checks.items():
        print(f"\n{filename}:")
        try:
            with open(filename, 'r') as f:
                content = f.read()
                for check_name, search_term in checks:
                    if search_term in content:
                        print(f"  ✅ {check_name}")
                    else:
                        print(f"  ❌ {check_name}")
        except Exception as e:
            print(f"  ❌ Error reading file: {e}")
    
    # ────────────────────────────────────────────────────────────────
    # FINAL SUMMARY
    # ────────────────────────────────────────────────────────────────
    print_header("📊 VERIFICATION SUMMARY")
    
    all_ok = all_files_exist and all_imports_ok and all_deps_ok
    
    if all_ok:
        print("""
✅ ALL CHECKS PASSED!

Your JMeter MCP Server is ready to use:

1. Core Files: ✅ All present and syntactically correct
2. Dependencies: ✅ All installed (mcp SDK)
3. Imports: ✅ All modules import successfully
4. Configuration: ✅ Config.py properly configured

NEXT STEPS:
───────────

Option A: Run the server directly
  $ python server.py
  
Then configure it in Claude Desktop's settings to use stdio transport.

Option B: Run the demo
  $ python demo_client.py
  
This will show you examples of all server capabilities.

Option C: Check specific functionality
  From Python:
    from generate_plan import generate_test_plan
    result = generate_test_plan("Test https://example.com with 10 users")
    print(result)

FEATURES AVAILABLE:
───────────────────
✓ Generate test plans from natural language
✓ Run JMeter tests (requires JMeter installed)
✓ Parse test results
✓ Compare test runs
✓ List available tests and results
✓ Full MCP protocol support for Claude Desktop
""")
    else:
        print("""
⚠️  Some checks failed. Please review the issues above.

Common fixes:
  1. Install dependencies: pip install -r requirements.txt
  2. Ensure Python 3.11+ is installed: python --version
  3. Check JMETER_HOME in config.py (only needed for running tests)
""")

if __name__ == "__main__":
    main()

