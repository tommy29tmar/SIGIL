#!/usr/bin/env python3
"""Print the 3-way Caveman bench table (verbose / primitive / sigil)."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evals" / "runs" / "caveman"
TASKS = ROOT / "evals" / "tasks_top_tier_holdout.jsonl"

VARIANTS = [
    ("default (verbose)",   "opus47_verbose.jsonl"),
    ("Caveman (primitive)", "opus47_primitive.jsonl"),
    ("SIGIL",               "opus47_sigil.jsonl"),
]


def score(path: Path, tasks: dict) -> dict | None:
    if not path.exists():
        return None
    rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    mi, tot, lat = [], [], []
    for r in rows:
        t = tasks[str(r["task_id"])]
        lo = r["content"].lower()
        mi.append(sum(1 for x in t["must_include"] if str(x).lower() in lo) / len(t["must_include"]))
        u = r["usage"]
        tot.append((u.get("input_tokens") or 0) + (u.get("output_tokens") or 0))
        lat.append(r.get("elapsed_ms") or 0)
    return {"must": mean(mi), "tot": mean(tot), "lat": mean(lat)}


def main() -> int:
    tasks = {str(json.loads(l)["id"]): json.loads(l) for l in TASKS.read_text().splitlines() if l.strip()}
    rows = [(label, score(OUT / f, tasks)) for label, f in VARIANTS]
    base = rows[0][1]
    print(f"{'variant':<22} {'tokens':>8} {'latency':>8} {'must_inc':>9} {'vs verbose tok':>16} {'vs verbose lat':>16}")
    for label, r in rows:
        if r is None:
            print(f"{label:<22} MISSING"); continue
        dt = f"{(r['tot']-base['tot'])/base['tot']*100:+.1f}%" if r is not base else "—"
        dl = f"{(r['lat']-base['lat'])/base['lat']*100:+.1f}%" if r is not base else "—"
        print(f"{label:<22} {r['tot']:>8.0f} {r['lat']/1000:>7.1f}s {r['must']*100:>8.1f}% {dt:>16} {dl:>16}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
