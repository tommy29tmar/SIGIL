#!/usr/bin/env python3
"""Run a single benchmark cell with truncation auto-retry.

A cell is one (model × variant × tasks) configuration. If any task returns
status=="max_tokens", the entire cell is rerun with doubled max_output_tokens.
Up to 3 retries. If still truncated, the cell is declared failed and the output
file is moved to <name>.FAILED.jsonl.

Writes:
  - <out> on success (gate-passing cell)
  - <out>.FAILED.jsonl on failure (for debugging)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def any_truncated(cell_path: Path) -> bool:
    with cell_path.open() as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("status") == "max_tokens":
                return True
    return False


def count_rows(cell_path: Path) -> int:
    if not cell_path.exists():
        return 0
    n = 0
    with cell_path.open() as f:
        for line in f:
            if line.strip():
                n += 1
    return n


def run_once(
    runner: str,
    model: str,
    variant_spec: str,
    tasks_path: Path,
    out_path: Path,
    max_output_tokens: int,
) -> int:
    if out_path.exists():
        out_path.unlink()
    cmd = [
        sys.executable,
        str(ROOT / "evals" / runner),
        "--tasks",
        str(tasks_path),
        "--model",
        model,
        "--out",
        str(out_path),
        "--variant",
        variant_spec,
        "--max-output-tokens",
        str(max_output_tokens),
        "--max-retries",
        "3",
    ]
    print(f"$ {' '.join(cmd)}", file=sys.stderr)
    result = subprocess.run(cmd, cwd=str(ROOT))
    return result.returncode


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Run one benchmark cell with truncation auto-retry.")
    p.add_argument("--runner", default="run_anthropic.py", help="Runner script name in evals/")
    p.add_argument("--model", required=True)
    p.add_argument("--variant", required=True, help="variant name@transport=prompt/path.txt")
    p.add_argument("--tasks", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--start-max-tokens", type=int, default=512)
    p.add_argument("--max-retries", type=int, default=3)
    args = p.parse_args(argv)

    cap = args.start_max_tokens
    for attempt in range(args.max_retries + 1):
        print(f"[bench_cell] attempt {attempt+1}: max_output_tokens={cap}", file=sys.stderr)
        rc = run_once(args.runner, args.model, args.variant, args.tasks, args.out, cap)
        if rc != 0:
            print(f"[bench_cell] runner exited {rc}", file=sys.stderr)
            failed_path = args.out.with_name(args.out.stem + ".FAILED.jsonl")
            if args.out.exists():
                args.out.rename(failed_path)
            return rc

        if not any_truncated(args.out):
            print(f"[bench_cell] cell clean: {args.out}", file=sys.stderr)
            return 0

        print(f"[bench_cell] truncation detected, doubling cap", file=sys.stderr)
        cap *= 2

    failed_path = args.out.with_name(args.out.stem + ".FAILED.jsonl")
    args.out.rename(failed_path)
    print(f"[bench_cell] FAILED after {args.max_retries+1} attempts: {failed_path}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
