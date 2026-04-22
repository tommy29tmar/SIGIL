# Hewn Benchmark Plan v9 — for Codex review

## Changes from v8 (2 issues addressed)

**[M1 fix v9]** Cross-track join for short_en comparisons defined
explicitly:

- `terse_appended` and `caveman_full_appended` (appended comparators)
  exist ONLY in T0 (1 run per prompt).
- `hewn_full` exists ONLY in T1b (3 runs per prompt) for short_en, and
  in T2-T5 for their respective prompts.
- T1a does NOT include `hewn_full` (T1a is strict 3-arm Caveman parity).

**Join rule for short_en (appended, observed) pair**:
```
For each prompt_id in short_en:
  appended_pair_caveman = T0[caveman_full_appended][prompt_id].output_tokens
                          - median(T1b[hewn_full][prompt_id].r1.r2.r3.output_tokens)
  observed_pair_caveman = median(T1b[caveman_full][prompt_id].r1.r2.r3.output_tokens)
                          - median(T1b[hewn_full][prompt_id].r1.r2.r3.output_tokens)
```
Same for terse vs hewn. Median across the 3 T1b runs, single T0 run on
appended side, single T1a run for caveman_full could also be used but
we use T1b (3 runs) for the observed side because it's more stable.
T1a values reserved exclusively as Caveman parity headline numbers.

**[M2 fix v9]** "Hewn-vs-baseline reported in all tracks" corrected to
"reported in **T1b-T5**" (the tracks where both `baseline` and
`hewn_full` arms exist). T0 has neither; T1a has baseline but no
`hewn_full`. Updated explicitly.

**Updated metric availability matrix**:

| Metric | T0 | T1a | T1b | T2 | T3 | T4 | T5 |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Append-vs-replace exposure deltas | ✓ |   |   |   |   |   |   |
| Caveman parity (skill vs terse) |   | ✓ |   |   |   |   |   |
| Hewn-vs-baseline (causal) |   |   | ✓ | ✓ | ✓ | ✓ | ✓ |
| (appended, observed) pair |   |   | ✓* |   |   |   |   |
| Hewn-vs-Caveman observational only |   |   | ✓ | ✓ | ✓ | ✓ | ✓ |

`*` appended side from T0 + observed/hewn side from T1b (per join rule)

## Goal

Produce benchmark evidence for Hewn's open release. Compare Hewn vs
Verbose Claude vs Caveman (Full + ultra-directive variant) using
Caveman's own methodology in T1a + Hewn-specific extensions in T1b-T5.
All runs via `claude -p` CLI (OAuth, no API key billing).

## Constraints (hard)

- No direct Anthropic API calls. Only `claude -p` via CLI.
- Model: `--model claude-opus-4-7`. Asserted via
  `modelUsage["claude-opus-4-7"].outputTokens == usage.output_tokens`.
- Language: English only.
- Fairness: T1a replicates Caveman `evals/llm_run.py` precisely.
  T0 calibrates append-vs-replace exposure on short_en only.
- Temperature: not pinnable; CLI default.
- Environment: NOT isolated.

## Append-vs-replace exposure — analysis

(unchanged from v8) Exposure asymmetry between `--system-prompt` (replaces)
and `--append-system-prompt` (adds). T0 quantifies on short_en only.

**Causal claims preserved for**:
- Hewn-vs-baseline in T1b-T5 (both inherit default+CLAUDE.md)
- Hewn-vs-`<comparator>_appended` on short_en, using T0+T1b join
  (both inherit default+CLAUDE.md)

**Observational only for**:
- Hewn-vs-stock-Caveman/terse in any track (asymmetric exposure)

## Caveman study findings

(unchanged) `evals/llm_run.py`: 1 run per (prompt, arm), 3 arms,
`--system-prompt`, tiktoken o200k_base. Honest delta = skill vs terse.

## Arms

(unchanged from v8 — same arm × track matrix)

## Tracks

| ID | Prompt set | # prompts | # runs | # arms | Calls | Purpose | Label |
|----|-----------|-----------|--------|--------|-------|---------|-------|
| **T0** | `short_en.txt` (10) | 10 | 1 | 4 (terse, terse_appended, caveman_full, caveman_full_appended) | 40 | Append-vs-replace exposure calibration | Calibration |
| **T1a** | `short_en.txt` | 10 | 1 | 3 (baseline, terse, caveman_full) | 30 | Strict Caveman replication | Caveman parity |
| T1b | same | 10 | 3 | 6 | 180 | Extended | Hewn extension |
| T2 | `vibe_en.txt` (5) | 5 | 3 | 6 | 90 | Vibe / non-tech | Observational only |
| T3 | `long_en.txt` (3, ~16k) | 3 | 3 | 6 | 54 | Long context | Observational only |
| T4 | `multiturn_en.json` (2 seq × 5 turns) | 10 turns | 2 | 5 | 100 | Drift + hook value | Observational only |
| T5 | `expansive_en.txt` (2) | 2 | 2 | 6 | 24 | Honesty: Hewn loses | Observational only |

Total: 518 benchmark calls + ~518 judge ≈ 1036. Time: 85-120 min.

## Arm-order randomization

(unchanged from v8) Factoradic permutation, seed `"hewn-bench-v1"`.
T0 and T1a do NOT randomize.

## Multi-turn (T4) session isolation

(unchanged from v8)

## Metrics captured per call

(unchanged from v8)

## Metrics derived

