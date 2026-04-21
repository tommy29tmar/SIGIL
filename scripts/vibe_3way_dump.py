#!/usr/bin/env python3
"""Dump each prompt's 3 responses side-by-side for qualitative review."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evals" / "runs" / "vibe_3way"
CORPUS = ROOT / "evals" / "vibe_3way.jsonl"

VARIANTS = ["plain", "cccaveman", "flint"]


def main() -> None:
    corpus = {json.loads(l)["id"]: json.loads(l) for l in CORPUS.read_text().splitlines() if l.strip()}
    for pid, meta in corpus.items():
        print("=" * 80)
        print(f"PROMPT {pid}  expected={meta['expected_shape']}")
        print("-" * 80)
        print(meta["prompt"])
        print()
        for v in VARIANTS:
            path = OUT / f"{v}_{pid}.json"
            if not path.exists():
                print(f"--- {v.upper()} MISSING ---\n")
                continue
            r = json.loads(path.read_text())
            tok = (r.get("usage") or {}).get("output_tokens") or 0
            tools = len(r.get("tool_uses") or [])
            lat = int((r.get("elapsed_ms") or 0) / 1000)
            content = r.get("content") or ""
            print(f"--- {v.upper()}  ({tok} tok, {tools} tools, {lat}s) ---")
            print(content)
            print()


if __name__ == "__main__":
    main()
