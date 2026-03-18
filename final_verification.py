#!/usr/bin/env python3
"""
Final Code Verification and Issue Report
"""

import os
import sys

def check_file_exists(path):
    """Check if file exists."""
    return os.path.exists(path)

def check_imports():
    """Check if all critical imports work."""
    try:
        # Test config
        from config import PLANS_DIR, RESULTS_DIR, get_jmeter_bin, ensure_directories
        
        # Test all tool modules
        from generate_plan import generate_test_plan
        from parse_results import parse_results
        from run_test import run_test, list_test_plans, list_results
        from compare_runs import compare_runs
        
        # Test server
        import server
        
        return True, "All imports successful"
    except Exception as e:
        return False, f"Import failed: {e}"

def check_directories():
    """Check if required directories exist or can be created."""
    try:
        from config import PLANS_DIR, RESULTS_DIR, ensure_directories
        ensure_directories()
        
        dirs_ok = os.path.exists(PLANS_DIR) and os.path.exists(RESULTS_DIR)
        return dirs_ok, f"PLANS_DIR={PLANS_DIR}, RESULTS_DIR={RESULTS_DIR}"
    except Exception as e:
        return False, f"Directory check failed: {e}"

def check_generate_plan():
    """Check generate_plan imports config correctly."""
    try:
        # Read the file and check for the import
        with open("generate_plan.py", "r") as f:
            content = f.read()
            
        # Should have: from config import PLANS_DIR
        if "from config import PLANS_DIR" in content:
            # Should NOT have: PLANS_DIR = os.path.join(..., "..", "test_plans")
            if 'PLANS_DIR = os.path.join(os.path.dirname(__file__), ".."' not in content:
                return True, "✅ generate_plan.py correctly imports PLANS_DIR from config"
            else:
                return False, "❌ generate_plan.py still has old PLANS_DIR definition"
        else:
            return False, "❌ generate_plan.py missing 'from config import PLANS_DIR'"
    except Exception as e:
        return False, f"File check failed: {e}"

def check_consistency():
    """Check all modules use consistent imports."""
    modules = {
        'generate_plan.py': 'from config import PLANS_DIR',
        'run_test.py': 'from config import',
        'parse_results.py': 'from config import',
        'compare_runs.py': 'from config import',
    }
    
    errors = []
    for module, expected_import in modules.items():
        try:
            with open(module, "r") as f:
                if expected_import not in f.read():
                    errors.append(f"{module}: missing '{expected_import}'")
        except Exception as e:
            errors.append(f"{module}: error reading - {e}")
    
    if errors:
        return False, "; ".join(errors)
    return True, "All modules consistently import from config"

def main():
    print("=" * 70)
    print("JMeter MCP Server - FINAL CODE VERIFICATION REPORT")
    print("=" * 70)
    print()
    
    checks = [
        ("File Existence", lambda: (check_file_exists("server.py"), "server.py exists")),
        ("Imports", check_imports),
        ("Directories", check_directories),
        ("generate_plan.py Fix", check_generate_plan),
        ("Import Consistency", check_consistency),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            passed, message = check_func()
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status}: {name}")
            print(f"         {message}")
            results.append(passed)
        except Exception as e:
            print(f"❌ ERROR: {name}")
            print(f"          {e}")
            results.append(False)
        print()
    
    print("=" * 70)
    print(f"SUMMARY: {sum(results)}/{len(results)} checks passed")
    print("=" * 70)
    print()
    
    if all(results):
        print("✅ ALL CHECKS PASSED!")
        print()
        print("The code is ready to use. To start the server:")
        print("  1. Open PowerShell")
        print("  2. cd D:\\Jmeter_MCP_NEW")
        print("  3. python server.py")
        print()
        print("Then in Claude Desktop:")
        print("  1. Create a NEW chat")
        print("  2. Ask to generate a test plan")
        return 0
    else:
        print("❌ SOME CHECKS FAILED")
        print()
        print("Please review the failures above and fix any issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

