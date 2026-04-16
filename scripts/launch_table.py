#!/usr/bin/env python3
"""Generate the launch benchmark table from per-cell JSONL files.

Input: a manifest JSON listing per-model cells:
{
  "corpus": "evals/tasks_top_tier_holdout.jsonl",
  "baseline_variant": "baseline-terse",
  "rows": [
    {
      "model": "claude-opus-4-7",
      "display_name": "Opus 4.7",
      "cells": {
        "baseline-terse": "evals/runs/launch/opus47_terse.jsonl",
        "primitive-english": "evals/runs/launch/opus47_primitive.jsonl",
        "sigil-nano": "evals/runs/launch/opus47_sigil.jsonl"
      }
    },
    ...
  ]
}

For each row:
  - Gate-check every cell (publish_gate.py)
  - Merge cells into one temp JSONL
  - Run measure_run with baseline
  - Pull aggregate savings numbers

Emits markdown table + JSON audit to stdout / --out.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.publish_gate import check_cell  # type: ignore
from evals.measure import measure_run  # type: ignore


def merge_cells(cell_paths: list[Path], out_path: Path) -> None:
    with out_path.open("w", encoding="utf-8") as w:
        for p in cell_paths:
            with p.open() as r:
                for line in r:
                    if line.strip():
                        w.write(line)


def fmt_pct(x: float | None, signed: bool = True) -> str:
    if x is None:
        return "—"
    v = x * 100
    if signed:
        sign = "+" if v > 0 else ""
        return f"{sign}{v:.1f}%"
    return f"{v:.1f}%"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("manifest", type=Path)
    p.add_argument("--out", type=Path, default=None)
    p.add_argument("--json-out", type=Path, default=None)
    args = p.parse_args(argv)

    manifest = json.loads(args.manifest.read_text())
    corpus = ROOT / manifest["corpus"]
    baseline_name = manifest["baseline_variant"]

    table_rows: list[dict] = []
    skipped: list[dict] = []

    for row_cfg in manifest["rows"]:
        model = row_cfg["model"]
        display = row_cfg.get("display_name", model)
        cells = row_cfg["cells"]

        cell_paths: list[Path] = []
        gate_problems = []
        for variant_name, rel_path in cells.items():
            cell_path = ROOT / rel_path
            if not cell_path.exists():
                gate_problems.append(f"{variant_name}: file missing ({rel_path})")
                continue
            ok, problems = check_cell(cell_path, corpus)
            if not ok:
                gate_problems.append(f"{variant_name}: gate failed ({len(problems)} issues)")
            cell_paths.append(cell_path)

        if gate_problems:
            skipped.append({"model": display, "reasons": gate_problems})
            continue

        merged_path = ROOT / "evals" / "runs" / "launch" / f"__merged__{model.replace('.','_').replace('-','_')}.jsonl"
        merged_path.parent.mkdir(parents=True, exist_ok=True)
        merge_cells(cell_paths, merged_path)

        summary = measure_run(corpus, merged_path, baseline=baseline_name)
        variants = summary["variants"]
        row_result = {"model": model, "display_name": display, "variants": {}}

        for variant_name in cells.keys():
            v = variants.get(variant_name)
            if v is None:
                continue
            entry = {
                "count": v.get("count"),
                "avg_total_tokens": v.get("avg_total_tokens"),
                "avg_output_tokens": v.get("avg_output_tokens"),
                "avg_elapsed_ms": v.get("avg_elapsed_ms"),
                "must_include_rate": v.get("must_include_rate"),
                "exact_literal_rate": v.get("exact_literal_rate"),
                "parse_rate": v.get("parse_rate"),
            }
            if "baseline_comparison" in v:
                bc = v["baseline_comparison"]
                entry["token_savings"] = bc.get("aggregate_total_token_savings_vs_baseline")
                entry["latency_savings"] = bc.get("aggregate_latency_savings_vs_baseline")
            table_rows.append({
                "model": model,
                "display": display,
                "variant": variant_name,
                **entry,
            })

    # Generate markdown table
    md = []
    md.append("| Model | Variant | Avg total tokens | Tokens vs terse | Latency vs terse | must_include |")
    md.append("| --- | --- | ---: | ---: | ---: | ---: |")
    for r in table_rows:
        mi = r.get("must_include_rate")
        md.append(
            f"| {r['display']} | {r['variant']} | "
            f"{r.get('avg_total_tokens') or '—'} | "
            f"{fmt_pct(-r['token_savings']) if r.get('token_savings') is not None else '—'} | "
            f"{fmt_pct(-r['latency_savings']) if r.get('latency_savings') is not None else '—'} | "
            f"{fmt_pct(mi, signed=False) if mi is not None else '—'} |"
        )
    md_text = "\n".join(md)

    if skipped:
        md_text += "\n\n### Cells skipped (gate failed)\n"
        for s in skipped:
            md_text += f"\n- **{s['model']}**: {'; '.join(s['reasons'])}"

    print(md_text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(md_text, encoding="utf-8")
    if args.json_out:
        args.json_out.write_text(json.dumps({"rows": table_rows, "skipped": skipped}, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
