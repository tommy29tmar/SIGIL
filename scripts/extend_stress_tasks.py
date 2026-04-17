#!/usr/bin/env python3
"""Extend evals/tasks_stress_coding.jsonl from 4 → 10 tasks.

Adds 6 new long-context coding tasks that stress Flint across realistic
engineering categories beyond the original {debug, arch, review, refactor}
quartet. Each new task reuses the existing ~10k-token cache_prefix so the
bench still measures the same "loaded project context" scenario.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STRESS = ROOT / "evals" / "tasks_stress_coding.jsonl"


NEW_TASKS = [
    {
        "id": "debug-memory-leak-node",
        "category": "debugging",
        "mode": "hybrid",
        "prompt_suffix": (
            "[capsule micro debugging]\n"
            "anchors: \"heapUsed\" | \"setInterval\"\n"
            "ctx: Atlas callback billing worker\n"
            "rule: heapUsed grows across ticks even when queue is empty\n"
            "need: find retained refs, propose minimal fix\n"
            "issue: retained closures inside setInterval callback hold batch rows\n"
            "deliver: root_cause min_fix reg_test"
        ),
        "must_include": ["heap", "leak", "profile", "verify"],
        "exact_literals": ["heapUsed", "setInterval"],
    },
    {
        "id": "arch-audit-log-schema",
        "category": "architecture",
        "mode": "hybrid",
        "prompt_suffix": (
            "[capsule micro architecture]\n"
            "anchors: \"JSONB\" | \"7 years\"\n"
            "ctx: Atlas audit log retention\n"
            "need: schema that supports compliance export, partitioned by month\n"
            "store: PostgreSQL\n"
            "retention: 7 years\n"
            "ops: lean platform team\n"
            "deliver: schema_sketch partitioning_strategy short_why"
        ),
        "must_include": ["audit", "retention", "partition", "compliance"],
        "exact_literals": ["JSONB", "7 years"],
    },
    {
        "id": "review-rate-limit-bypass",
        "category": "code_review",
        "mode": "hybrid",
        "prompt_suffix": (
            "[capsule micro review]\n"
            "anchors: \"X-Forwarded-For\" | \"Redis\"\n"
            "diff: + const key=`rl:${req.headers['x-forwarded-for']||req.ip}`;"
            " await redis.incr(key);\n"
            "ctx: public_api_gateway rate limiter\n"
            "deliver: risk mitigation verify"
        ),
        "must_include": ["bypass", "spoof", "rate", "verify"],
        "exact_literals": ["X-Forwarded-For", "Redis"],
    },
    {
        "id": "refactor-extract-shared-lib",
        "category": "refactoring",
        "mode": "hybrid",
        "prompt_suffix": (
            "[capsule micro refactor]\n"
            "anchors: \"package.json\" | \"semver\"\n"
            "target: currency-formatting helper duplicated across billing, "
            "audit, gateway\n"
            "ctx: extract to @atlas/currency npm package, keep call sites unchanged\n"
            "deliver: extraction_plan versioning_strategy test_strategy"
        ),
        "must_include": ["library", "versioning", "backward", "test"],
        "exact_literals": ["package.json", "semver"],
    },
    {
        "id": "arch-idempotent-webhook",
        "category": "architecture",
        "mode": "hybrid",
        "prompt_suffix": (
            "[capsule micro architecture]\n"
            "anchors: \"Idempotency-Key\" | \"409\"\n"
            "ctx: Atlas payment webhook receiver, provider retries on 5xx\n"
            "need: idempotent processing, duplicate detection, observable replays\n"
            "store: PostgreSQL\n"
            "deliver: dedup_strategy error_model short_why"
        ),
        "must_include": ["idempotent", "duplicate", "key", "verify"],
        "exact_literals": ["Idempotency-Key", "409"],
    },
    {
        "id": "debug-query-n-plus-one",
        "category": "debugging",
        "mode": "hybrid",
        "prompt_suffix": (
            "[capsule micro debugging]\n"
            "anchors: \"N+1\" | \"db.findUser\"\n"
            "ctx: /invoices endpoint latency regressed 3x this week\n"
            "rule: for each invoice row, db.findUser(row.customerId) inside loop\n"
            "need: identify fix, preserve response shape, add regression gate\n"
            "deliver: min_fix reg_test"
        ),
        "must_include": ["N+1", "batch", "query", "verify"],
        "exact_literals": ["N+1", "db.findUser"],
    },
]


def main() -> int:
    existing = [json.loads(l) for l in STRESS.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not existing:
        raise SystemExit(f"{STRESS} is empty; cannot reuse cache_prefix.")
    cache_prefix = existing[0]["cache_prefix"]
    existing_ids = {row["id"] for row in existing}

    merged = list(existing)
    for task in NEW_TASKS:
        if task["id"] in existing_ids:
            continue
        row = {
            **task,
            "prompt": cache_prefix + "\n\n[Task]\n" + task["prompt_suffix"],
            "cache_prefix": cache_prefix,
            "benchmark_scale": "stress",
            "capsule": "micro",
        }
        merged.append(row)

    with STRESS.open("w", encoding="utf-8") as f:
        for row in merged:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    for row in merged:
        print(f"  {row['id']:<34} category={row['category']:<13} "
              f"prompt_chars={len(row['prompt']):>6}", file=sys.stderr)
    print(f"wrote {STRESS} ({len(merged)} tasks)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
