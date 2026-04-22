# Hewn Benchmark Plan v8 — for Codex review

## Changes from v7 (2 issues addressed)

**[M1 fix v8]** Adjusted bracket scope restricted to tracks where
appended comparator arms exist. T0 runs `terse_appended` and
`caveman_full_appended` only on `short_en.txt` → the `adj_` formula
applies only to T1a/T1b. T2-T5 report **raw observational** numbers
only, with an explicit callout:

> "T2-T5 Hewn-vs-Caveman / Hewn-vs-terse figures are observational
> under asymmetric exposure; no appended-comparator calibration was
> run on these prompts. Magnitude of inflation presumed similar to
> T0-measured effect on short_en.txt; not adjusted numerically."

Rationale for not extending appended comparators to T2-T5: cost vs.
value tradeoff. Calibration on short_en already quantifies the
exposure effect magnitude; extending to T2-T5 would add ~150 calls.
We accept the limitation and document it.

**[M2 fix v8]** `[adj, raw]` bracket renamed and no longer assumes
ordering. New naming: **`(appended, observed)`** pair. Per prompt:

```
appended_comparator_vs_hewn = comparator_appended.output_tokens - hewn_full.output_tokens
observed_stock_vs_hewn      = comparator_stock.output_tokens     - hewn_full.output_tokens
```

Sign convention unchanged (positive = Hewn fewer tokens). Ordering NOT
assumed. REPORT derives `min(pair)` and `max(pair)` empirically per
prompt; aggregate statistics reported separately on the `appended` and
`observed` series rather than as a "range".

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
- Environment: NOT isolated. Append-vs-replace asymmetry: calibrated
  in T0 for short_en, acknowledged as observational for T2-T5.

## Append-vs-replace exposure — analysis

(unchanged from v7)

`--system-prompt` replaces entire default Claude Code system prompt
(tool instructions, env info, auto-memory, user CLAUDE.md);
`--append-system-prompt` adds to that stack.

| Arm | Flag | Sees default+CLAUDE.md? |
|---|---|---|
| `baseline` | (none) | YES |
| `terse`, `caveman_full`, `caveman_full_plus_ultra_directive` | `--system-prompt` | NO |
| `hewn_prompt_only`, `hewn_full` | `--append-system-prompt` | YES |

Hewn-vs-Caveman/terse comparisons are observed under asymmetric
exposure; direction and magnitude quantified by T0 on short_en only.

**Causal claims preserved for**:
- Hewn-vs-baseline (both inherit default+CLAUDE.md)
- Hewn-vs-`<comparator>_appended` on short_en (both inherit
  default+CLAUDE.md)

**Observational only for**:
- Hewn-vs-`<comparator>_stock` on any track (asymmetric exposure)
- T2-T5 comparator comparisons (no appended calibration run)

## Caveman study findings

(unchanged from v7)

## Arms

(unchanged from v7)

| ID | System prompt content | Mechanism | T0 | T1a | T1b | T2 | T3 | T4 | T5 |
|---|---|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `baseline` | (none) | `claude -p --model claude-opus-4-7 <prompt>` |   | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `terse` | `"Answer concisely."` | `--system-prompt` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `terse_appended` | same content | `--append-system-prompt` | ✓ |   |   |   |   |   |   |
| `caveman_full` | terse + SKILL.md | `--system-prompt` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `caveman_full_appended` | same content | `--append-system-prompt` | ✓ |   |   |   |   |   |   |
| `caveman_full_plus_ultra_directive` | + ultra directive | `--system-prompt` |   |   | ✓ | ✓ | ✓ |   | ✓ |
| `hewn_prompt_only` | hewn_thinking_system_prompt.txt | `--append-system-prompt` |   |   | ✓ | ✓ | ✓ | ✓ | ✓ |
| `hewn_full` | (same content via `--append`) + hook | `hewn -p` |   |   | ✓ | ✓ | ✓ | ✓ | ✓ |

## Tracks

| ID | Prompt set | # prompts | # runs | # arms | Calls | Purpose | Label |
|----|-----------|-----------|--------|--------|-------|---------|-------|
| **T0** | `short_en.txt` (10) | 10 | 1 | 4 | 40 | Append-vs-replace exposure calibration | Calibration |
| **T1a** | `short_en.txt` | 10 | 1 | 3 | 30 | Strict Caveman replication | Caveman parity |
| T1b | same | 10 | 3 | 6 | 180 | Extended | Hewn extension |
| T2 | `vibe_en.txt` (5) | 5 | 3 | 6 | 90 | Vibe / non-tech | Hewn extension (observational only) |
| T3 | `long_en.txt` (3, ~16k) | 3 | 3 | 6 | 54 | Long context | Hewn extension (observational only) |
| T4 | `multiturn_en.json` (2 seq × 5 turns) | 10 turns | 2 | 5 | 100 | Drift + hook value | Hewn extension (observational only) |
| T5 | `expansive_en.txt` (2) | 2 | 2 | 6 | 24 | Honesty: Hewn loses | Hewn extension (observational only) |

