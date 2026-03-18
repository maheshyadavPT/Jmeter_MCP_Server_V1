"""
tools/compare_runs.py
=====================
Compare two JMeter .jtl result files (baseline vs new run) and
highlight improvements or regressions in key performance metrics.

Use case: You ran a performance test, made a code change, ran again.
  compare_runs("run1.jtl", "run2.jtl")
  → Did response times improve? Did errors go up? Did throughput drop?
"""

import os
import csv
from collections import defaultdict
from config import RESULTS_DIR


def compare_runs(baseline_file: str, new_file: str) -> str:
    """
    Side-by-side comparison of baseline vs new .jtl files.

    Parameters
    ----------
    baseline_file : str  the OLDER / reference run
    new_file      : str  the NEWER / test run

    Returns
    -------
    str  comparison report with delta indicators (▲ better / ▼ worse)
    """

    # ── Load both files ───────────────────────────────────────────────
    base_path = _resolve(baseline_file)
    new_path  = _resolve(new_file)

    missing = []
    if not os.path.exists(base_path):
        missing.append(f"Baseline: {base_path}")
    if not os.path.exists(new_path):
        missing.append(f"New run : {new_path}")
    if missing:
        return "❌ File(s) not found:\n  " + "\n  ".join(missing)

    base_rows = _load_jtl(base_path)
    new_rows  = _load_jtl(new_path)

    if not base_rows:
        return f"❌ Baseline file is empty: {base_path}"
    if not new_rows:
        return f"❌ New file is empty: {new_path}"

    # ── Compute stats for each file ───────────────────────────────────
    base_stats = _compute_stats(base_rows)
    new_stats  = _compute_stats(new_rows)

    # ── Build comparison report ───────────────────────────────────────
    lines = [
        "📊 JMeter Run Comparison",
        "─" * 60,
        f"  Baseline : {os.path.basename(base_path)}  ({len(base_rows):,} samples)",
        f"  New Run  : {os.path.basename(new_path)}  ({len(new_rows):,} samples)",
        "",
        f"{'Metric':<28} {'Baseline':>12} {'New Run':>12} {'Change':>12}",
        "─" * 60,
    ]

    def row(label, key, unit="ms", lower_is_better=True):
        """Format one comparison row with delta indicator."""
        b = base_stats.get(key, 0)
        n = new_stats.get(key, 0)
        delta = n - b
        pct   = (delta / b * 100) if b != 0 else 0

        # Determine if change is good or bad
        if abs(delta) < 0.01:
            arrow = "  ─"          # no change
            colour = ""
        elif (delta < 0) == lower_is_better:
            arrow = "▲ improved"   # good direction
        else:
            arrow = "▼ regressed"  # bad direction

        return (
            f"  {label:<26} {b:>10.1f}{unit}  {n:>10.1f}{unit}  "
            f"{delta:>+8.1f}{unit} {arrow} ({pct:+.1f}%)"
        )

    lines += [
        row("Avg Response Time",      "avg_ms"),
        row("90th Percentile",        "p90_ms"),
        row("95th Percentile",        "p95_ms"),
        row("Max Response Time",      "max_ms"),
        row("Error Rate",             "error_pct", unit="%"),
        row("Throughput",             "throughput", unit=" rps", lower_is_better=False),
    ]

    # ── Per-label comparison ──────────────────────────────────────────
    all_labels = sorted(
        set(base_stats["labels"].keys()) | set(new_stats["labels"].keys())
    )

    if all_labels:
        lines += [
            "",
            "─" * 60,
            "PER-SAMPLER COMPARISON",
            f"  {'Sampler':<30} {'Base Avg':>10} {'New Avg':>10} {'Δ':>8}",
            "─" * 60,
        ]
        for label in all_labels:
            b_avg = base_stats["labels"].get(label, {}).get("avg_ms", 0)
            n_avg = new_stats["labels"].get(label, {}).get("avg_ms", 0)
            delta = n_avg - b_avg
            arrow = "▲" if delta < 0 else ("▼" if delta > 0 else "─")
            lines.append(
                f"  {label[:30]:<30} {b_avg:>8.0f}ms  {n_avg:>8.0f}ms  "
                f"{delta:>+6.0f}ms {arrow}"
            )

    # ── Verdict ───────────────────────────────────────────────────────
    lines += ["", "─" * 60, _verdict(base_stats, new_stats)]

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────
# PRIVATE HELPERS
# ─────────────────────────────────────────────────────────────────────

def _resolve(path: str) -> str:
    if os.path.isabs(path):
        return path
    if os.path.exists(path):
        return os.path.abspath(path)
    return os.path.join(RESULTS_DIR, path)


def _load_jtl(path: str) -> list:
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def _compute_stats(rows: list) -> dict:
    """Compute aggregate stats dict from a list of JTL row dicts."""
    total  = len(rows)
    failed = sum(1 for r in rows if r.get("success", "").lower() != "true")

    times = sorted(int(r["elapsed"]) for r in rows if r.get("elapsed"))

    def pct(data, p):
        if not data:
            return 0
        return data[min(int(len(data) * p / 100), len(data) - 1)]

    avg_ms = int(sum(times) / len(times)) if times else 0

    # Throughput
    try:
        ts = [int(r["timeStamp"]) for r in rows if r.get("timeStamp")]
        dur_s = (max(ts) - min(ts)) / 1000 if len(ts) > 1 else 1
        throughput = round(total / dur_s, 2)
    except Exception:
        throughput = 0

    # Per-label averages
    label_map = defaultdict(list)
    for r in rows:
        try:
            label_map[r.get("label", "?")].append(int(r["elapsed"]))
        except (ValueError, KeyError):
            pass

    label_stats = {}
    for label, lt in label_map.items():
        label_stats[label] = {
            "avg_ms": int(sum(lt) / len(lt)) if lt else 0,
            "p90_ms": pct(sorted(lt), 90),
        }

    return {
        "total":     total,
        "failed":    failed,
        "error_pct": round(failed / total * 100, 2) if total else 0,
        "avg_ms":    avg_ms,
        "p90_ms":    pct(times, 90),
        "p95_ms":    pct(times, 95),
        "max_ms":    max(times) if times else 0,
        "throughput": throughput,
        "labels":    label_stats,
    }


def _verdict(base: dict, new: dict) -> str:
    """Overall pass/fail verdict based on key metric changes."""
    errors_worse     = new["error_pct"] > base["error_pct"] + 1
    response_worse   = new["avg_ms"]    > base["avg_ms"] * 1.2     # >20% slower
    throughput_worse = new["throughput"] < base["throughput"] * 0.8  # >20% lower

    if errors_worse or response_worse or throughput_worse:
        issues = []
        if errors_worse:     issues.append("error rate increased")
        if response_worse:   issues.append("avg response time degraded >20%")
        if throughput_worse: issues.append("throughput dropped >20%")
        return f"🔴 REGRESSION DETECTED: {', '.join(issues)}"
    elif (new["avg_ms"] < base["avg_ms"] * 0.9 and
          new["error_pct"] <= base["error_pct"]):
        return "🟢 IMPROVEMENT: Response time improved >10% with no increase in errors"
    else:
        return "🟡 NO SIGNIFICANT CHANGE: Performance is comparable to baseline"
