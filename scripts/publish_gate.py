#!/usr/bin/env python3
"""Per-cell publish gate.

Enforces that a benchmark cell (one model × one variant × N tasks) is publishable:
- Every row has status != "max_tokens"
- Every expected task_id appears exactly once
- No task had an HTTP/network error

Exit 0 if clean. Exit 1 with a human-readable diagnostic otherwise.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def load_expected_task_ids(tasks_path: Path) -> list[str]:
    return [str(json.loads(line)["id"]) for line in tasks_path.read_text().splitlines() if line.strip()]


def check_cell(cell_path: Path, tasks_path: Path) -> tuple[bool, list[str]]:
    problems: list[str] = []
    rows = load_jsonl(cell_path)
    expected = load_expected_task_ids(tasks_path)

    seen_ids: dict[str, int] = {}
    for row in rows:
        tid = str(row.get("task_id"))
        seen_ids[tid] = seen_ids.get(tid, 0) + 1
        status = row.get("status")
        if status == "max_tokens":
            problems.append(f"task {tid}: truncated (status=max_tokens)")
        if row.get("error") or row.get("content") is None:
            problems.append(f"task {tid}: missing content or error")

    for tid in expected:
        count = seen_ids.get(tid, 0)
        if count == 0:
            problems.append(f"task {tid}: missing from cell")
        elif count > 1:
            problems.append(f"task {tid}: appears {count} times (expected 1)")

    extras = set(seen_ids.keys()) - set(expected)
    for tid in extras:
        problems.append(f"task {tid}: unexpected (not in corpus)")

    return (len(problems) == 0), problems


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Publish gate for a benchmark cell.")
    p.add_argument("cell", type=Path, help="Path to per-cell JSONL run output")
    p.add_argument("--tasks", type=Path, required=True, help="Expected tasks JSONL")
    args = p.parse_args(argv)

    ok, problems = check_cell(args.cell, args.tasks)
    if ok:
        print(f"GATE PASS: {args.cell}")
        return 0
    print(f"GATE FAIL: {args.cell}")
    for prob in problems:
        print(f"  - {prob}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