Total: 518 benchmark calls + ~518 judge ≈ 1036. Time: 85-120 min.

## Arm-order randomization

(unchanged from v7)

## Multi-turn (T4) session isolation

(unchanged from v7)

## Metrics captured per call

(unchanged from v7)

## Metrics derived

**Append-vs-replace exposure deltas (T0, short_en only)**:

Signed delta, no sign assumed:
```
terse_exposure_delta_per_prompt = terse_appended.output_tokens - terse.output_tokens
caveman_full_exposure_delta_per_prompt = caveman_full_appended.output_tokens - caveman_full.output_tokens
```

Positive → appending makes output longer than replacing.
Negative → appending compresses more than replacing.
Reported per prompt + aggregated (median, mean, stdev).

**Hewn-vs-Caveman/terse — (appended, observed) pair, T1a/T1b only**:

Per prompt, positive = Hewn fewer tokens:
```
appended_comparator_vs_hewn_caveman = caveman_full_appended.output_tokens - hewn_full.output_tokens
observed_stock_vs_hewn_caveman      = caveman_full.output_tokens - hewn_full.output_tokens

appended_comparator_vs_hewn_terse = terse_appended.output_tokens - hewn_full.output_tokens
observed_stock_vs_hewn_terse      = terse.output_tokens - hewn_full.output_tokens
```

Aggregate: report the `appended` and `observed` series independently
with median/mean/min/max/stdev. REPORT also computes per-prompt
`min(appended, observed)` and `max(appended, observed)` empirically,
WITHOUT assuming adj < raw or vice versa.

**Hewn-vs-Caveman/terse on T2-T5** — **raw observational only**:
```
observed_stock_vs_hewn_caveman = caveman_full.output_tokens - hewn_full.output_tokens
observed_stock_vs_hewn_terse   = terse.output_tokens - hewn_full.output_tokens
```

Labeled clearly in REPORT: "observational under asymmetric exposure,
not adjusted numerically. T0 measured magnitude of effect on short_en
for reference context."

**Hewn-vs-baseline** — causal, both arms symmetric:
```
observed_baseline_vs_hewn = baseline.output_tokens - hewn_full.output_tokens
```
Reported in all tracks.

Other metrics (info density, literal preservation, format compliance,
concepts covered, stability, cache efficiency, hook value T4, hewn
classifier injection cost via cache_creation delta, cumulative
multi-turn, wrapper overhead, readability, judge failure rate):
unchanged from v7.

## Judge methodology

(unchanged from v7)

## Directory layout

(unchanged from v7)

## Execution order

(unchanged from v7, steps 1-14)

## Honesty commitments

(updated)

- T5 surfaces where Hewn loses.
- T1a labeled "Caveman parity".
- All raw JSON snapshots committed.
- `caveman_full_plus_ultra_directive` NEVER called "Caveman Ultra".
- **Hewn-vs-Caveman/terse on T1a/T1b**: `(appended, observed)` pair
  reported per prompt; aggregate on each series independently.
  No implied ordering.
- **Hewn-vs-Caveman/terse on T2-T5**: raw observational only; labeled
  explicitly as not adjusted. T0 magnitude cited as reference context.
- **Hewn-vs-baseline (all tracks)**: causal, symmetric exposure.
- T0 labeled "append-vs-replace exposure calibration", NOT
  "CLAUDE.md-only" (cannot isolate CLAUDE.md under OAuth).
- Hook cost via `cache_creation_input_tokens` delta.
- T4 hook value = `(hewn_prompt_only - hewn_full)` delta only.
- Judge failure rate per track.

## Open risks

- T0 only calibrates short_en prompts. T2-T5 Hewn-vs-Caveman numbers
  are observational; magnitude of inflation presumed but not measured
  on those prompts. If rigor demands, re-run T2-T5 with appended
  comparators (not in this plan).
- T0 measures combined default+CLAUDE.md exposure, not CLAUDE.md alone.
  Cannot isolate under OAuth.
- Exposure effect may be non-additive or non-transferable across
  arms/prompts. Documented.
- Caveman's published numbers may differ ±25%; documented.
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
