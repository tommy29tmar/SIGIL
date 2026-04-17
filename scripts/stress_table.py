#!/usr/bin/env python3
"""Aggregate stress bench table: verbose vs Caveman vs Flint on long-context tasks.

Reads evals/runs/stress/opus47_stress_{verbose,caveman,flintnew}_r*.jsonl.
Reports output tokens, cache-adjusted effective tokens, latency, and
must_include coverage. Deltas computed vs verbose Claude baseline.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import mean, stdev

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from flint.eval_common import cell_run_files  # noqa: E402

OUT = ROOT / "evals" / "runs" / "stress"
TASKS = ROOT / "evals" / "tasks_stress_coding.jsonl"

CELLS = [
    ("verbose Claude",     "stress_verbose"),
    ("Caveman (primitive)", "stress_caveman"),
    ("Flint",              "stress_flintnew"),
]


def task_index() -> dict:
    return {str(json.loads(l)["id"]): json.loads(l)
            for l in TASKS.read_text().splitlines() if l.strip()}


def score_run(path: Path, tasks: dict) -> dict:
    rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    mi, out, eff, lat = [], [], [], []
    for r in rows:
        t = tasks[str(r["task_id"])]
        lo = (r.get("content") or "").lower()
        mi.append(sum(1 for x in t["must_include"] if str(x).lower() in lo) / len(t["must_include"]))
        u = r.get("usage") or {}
        i = u.get("input_tokens") or 0
        o = u.get("output_tokens") or 0
        c = u.get("cached_tokens") or 0
        out.append(o)
        eff.append(max(0, i - c) + c * 0.1 + o)
        lat.append((r.get("elapsed_ms") or 0) / 1000)
    return {
        "must": mean(mi) * 100 if mi else 0.0,
        "out": mean(out) if out else 0.0,
        "eff": mean(eff) if eff else 0.0,
        "lat": mean(lat) if lat else 0.0,
    }


def fmt(m: float, s: float, unit: str = "") -> str:
    return f"{m:.0f}{unit}±{s:.0f}" if s > 0 else f"{m:.0f}{unit}"


def main() -> int:
    tasks = task_index()
    header = (f"{'variant':<22} {'n':>2} {'output':>9} {'eff_total':>11} "
              f"{'latency':>10} {'must_inc':>10} {'vs verbose out':>16} "
              f"{'vs verbose lat':>16}")
    print(header)
    baseline: dict | None = None
    for label, cell in CELLS:
        paths = cell_run_files(OUT, cell)
        if not paths:
            print(f"{label:<22} MISSING ({cell})")
            continue
        scores = [score_run(p, tasks) for p in paths]
        n = len(scores)
        agg = {k: (mean(s[k] for s in scores),
                   stdev(s[k] for s in scores) if n > 1 else 0.0)
               for k in ("must", "out", "eff", "lat")}
        if baseline is None:
            baseline = agg
            dout = dlat = "—"
        else:
            dout = f"{(agg['out'][0] - baseline['out'][0]) / baseline['out'][0] * 100:+.1f}%"
            dlat = f"{(agg['lat'][0] - baseline['lat'][0]) / baseline['lat'][0] * 100:+.1f}%"
        print(
            f"{label:<22} {n:>2} "
            f"{fmt(agg['out'][0], agg['out'][1]):>9} "
            f"{fmt(agg['eff'][0], agg['eff'][1]):>11} "
            f"{fmt(agg['lat'][0], agg['lat'][1], 's'):>10} "
            f"{fmt(agg['must'][0], agg['must'][1], '%'):>10} "
            f"{dout:>16} {dlat:>16}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
