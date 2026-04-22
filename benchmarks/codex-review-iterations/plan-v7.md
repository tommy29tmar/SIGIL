# Hewn Benchmark Plan v7 — for Codex review

## Changes from v6 (2 issues addressed)

**[M1 fix v7]** T0 renamed throughout to **"append-vs-replace exposure
calibration"** (not "CLAUDE.md asymmetry"). `--append-system-prompt`
inherits the entire default Claude Code system prompt PLUS user's
CLAUDE.md; `--system-prompt` replaces everything. T0 measures aggregate
exposure delta, not CLAUDE.md alone. Under the OAuth CLI constraint,
isolating CLAUDE.md specifically is not possible (would require
`--bare`, which requires API key). Documented as limitation.

**[M2 fix v7]** Correction formula rewritten in output-token space with
explicit sign conventions. No more "observational delta minus effect"
(sign-ambiguous). For each prompt:

```
# Raw observational (asymmetric exposure):
raw_savings_vs_caveman = caveman_full.output_tokens - hewn_full.output_tokens

# Append-vs-append apples-to-apples (symmetric exposure):
adj_savings_vs_caveman_appended = caveman_full_appended.output_tokens - hewn_full.output_tokens
```

REPORT presents both as a **bracket/range**: `[adj, raw]` per prompt.
Same for vs terse. Sign convention: positive = Hewn produced fewer
tokens (won). Lower bound = more honest (append vs append); upper bound
= observational (what users see when running the stock tools).

## Goal

Produce benchmark evidence for Hewn's open release. Compare Hewn vs
Verbose Claude vs Caveman (Full + ultra-directive variant) using
Caveman's own methodology in T1a + Hewn-specific extensions in T1b-T5.
All runs via `claude -p` CLI (OAuth, no API key billing).

## Constraints (hard)

- No direct Anthropic API calls. Only `claude -p` via CLI.
- Model: `--model claude-opus-4-7` (full ID). Asserted via
  `modelUsage["claude-opus-4-7"].outputTokens == usage.output_tokens`.
- Language: English only.
- Fairness: T1a replicates Caveman `evals/llm_run.py`. T0 calibrates
  append-vs-replace exposure.
- Temperature: not pinnable; CLI default.
- Environment: NOT isolated. User CLAUDE.md + Claude Code default
  system prompt both active. Append-vs-replace asymmetry calibrated in
  T0.

## Append-vs-replace exposure — analysis

The two system-prompt flags differ structurally:

- `--system-prompt <x>` — **replaces** Claude Code's entire default
  system prompt (which includes tool instructions, environment info,
  auto-memory, user CLAUDE.md, etc.) with `<x>`.
- `--append-system-prompt <x>` — **adds** `<x>` to the default stack;
  everything else remains.

| Arm | Flag | Sees Claude Code default + CLAUDE.md? |
|---|---|---|
| `baseline` | (none) | YES (default is full) |
| `terse` | `--system-prompt` | NO |
| `caveman_full` | `--system-prompt` | NO |
| `caveman_full_plus_ultra_directive` | `--system-prompt` | NO |
| `hewn_prompt_only` | `--append-system-prompt` | YES |
| `hewn_full` | `--append-system-prompt` (via hewn wrapper) | YES |

The user's CLAUDE.md contains a terseness instruction ("Answer
concisely. Drop filler..."). This adds a terseness signal to all arms
that see the default. The Claude Code default also carries tool
instructions, etc. — we cannot decompose which component drives the
delta.