**Append-vs-replace exposure deltas (T0, short_en only)**:
```
terse_exposure_delta_per_prompt = terse_appended.output_tokens - terse.output_tokens
caveman_full_exposure_delta_per_prompt = caveman_full_appended.output_tokens - caveman_full.output_tokens
```
Sign: positive → appending makes output longer; negative → appending
compresses more.

**Hewn-vs-Caveman/terse on short_en — `(appended, observed)` pair**
(cross-track join: T0 + T1b):

Per prompt_id in short_en, positive = Hewn fewer tokens:
```
hewn_med = median([T1b[hewn_full][prompt_id][r].output_tokens for r in 1..3])
appended_pair_caveman = T0[caveman_full_appended][prompt_id].output_tokens - hewn_med
observed_pair_caveman = median([T1b[caveman_full][prompt_id][r].output_tokens for r in 1..3]) - hewn_med
appended_pair_terse   = T0[terse_appended][prompt_id].output_tokens - hewn_med
observed_pair_terse   = median([T1b[terse][prompt_id][r].output_tokens for r in 1..3]) - hewn_med
```

Aggregate: `appended` and `observed` series each report
median/mean/min/max/stdev across the 10 prompts. NO range/bracket
ordering assumed.

**Hewn-vs-Caveman/terse on T2-T5** — raw observational only:
```
observed_stock_vs_hewn_caveman = median(caveman_full runs).output_tokens - median(hewn_full runs).output_tokens
observed_stock_vs_hewn_terse   = median(terse runs).output_tokens - median(hewn_full runs).output_tokens
```
Labeled clearly: not adjusted; T0 magnitude cited as reference.

**Hewn-vs-baseline (T1b-T5 only)** — causal, symmetric exposure:
```
observed_baseline_vs_hewn = median(baseline runs).output_tokens - median(hewn_full runs).output_tokens
```
Reported in T1b-T5 only (T0 has no baseline; T1a has no hewn_full).

**Caveman parity headline (T1a only)**: aggregate output-token tables
matching Caveman `evals/measure.py` output format (median/mean/min/max
/stdev across 10 prompts, savings vs `__terse__`).

Other derived metrics (info density, literal preservation, format
compliance, concepts, stability, cache efficiency, T4 hook value,
classifier injection cost via cache_creation delta, cumulative T4 cost,
wrapper overhead, readability, judge failure rate): unchanged from v8.

## Judge methodology

(unchanged from v8)

## Directory layout

(unchanged from v8)

## Execution order

1. Fetch Caveman at pinned commit; SHA256 SKILL.md; copy to
   `caveman_source/`.
2. Write harness: `run.py`, `judge.py`, `measure.py`.
3. Write prompts + rubrics + arms (incl. T0 arms).
4. Smoke test 1 — model assertion.
5. Smoke test 2 — sentinel arm (content not path).
6. Smoke test 3 — hewn_full hook delta in `cache_creation_input_tokens`.
7. Smoke test 4 — multi-turn `--resume` system-prompt persistence.
8. **T0 calibration** before any Hewn-vs-Caveman comparison published.
9. **T1a** — strict Caveman parity (matches their evals format).
10. T1b runs (provides hewn_full for short_en, enables T0+T1b joins).
11. T2, T3, T5 runs.
12. T4 multi-turn run + post-run session-isolation validation.
13. Judge pass on all responses.
14. Generate REPORT.md + evidence/ (with explicit T0+T1b joins for
    short_en (appended, observed) pair tables).
15. Commit snapshots + report.

## Honesty commitments

- T5 surfaces where Hewn loses.
- T1a labeled "Caveman parity" using exact methodology.
- All raw JSON snapshots committed.
- `caveman_full_plus_ultra_directive` NEVER called "Caveman Ultra".
- **Hewn-vs-Caveman/terse on short_en**: `(appended, observed)` pair
  via T0+T1b join. Per-prompt and aggregate. No implied ordering.
- **Hewn-vs-Caveman/terse on T2-T5**: raw observational only; not
  adjusted. T0 magnitude cited as reference context.
- **Hewn-vs-baseline (T1b-T5)**: causal, symmetric exposure. NOT
  reported for T0 (no baseline arm) or T1a (no hewn_full arm).
- T0 labeled "append-vs-replace exposure calibration", NOT CLAUDE.md
  isolation (cannot isolate under OAuth).
- Hook cost via `cache_creation_input_tokens` delta.
- T4 hook value = `(hewn_prompt_only - hewn_full)` delta only.
- Judge failure rate per track.

## Open risks

- T0 only calibrates short_en. T2-T5 Hewn-vs-Caveman observational
  only.
- T0 measures combined default+CLAUDE.md exposure; cannot isolate
  CLAUDE.md alone under OAuth.
- T0+T1b cross-track join uses 1 T0 run vs median of 3 T1b runs —
  asymmetric noise. T0 single-run noise inherits into the appended
  pair number. Documented; if T0 stdev is large for a prompt, flag in
  REPORT.
- Exposure effect may not transfer additively across arms/prompts.
- Caveman published numbers may differ ±25%.
- Temperature unpinnable.
- `--resume` persistence: validated step 7.
- Rate limits: backoff + idempotent skip.

## What this plan does NOT cover

- Sonnet 4.6
- Cross-provider
- Human studies
- Non-English
- Official `/caveman ultra` skill-runtime
- TTFT
- Pristine isolation (OAuth forbids --bare)
- CLAUDE.md isolation from default system prompt
- Appended-comparator calibration on T2-T5 prompts
- Multiple T0 runs per prompt (single-run; noise documented)
