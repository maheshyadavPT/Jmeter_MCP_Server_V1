"""
parse_results.py - Enhanced JMeter Results Parser
===================================================
IMPROVEMENTS over v1:
  • Failure analysis section — shows top error messages and response codes
  • Slowest requests listing — top 5 slowest individual samples
  • Connect time vs latency breakdown
  • Standard deviation of response times
  • Clearer grade thresholds with context
"""

import os
import csv
import math
from collections import defaultdict, Counter
from config import RESULTS_DIR


def parse_results(results_file: str) -> str:
    jtl_path = _resolve_results_path(results_file)
    if not os.path.exists(jtl_path):
        return (
            f"❌ Results file not found: '{results_file}'\n"
            f"   Searched: {jtl_path}\n"
            f"   Use list_results() to see available files."
        )

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

    # ── Overall stats ─────────────────────────────────────────────────
    total  = len(rows)
    passed = sum(1 for r in rows if r.get("success", "").lower() == "true")
    failed = total - passed
    error_pct = (failed / total * 100) if total > 0 else 0

    times = sorted(int(r["elapsed"]) for r in rows if r.get("elapsed"))

    def pct(data, p):
        if not data: return 0
        return data[min(int(len(data) * p / 100), len(data) - 1)]

    t_min = min(times) if times else 0
    t_max = max(times) if times else 0
    t_avg = int(sum(times) / len(times)) if times else 0
    t_90  = pct(times, 90)
    t_95  = pct(times, 95)
    t_std = int(math.sqrt(sum((t - t_avg) ** 2 for t in times) / len(times))) if times else 0

    # Connect time and latency averages
    latencies = [int(r["Latency"]) for r in rows if r.get("Latency") and r["Latency"].isdigit()]
    connects  = [int(r["Connect"]) for r in rows if r.get("Connect") and r["Connect"].isdigit()]
    avg_latency = int(sum(latencies) / len(latencies)) if latencies else 0
    avg_connect = int(sum(connects) / len(connects)) if connects else 0

    # Throughput
    try:
        ts_vals = [int(r["timeStamp"]) for r in rows if r.get("timeStamp")]
        duration_s = (max(ts_vals) - min(ts_vals)) / 1000 if len(ts_vals) > 1 else 1
        throughput = round(total / duration_s, 2)
    except Exception:
        duration_s = 1
        throughput = 0

    # Bandwidth
    try:
        total_bytes = sum(int(r.get("bytes", 0)) for r in rows)
        bandwidth = round((total_bytes / 1024) / max(duration_s, 1), 2)
    except Exception:
        bandwidth = 0

    # ── Per-label breakdown ───────────────────────────────────────────
    label_data = defaultdict(list)
    for row in rows:
        label_data[row.get("label", "Unknown")].append(row)

    # ── Failure analysis ─────────────────────────────────────────────
    failed_rows = [r for r in rows if r.get("success", "").lower() != "true"]
    error_codes = Counter(r.get("responseCode", "?") for r in failed_rows)
    error_msgs  = Counter(r.get("failureMessage", r.get("responseMessage", "?"))
                          for r in failed_rows)

    # ── Top 5 slowest requests ────────────────────────────────────────
    slowest = sorted(rows, key=lambda r: int(r.get("elapsed", 0)), reverse=True)[:5]

    # ── Build report ──────────────────────────────────────────────────
    lines = [
        "📊 JMeter Results Summary",
        "─" * 52,
        f"📄 File        : {os.path.basename(jtl_path)}",
        "",
        "OVERALL",
        f"  Total Requests : {total:,}",
        f"  Passed         : {passed:,}  ✅",
        f"  Failed         : {failed:,}  {'❌' if failed else '✅'}",
        f"  Error Rate     : {error_pct:.2f}%",
        "",
        "RESPONSE TIMES (ms)",
        f"  Min            : {t_min:,}",
        f"  Average        : {t_avg:,}",
        f"  Std Deviation  : ±{t_std:,}  {'(high variance ⚠)' if t_std > t_avg * 0.5 else ''}",
        f"  90th Pct       : {t_90:,}",
        f"  95th Pct       : {t_95:,}",
        f"  Max            : {t_max:,}",
        "",
        "NETWORK BREAKDOWN (ms)",
        f"  Avg Connect    : {avg_connect:,}",
        f"  Avg Latency    : {avg_latency:,}  (time to first byte)",
        f"  Avg Processing : {max(0, t_avg - avg_latency):,}  (server processing)",
        "",
        "THROUGHPUT",
        f"  Requests/sec   : {throughput}",
        f"  Bandwidth      : {bandwidth} KB/s",
        f"  Test Duration  : {round(duration_s, 1)}s",
    ]

    # Failure analysis section
    if failed_rows:
        lines += ["", "─" * 52, "FAILURE ANALYSIS ❌"]
        lines.append(f"  Total failures : {failed}")
        if error_codes:
            lines.append("  Response codes :")
            for code, count in error_codes.most_common(5):
                lines.append(f"    {code:>6} → {count} requests")
        if error_msgs:
            lines.append("  Failure reasons:")
            for msg, count in error_msgs.most_common(3):
                short_msg = msg[:80] + "…" if len(msg) > 80 else msg
                lines.append(f"    [{count}x] {short_msg}")

    # Slowest requests
    if slowest:
        lines += ["", "─" * 52, "TOP 5 SLOWEST REQUESTS"]
        for i, r in enumerate(slowest, 1):
            label = r.get("label", "?")[:35]
            elapsed = int(r.get("elapsed", 0))
            code = r.get("responseCode", "?")
            ok = "✅" if r.get("success", "").lower() == "true" else "❌"
            lines.append(f"  {i}. {ok} {elapsed:>6}ms  [{code}]  {label}")

    # Per-label breakdown
    lines += ["", "─" * 52, "PER-SAMPLER BREAKDOWN"]
    for label, label_rows in sorted(label_data.items()):
        lbl_total  = len(label_rows)
        lbl_passed = sum(1 for r in label_rows if r.get("success", "").lower() == "true")
        lbl_failed = lbl_total - lbl_passed
        lbl_times  = sorted(int(r["elapsed"]) for r in label_rows if r.get("elapsed"))
        lbl_avg    = int(sum(lbl_times) / len(lbl_times)) if lbl_times else 0
        lbl_90     = pct(lbl_times, 90)
        lbl_err    = round(lbl_failed / lbl_total * 100, 1) if lbl_total else 0

        lines += [
            "",
            f"  [{label}]",
            f"    Requests : {lbl_total:,}  |  Errors: {lbl_failed} ({lbl_err}%)",
            f"    Avg RT   : {lbl_avg} ms  |  P90: {lbl_90} ms",
        ]

        # Show top error for this label
        lbl_failed_rows = [r for r in label_rows if r.get("success", "").lower() != "true"]
        if lbl_failed_rows:
            top_err = Counter(
                r.get("responseCode", "?") for r in lbl_failed_rows
            ).most_common(1)
            if top_err:
                lines.append(f"    Top Error: HTTP {top_err[0][0]} ({top_err[0][1]}x)")

    # Grade
    grade = _performance_grade(error_pct, t_avg, t_90, t_std)
    lines += ["", "─" * 52, f"PERFORMANCE GRADE: {grade}"]

    return "\n".join(lines)


def _resolve_results_path(results_file: str) -> str:
    if os.path.isabs(results_file):
        return results_file
    if os.path.exists(results_file):
        return os.path.abspath(results_file)
    return os.path.join(RESULTS_DIR, results_file)


def _performance_grade(error_pct, avg_ms, p90_ms, std_ms) -> str:
    high_variance = std_ms > avg_ms * 0.5
    if error_pct == 0 and avg_ms < 300 and p90_ms < 600:
        return "🟢 A+ — Excellent (fast, zero errors)"
    elif error_pct < 1 and avg_ms < 500 and p90_ms < 1000:
        return "🟢 A — Good" + (" — high variance detected ⚠" if high_variance else "")
    elif error_pct < 2 and avg_ms < 1000 and p90_ms < 2000:
        return "🟡 B — Acceptable" + (" — inconsistent response times ⚠" if high_variance else "")
    elif error_pct < 5 and avg_ms < 2000:
        return "🟠 C — Needs Improvement — investigate slow P90"
    else:
        return "🔴 D — Poor — errors and/or high latency require investigation"