**Bias direction**: Hewn-vs-Caveman/terse comparisons are observed
under **asymmetric exposure**: Hewn arms have `hewn prompt + default +
CLAUDE.md`; Caveman/terse arms have `their_prompt only`. This may
inflate Hewn savings if the default+CLAUDE.md reinforces terseness
(likely given user's CLAUDE.md content). Direction and magnitude
quantified by T0.

**Comparisons preserving apples-to-apples**:
- Hewn-vs-baseline: both see default+CLAUDE.md → causal claim valid
- Hewn-vs-`caveman_full_appended` (from T0): both see default+CLAUDE.md
  → causal claim valid
- Hewn-vs-`caveman_full` (T1a-T5): observational, asymmetric → reported
  as upper bound of range

## Caveman study findings

(unchanged) `evals/llm_run.py`: 1 run per (prompt, arm), 3 arms,
`--system-prompt`, tiktoken o200k_base. Honest delta = skill vs terse.

## Arms

| ID | System prompt content | Mechanism | T0 | T1a | T1b | T2 | T3 | T4 | T5 |
|---|---|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `baseline` | (none) | `claude -p --model claude-opus-4-7 <prompt>` |   | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `terse` | `"Answer concisely."` | `claude -p --model claude-opus-4-7 --system-prompt <content> <prompt>` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `terse_appended` | same content | `claude -p --model claude-opus-4-7 --append-system-prompt <content> <prompt>` | ✓ |   |   |   |   |   |   |
| `caveman_full` | terse + SKILL.md | `--system-prompt` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `caveman_full_appended` | same content | `--append-system-prompt` | ✓ |   |   |   |   |   |   |
| `caveman_full_plus_ultra_directive` | caveman_full + ultra directive | `--system-prompt` |   |   | ✓ | ✓ | ✓ |   | ✓ |
| `hewn_prompt_only` | hewn_thinking_system_prompt.txt | `--append-system-prompt` |   |   | ✓ | ✓ | ✓ | ✓ | ✓ |
| `hewn_full` | (same content via `--append`) + hook | `bash <repo>/integrations/claude-code/bin/hewn -p ...` |   |   | ✓ | ✓ | ✓ | ✓ | ✓ |

`run.py` reads each arm file and passes CONTENT as the flag value.
Sentinel smoke test verifies.

## Tracks

| ID | Prompt set | # prompts | # runs | # arms | Calls | Purpose | Label |
|----|-----------|-----------|--------|--------|-------|---------|-------|
| **T0** | `short_en.txt` (10) | 10 | 1 | 4 (terse, terse_appended, caveman_full, caveman_full_appended) | 40 | **Append-vs-replace exposure calibration** | Calibration |
| **T1a** | `short_en.txt` | 10 | 1 | 3 (baseline, terse, caveman_full) | 30 | Strict Caveman replication | Caveman parity |
| T1b | same | 10 | 3 | 6 | 180 | Extended | Hewn extension |
| T2 | `vibe_en.txt` (5) | 5 | 3 | 6 | 90 | Vibe / non-tech | Hewn extension |
| T3 | `long_en.txt` (3, ~16k handbook) | 3 | 3 | 6 | 54 | Long context | Hewn extension |
| T4 | `multiturn_en.json` (2 seq × 5 turns) | 10 turns | 2 | 5 | 100 | Drift + isolated hook value | Hewn extension |
| T5 | `expansive_en.txt` (2) | 2 | 2 | 6 | 24 | Honesty: Hewn loses | Hewn extension |

Note: T0 includes terse and caveman_full so the append vs replace deltas
can be computed within the same prompt set without relying on T1a
alignment. These runs are distinct from T1a (different randomization
index if T0 runs first) and snapshotted separately under
`snapshots/raw/T0/...`.

Total: 518 benchmark calls + ~518 judge ≈ 1036. Time: 85-120 min.

## Arm-order randomization

(unchanged from v6) Factoradic permutation, seed `"hewn-bench-v1"`.
T0 and T1a do NOT randomize (single-run sequential).

## Multi-turn (T4) session isolation

(unchanged from v6) Explicit `session_id` + `--resume <id>`, post-run
validation.

## Metrics captured per call

(unchanged from v6)

## Metrics derived

(unchanged from v6 list; corrected formulas below)

**Append-vs-replace exposure deltas (T0)** — positive means appending
compresses MORE than replacing:

```
terse_exposure_effect_per_prompt = terse.output_tokens - terse_appended.output_tokens
caveman_full_exposure_effect_per_prompt = caveman_full.output_tokens - caveman_full_appended.output_tokens
```

If these are positive → the default+CLAUDE.md context makes responses
shorter → Hewn-vs-replace numbers are inflated by this magnitude.
If negative → the opposite (default+CLAUDE.md context makes responses
longer, possibly due to tool/Claude-Code verbosity overwhelming
CLAUDE.md terseness).

**Hewn-vs-Caveman savings — reported as a range (raw and adjusted)**:

Per prompt, with sign convention "positive = Hewn fewer tokens":

```
raw_savings_vs_caveman_tokens = caveman_full.output_tokens - hewn_full.output_tokens
adj_savings_vs_caveman_tokens = caveman_full_appended.output_tokens - hewn_full.output_tokens
```

`adj_` (from T0 caveman_full_appended) is apples-to-apples
(both arms see default+CLAUDE.md). `raw_` is observational (what users
see when running stock Caveman vs stock Hewn).

Same for vs terse:
```
raw_savings_vs_terse_tokens = terse.output_tokens - hewn_full.output_tokens
adj_savings_vs_terse_tokens = terse_appended.output_tokens - hewn_full.output_tokens
```

REPORT presents both per-prompt and aggregate as `[adj, raw]` bracket.

## Judge methodology

(unchanged from v6)

## Directory layout

(unchanged from v6; `arms/` adds `terse_appended.txt` and
`caveman_full_appended.txt` — same content as `terse.txt` /
`caveman_full.txt`. `snapshots/` adds `results_T0.json`)

## Execution order

1. Fetch Caveman at pinned commit; SHA256 SKILL.md; copy to
   `caveman_source/`.
2. Write harness: `run.py`, `judge.py`, `measure.py`.
3. Write prompts + rubrics + arms (incl. T0 arms).
4. Smoke test 1 — model assertion.
5. Smoke test 2 — sentinel arm (content not path).
6. Smoke test 3 — hewn_full hook delta in `cache_creation_input_tokens`.
7. Smoke test 4 — multi-turn `--resume` system-prompt persistence.
8. **T0 calibration** — 4 arms × 10 prompts × 1 run. Reports
   append-vs-replace deltas for terse and caveman_full before any
   Hewn-vs-Caveman comparison is published.
9. **T1a** — strict Caveman parity; compare to Caveman published
   numbers ±25% tol.
10. T1b, T2, T3, T5 runs.
11. T4 multi-turn run + post-run session-isolation validation.
12. Judge pass on all responses.
13. Generate REPORT.md + evidence/ (Hewn-vs-Caveman/terse reported as
    `[adj, raw]` bracket from T0).
14. Commit snapshots + report.

## Honesty commitments

- T5 surfaces where Hewn loses; reported prominently.
- T1a labeled "Caveman parity" using exact methodology.
- All raw JSON snapshots committed.
- `caveman_full_plus_ultra_directive` NEVER called "Caveman Ultra".
- **Append-vs-replace asymmetry**: Hewn-vs-Caveman/terse comparisons
  reported as `[adj, raw]` bracket. Causal claims restricted to
  Hewn-vs-baseline (both inherit default+CLAUDE.md) and
  Hewn-vs-appended-comparator (both inherit default+CLAUDE.md; from T0).
- T0 labeled "append-vs-replace exposure calibration", NOT
  "CLAUDE.md only" (cannot isolate CLAUDE.md under OAuth).
- Hook cost via `cache_creation_input_tokens` delta.
- T4 hook value = `(hewn_prompt_only - hewn_full)` delta.
- Judge failure rate per track.
- Caveman published numbers also ran under their own user context
  (presumed); ±25% parity tolerance.

## Open risks

- T0 measures combined default+CLAUDE.md exposure, not CLAUDE.md alone.
  Pure CLAUDE.md isolation requires `--bare` mode (API key required,
  forbidden). Stated as limitation.
- T0 uses different prompts' exposure effect to correct Hewn numbers.
  Assumes exposure effect is additive per prompt and transferable
  across arms. If effects are prompt-specific or non-linear, bracket
  may be imprecise. Documented.
- Caveman's published numbers may differ ±25% due to user CLAUDE.md,
  CLI version, etc. Documented.
- Temperature unpinnable.
- `--resume` system-prompt persistence: validated step 7.
- Rate limits: backoff + idempotent skip.
- `--append-system-prompt` inherits default + CLAUDE.md → larger input.
  Output-token claims bracketed via T0.

## What this plan does NOT cover

- Sonnet 4.6
- Cross-provider
- Human user studies
- Non-English
- Official `/caveman ultra` skill-runtime
- TTFT
- Pristine isolation (OAuth doesn't allow --bare)
- Isolating CLAUDE.md from default system prompt (cannot decouple)
