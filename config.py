"""
config.py - Central configuration for JMeter MCP Server
=========================================================
Edit the constants in this file to match your local environment.
You only need to change JMETER_HOME (and optionally the directory paths).
"""

import os
import sys

# ─────────────────────────────────────────────────────────────────────
# ① JMETER_HOME
#    The root folder of your Apache JMeter installation.
#    Download JMeter: https://jmeter.apache.org/download_jmeter.cgi
#
#    Examples:
#      Windows : r"C:\apache-jmeter-5.6.3"
#      macOS   : "/usr/local/opt/jmeter" or "/opt/homebrew/opt/jmeter"
#      Linux   : "/opt/apache-jmeter-5.6.3"
#
#    You can also set this as an ENVIRONMENT VARIABLE instead of
#    editing this file:
#      Windows PowerShell: $env:JMETER_HOME = "C:\apache-jmeter-5.6.3"
#      Bash/zsh:           export JMETER_HOME=/opt/apache-jmeter-5.6.3
# ─────────────────────────────────────────────────────────────────────
JMETER_HOME = os.environ.get(
    "JMETER_HOME",
    r"D:\Program Files\Jmeter\apache-jmeter-5.6.3"   # ← Updated to your JMeter location
)

# ─────────────────────────────────────────────────────────────────────
# ② Directory paths (relative to this file)
#    These are created automatically if they don't exist.
# ─────────────────────────────────────────────────────────────────────
_BASE_DIR   = os.path.dirname(os.path.abspath(__file__))   # folder of config.py

PLANS_DIR   = os.path.join(_BASE_DIR, "test_plans")   # .jmx files stored here
RESULTS_DIR = os.path.join(_BASE_DIR, "results")      # .jtl files stored here


# ─────────────────────────────────────────────────────────────────────
# ③ Auto-detect the JMeter binary path
#    Returns the full path to jmeter.bat (Windows) or jmeter (Unix).
#    Returns None if the binary cannot be found.
# ─────────────────────────────────────────────────────────────────────
def get_jmeter_bin() -> str | None:
    """
    Locate the JMeter executable.

    Search order:
    1. Use JMETER_HOME environment variable (if set)
    2. Use JMETER_HOME from this file (if configured)
    3. Check common installation paths
    
    Returns:
        Path to jmeter executable, or None if not found.
    """
    
    # Try JMETER_HOME first
    if JMETER_HOME and os.path.exists(JMETER_HOME):
        if sys.platform == "win32":
            jmeter_bin = os.path.join(JMETER_HOME, "bin", "jmeter.bat")
        else:
            jmeter_bin = os.path.join(JMETER_HOME, "bin", "jmeter")
        
        if os.path.exists(jmeter_bin):
            return jmeter_bin
    
    # If not found, return None (will be handled gracefully)
    return None


def check_jmeter_installed() -> tuple[bool, str]:
    """
    Check if JMeter is installed and return status + message.
    
    Returns:
        (is_installed, message)
    """
    jmeter_bin = get_jmeter_bin()
    
    if jmeter_bin:
        return True, f"✅ JMeter found at: {jmeter_bin}"
    else:
        return False, (
            "⚠️  JMeter is not installed or not found at configured path.\n"
            f"   Expected at: {JMETER_HOME}\n"
            "   \n"
            "   INSTALLATION INSTRUCTIONS:\n"
            "   1. Download JMeter: https://jmeter.apache.org/download_jmeter.cgi\n"
            "   2. Extract to: C:\\apache-jmeter-5.6.3 (or your preferred location)\n"
            "   3. Update JMETER_HOME in this file (config.py)\n"
            "   4. OR set environment variable: $env:JMETER_HOME = 'your_path'\n"
            "   \n"
            "   NOTE: Test plan GENERATION will work without JMeter.\n"
            "   Only test EXECUTION requires JMeter to be installed."
        )


# ─────────────────────────────────────────────────────────────────────
# ④ Create directories if they don't exist
# ─────────────────────────────────────────────────────────────────────
def ensure_directories():
    """Create necessary directories if they don't exist."""
    for directory in [PLANS_DIR, RESULTS_DIR]:
        os.makedirs(directory, exist_ok=True)


# Auto-create directories when config is imported
ensure_directories()


# ─────────────────────────────────────────────────────────────────────
# ⑤ Summary information (for debugging)
# ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 70)
    print("JMeter MCP Server Configuration")
    print("=" * 70)
    print()
    print(f"Base Directory:  {_BASE_DIR}")
    print(f"Test Plans Dir:  {PLANS_DIR}")
    print(f"Results Dir:     {RESULTS_DIR}")
    print(f"JMETER_HOME:     {JMETER_HOME}")
    print()
    
    is_installed, msg = check_jmeter_installed()
    print(msg)
    print()
    print("=" * 70)
