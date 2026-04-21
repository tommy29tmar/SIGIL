#!/usr/bin/env python3
"""Aggregate the vibe-coding 3-way bench."""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evals" / "runs" / "vibe_3way"
CORPUS = ROOT / "evals" / "vibe_3way.jsonl"

IR_PREFIX = re.compile(r"^\s*@flint\s+v\d+\b", re.IGNORECASE)
FENCED = re.compile(r"```[\w+-]*\n[\s\S]*?\n```", re.MULTILINE)

VARIANTS = ["plain", "cccaveman", "flint"]


def nfc(s: str | None) -> str:
    return unicodedata.normalize("NFC", s or "")


def detect_shape(row: dict) -> str:
    raw = nfc(row.get("content"))
    if IR_PREFIX.match(raw):
        return "ir"
    if any("submit_flint_ir" in (tu.get("name") or "").lower() for tu in row.get("tool_uses") or []):
        return "ir"
    if FENCED.search(raw):
        return "prose_code"
    return "prose"


def load() -> dict[str, list[dict]]:
    corpus = [json.loads(l) for l in CORPUS.read_text().splitlines() if l.strip()]
    by_prompt = {}
    for prompt in corpus:
        pid = prompt["id"]
        by_prompt[pid] = {"expected": prompt["expected_shape"], "prompt": prompt["prompt"], "results": {}}
    for path in sorted(OUT.glob("*.json")):
        row = json.loads(path.read_text())
        name = path.stem  # variant_promptid
        for v in VARIANTS:
            pfx = f"{v}_"
            if name.startswith(pfx):
                pid = name[len(pfx):]
                if pid in by_prompt:
                    by_prompt[pid]["results"][v] = row
                break
    return by_prompt


def main() -> None:
    data = load()

    # Headline: per-prompt × variant grid
    cols = ["prompt_id", "expected"] + [f"{v}_shape" for v in VARIANTS] + [f"{v}_tok" for v in VARIANTS] + [f"{v}_tools" for v in VARIANTS] + [f"{v}_lat" for v in VARIANTS]
    print(f"{'prompt':<18} {'exp':<14} " + " ".join(f"{v:<22}" for v in VARIANTS))
    print(f"{'':<18} {'':<14} " + " ".join(f"{'shape/tok/tools/lat':<22}" for v in VARIANTS))
    totals = {v: {"tok": 0, "lat": 0, "tools": 0, "shape_hits": 0, "n": 0} for v in VARIANTS}
    for pid, entry in data.items():
        exp = entry["expected"]
        cells = []
        for v in VARIANTS:
            r = entry["results"].get(v)
            if not r:
                cells.append(f"{'MISSING':<22}")
                continue
            shape = detect_shape(r)
            tok = (r.get("usage") or {}).get("output_tokens") or 0
            tools = len(r.get("tool_uses") or [])
            lat = int((r.get("elapsed_ms") or 0) / 1000)
            totals[v]["tok"] += tok
            totals[v]["lat"] += lat
            totals[v]["tools"] += tools
            totals[v]["n"] += 1
            # shape hit: exact match, OR ir-expected matches prose_code (both technical), OR prose*-expected matches prose
            hit_exact = (shape == exp)
            hit_relaxed = (shape in {"ir", "prose_code"} and exp in {"ir", "prose_code"}) or (shape == "prose" and exp.startswith("prose"))
            if hit_exact:
                totals[v]["shape_hits"] += 1
            marker = "✓" if hit_exact else ("~" if hit_relaxed else "✗")
            cells.append(f"{marker}{shape:<11}{tok:>5}t{tools:>2}T{lat:>3}s  ")
        print(f"{pid:<18} {exp:<14} " + " ".join(cells))

    print()
    print("Totals:")
    print(f"{'variant':<12} {'tok_sum':>8} {'lat_sum':>8} {'tools':>6} {'shape_hit':>10}")
    for v in VARIANTS:
        t = totals[v]
        hit_pct = (t["shape_hits"] / t["n"] * 100) if t["n"] else 0
        print(f"{v:<12} {t['tok']:>8} {t['lat']:>7}s {t['tools']:>6} {hit_pct:>9.0f}%")

    plain = totals["plain"]
    if plain["tok"]:
        print()
        print("vs plain:")
        for v in ("cccaveman", "flint"):
            t = totals[v]
            dt = (t["tok"] - plain["tok"]) / plain["tok"] * 100
            dl = (t["lat"] - plain["lat"]) / plain["lat"] * 100 if plain["lat"] else 0
            dtools = t["tools"] - plain["tools"]
            print(f"  {v:<12} tok {dt:+6.1f}%   lat {dl:+6.1f}%   tools {dtools:+d}")


if __name__ == "__main__":
    main()
