"""
tools/run_test.py
=================
Executes a JMeter .jmx test plan using the system JMeter installation
and saves results to a .jtl file.

Also provides helper functions:
  list_test_plans() → lists .jmx files in test_plans/
  list_results()    → lists .jtl files in results/
"""

import os
import subprocess
import datetime
from config import get_jmeter_bin, PLANS_DIR, RESULTS_DIR


def run_test(test_plan: str, results_file: str = None) -> str:
    """
    Run a JMeter test plan non-interactively (headless / CLI mode).

    JMeter CLI flags used:
      -n           → non-GUI (headless) mode
      -t <file>    → path to the .jmx test plan
      -l <file>    → path for the .jtl output results file
      -e           → generate HTML dashboard report after test
      -o <dir>     → directory for the HTML report

    Parameters
    ----------
    test_plan    : str  path or filename of the .jmx file
    results_file : str  optional path/name for the .jtl output

    Returns
    -------
    str  summary of execution (stdout + stderr) or error message
    """

    # ── Resolve the test plan path ────────────────────────────────────
    jmx_path = _resolve_plan_path(test_plan)
    if not os.path.exists(jmx_path):
        return (
            f"❌ Test plan not found: '{test_plan}'\n"
            f"   Searched: {jmx_path}\n"
            f"   Use list_test_plans() to see available plans."
        )

    # ── Resolve the results file path ─────────────────────────────────
    os.makedirs(RESULTS_DIR, exist_ok=True)
    if not results_file:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        plan_stem = os.path.splitext(os.path.basename(jmx_path))[0]
        results_file = f"{plan_stem}_{timestamp}.jtl"

    jtl_path = os.path.join(RESULTS_DIR, os.path.basename(results_file))

    # ── HTML report directory (alongside .jtl) ───────────────────────
    report_dir = jtl_path.replace(".jtl", "_report")

    # ── Locate JMeter binary ──────────────────────────────────────────
    jmeter_bin = get_jmeter_bin()
    if not jmeter_bin:
        return (
            "❌ JMeter binary not found!\n\n"
            "Fix: Set the JMETER_HOME environment variable, e.g.:\n"
            "  Windows PowerShell:\n"
            "    $env:JMETER_HOME = 'C:\\apache-jmeter-5.6.3'\n"
            "  Or edit config.py → JMETER_HOME constant."
        )

    # ── Build the command ─────────────────────────────────────────────
    # jmeter -n -t plan.jmx -l results.jtl -e -o report_dir
    cmd = [
        jmeter_bin,
        "-n",               # non-GUI mode
        "-t", jmx_path,     # test plan
        "-l", jtl_path,     # results file
        "-e",               # generate dashboard
        "-o", report_dir,   # dashboard output dir
    ]

    # ── Execute ───────────────────────────────────────────────────────
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,   # capture stdout + stderr
            text=True,             # decode bytes → str
            timeout=3600,          # 1-hour safety timeout
        )

        # Combine both streams for the return message
        output = proc.stdout + ("\n" + proc.stderr if proc.stderr else "")

        if proc.returncode == 0:
            return (
                f"✅ Test completed successfully!\n\n"
                f"📄 Results file : {jtl_path}\n"
                f"📊 HTML Report  : {report_dir}\n\n"
                f"▶ Parse results with: parse_results('{os.path.basename(jtl_path)}')\n\n"
                f"─── JMeter output ───\n{output}"
            )
        else:
            return (
                f"❌ JMeter exited with code {proc.returncode}\n\n"
                f"─── Output ───\n{output}"
            )

    except subprocess.TimeoutExpired:
        return "❌ Test timed out after 1 hour. Increase timeout in run_test.py if needed."

    except FileNotFoundError:
        return (
            f"❌ Could not launch JMeter.\n"
            f"   Binary path: {jmeter_bin}\n"
            f"   Make sure JMETER_HOME is set correctly."
        )


# ─────────────────────────────────────────────────────────────────────
def list_test_plans() -> str:
    """
    Return a formatted list of all .jmx files in the test_plans/ directory.
    """
    os.makedirs(PLANS_DIR, exist_ok=True)
    files = sorted(f for f in os.listdir(PLANS_DIR) if f.endswith(".jmx"))

    if not files:
        return (
            "📂 No test plans found in: " + PLANS_DIR + "\n"
            "   Use generate_test_plan() to create one."
        )

    lines = [f"📂 Test plans in {PLANS_DIR}:\n"]
    for i, f in enumerate(files, 1):
        full_path = os.path.join(PLANS_DIR, f)
        size_kb = os.path.getsize(full_path) / 1024
        lines.append(f"  {i:2d}. {f}  ({size_kb:.1f} KB)")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────
def list_results() -> str:
    """
    Return a formatted list of all .jtl files in the results/ directory.
    """
    os.makedirs(RESULTS_DIR, exist_ok=True)
    files = sorted(f for f in os.listdir(RESULTS_DIR) if f.endswith(".jtl"))

    if not files:
        return (
            "📂 No result files found in: " + RESULTS_DIR + "\n"
            "   Run a test first with run_test()."
        )

    lines = [f"📂 Result files in {RESULTS_DIR}:\n"]
    for i, f in enumerate(files, 1):
        full_path = os.path.join(RESULTS_DIR, f)
        size_kb = os.path.getsize(full_path) / 1024
        lines.append(f"  {i:2d}. {f}  ({size_kb:.1f} KB)")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────
# PRIVATE HELPER
# ─────────────────────────────────────────────────────────────────────
def _resolve_plan_path(test_plan: str) -> str:
    """
    Accept either a full absolute path OR just a filename.
    If just a filename, look inside PLANS_DIR.
    """
    if os.path.isabs(test_plan):
        return test_plan
    # Maybe user passed a relative path
    if os.path.exists(test_plan):
        return os.path.abspath(test_plan)
    # Assume it's a filename inside PLANS_DIR
    return os.path.join(PLANS_DIR, test_plan)
