"""
tools/parse_results.py
======================
Reads a JMeter .jtl (CSV) results file and produces a human-readable
performance summary with key metrics.

JTL Format
──────────
JMeter saves results as CSV with these columns (when fieldNames=true):
  timeStamp, elapsed, label, responseCode, responseMessage,
  threadName, dataType, success, failureMessage, bytes, sentBytes,
  grpThreads, allThreads, URL, Latency, IdleTime, Connect

Key columns we use:
  elapsed      → response time in milliseconds
  success      → "true" / "false"
  label        → sampler name (e.g. "GET /api/users")
  responseCode → HTTP status code (200, 404, 500 …)
  bytes        → response size
  Latency      → time-to-first-byte in ms
"""

import os
import csv
from collections import defaultdict
from config import RESULTS_DIR


def parse_results(results_file: str) -> str:
    """
    Parse a .jtl file and return a performance summary string.

    Parameters
    ----------
    results_file : str  path or filename of the .jtl file

    Returns
    -------
    str  multi-section report with overall + per-label stats
    """

    # ── Resolve path ──────────────────────────────────────────────────
    jtl_path = _resolve_results_path(results_file)
    if not os.path.exists(jtl_path):
        return (
            f"❌ Results file not found: '{results_file}'\n"
            f"   Searched: {jtl_path}\n"
            f"   Use list_results() to see available files."
        )

    # ── Read the CSV ──────────────────────────────────────────────────
    rows = []
    try:
        with open(jtl_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    except Exception as e:
        return f"❌ Could not read {jtl_path}: {e}"

    if not rows:
        return f"❌ Results file is empty: {jtl_path}"

    # ── Aggregate overall statistics ──────────────────────────────────
    total     = len(rows)
    passed    = sum(1 for r in rows if r.get("success", "").lower() == "true")
    failed    = total - passed
    error_pct = (failed / total * 100) if total > 0 else 0

    # Response times (elapsed field, in ms)
    times = []
    for r in rows:
        try:
            times.append(int(r["elapsed"]))
        except (KeyError, ValueError):
            pass

    times.sort()

    def percentile(data, pct):
        """Return the pct-th percentile from a sorted list."""
        if not data:
            return 0
        idx = int(len(data) * pct / 100)
        idx = min(idx, len(data) - 1)
        return data[idx]

    t_min   = min(times) if times else 0
    t_max   = max(times) if times else 0
    t_avg   = int(sum(times) / len(times)) if times else 0
    t_90    = percentile(times, 90)   # 90th percentile
    t_95    = percentile(times, 95)   # 95th percentile

    # Throughput = total requests / test duration in seconds
    # timeStamp is epoch milliseconds
    try:
        ts_values = [int(r["timeStamp"]) for r in rows if r.get("timeStamp")]
        if ts_values:
            duration_ms = max(ts_values) - min(ts_values)
            duration_s  = duration_ms / 1000 if duration_ms > 0 else 1
            throughput  = round(total / duration_s, 2)
        else:
            throughput = 0
    except Exception:
        throughput = 0

    # Bandwidth (average KB/s)
    try:
        total_bytes = sum(int(r.get("bytes", 0)) for r in rows)
        bandwidth_kbs = round((total_bytes / 1024) / max(duration_s, 1), 2)
    except Exception:
        bandwidth_kbs = 0

    # ── Per-label breakdown ───────────────────────────────────────────
    # Group rows by 'label' (sampler name)
    label_data = defaultdict(list)
    for row in rows:
        label = row.get("label", "Unknown")
        label_data[label].append(row)

    # ── Build the report string ───────────────────────────────────────
    lines = [
        f"📊 JMeter Results Summary",
        f"{'─'*50}",
        f"📄 File       : {os.path.basename(jtl_path)}",
        f"",
        f"OVERALL",
        f"  Total Requests  : {total:,}",
        f"  Passed          : {passed:,}  ✅",
        f"  Failed          : {failed:,}  {'❌' if failed else '✅'}",
        f"  Error Rate      : {error_pct:.2f}%",
        f"",
        f"RESPONSE TIMES (ms)",
        f"  Min             : {t_min:,} ms",
        f"  Average         : {t_avg:,} ms",
        f"  90th Percentile : {t_90:,} ms",
        f"  95th Percentile : {t_95:,} ms",
        f"  Max             : {t_max:,} ms",
        f"",
        f"THROUGHPUT",
        f"  Requests/sec    : {throughput}",
        f"  Bandwidth       : {bandwidth_kbs} KB/s",
        f"",
        f"{'─'*50}",
        f"PER-SAMPLER BREAKDOWN",
    ]

    for label, label_rows in sorted(label_data.items()):
        lbl_total  = len(label_rows)
        lbl_passed = sum(1 for r in label_rows if r.get("success", "").lower() == "true")
        lbl_failed = lbl_total - lbl_passed
        lbl_times  = sorted(int(r["elapsed"]) for r in label_rows if r.get("elapsed"))
        lbl_avg    = int(sum(lbl_times) / len(lbl_times)) if lbl_times else 0
        lbl_90     = percentile(lbl_times, 90)
        lbl_err    = round(lbl_failed / lbl_total * 100, 1) if lbl_total else 0

        lines += [
            f"",
            f"  [{label}]",
            f"    Requests : {lbl_total:,}  |  Errors: {lbl_failed} ({lbl_err}%)",
            f"    Avg RT   : {lbl_avg} ms  |  P90: {lbl_90} ms",
        ]

    # ── Performance grade ─────────────────────────────────────────────
    grade = _performance_grade(error_pct, t_avg, t_90)
    lines += [
        f"",
        f"{'─'*50}",
        f"PERFORMANCE GRADE: {grade}",
    ]

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────
# PRIVATE HELPERS
# ─────────────────────────────────────────────────────────────────────

def _resolve_results_path(results_file: str) -> str:
    if os.path.isabs(results_file):
        return results_file
    if os.path.exists(results_file):
        return os.path.abspath(results_file)
    return os.path.join(RESULTS_DIR, results_file)


def _performance_grade(error_pct: float, avg_ms: int, p90_ms: int) -> str:
    """
    Simple grading rubric:
      A = error < 1%  AND avg < 500ms  AND p90 < 1000ms
      B = error < 2%  AND avg < 1000ms AND p90 < 2000ms
      C = error < 5%  AND avg < 2000ms
      D = anything worse
    """
    if error_pct < 1 and avg_ms < 500 and p90_ms < 1000:
        return "🟢 A — Excellent"
    elif error_pct < 2 and avg_ms < 1000 and p90_ms < 2000:
        return "🟡 B — Good"
    elif error_pct < 5 and avg_ms < 2000:
        return "🟠 C — Needs Improvement"
    else:
        return "🔴 D — Poor — Investigate errors and response times"
