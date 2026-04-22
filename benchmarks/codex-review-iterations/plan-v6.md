# Hewn Benchmark Plan v6 — for Codex review

## Changes from v5 (1 issue addressed)

**[H1 fix v6]** Bias direction in CLAUDE.md asymmetry was misstated.
Corrected:

- Hewn arms (`--append`) inherit CLAUDE.md ("Answer concisely. Drop
  filler...") on top of the hewn prompt → DOUBLE terseness reinforcement
- Caveman/terse arms (`--system-prompt`) replace CLAUDE.md → SINGLE
  terseness from their own SKILL/instruction
- Therefore Hewn-vs-Caveman/terse comparisons may be **inflated in
  Hewn's favor**, not deflated as v5 incorrectly stated

Two mitigations added:

1. **New auxiliary track T0** — "asymmetry calibration":
   - Re-run all 10 `short_en.txt` prompts with two extra arms:
     - `terse_appended` — `terse` content via `--append-system-prompt`
     - `caveman_full_appended` — `caveman_full` content via
       `--append-system-prompt`
   - Compare deltas: `terse_appended.output_tokens` vs `terse.output_tokens`,
     same for caveman_full
   - Delta quantifies the CLAUDE.md compression effect
   - Used as correction factor / context in REPORT for Hewn-vs-Caveman
     observational claims
   - 10 prompts × 1 run × 2 arms = 20 extra calls
2. **Report language demoted**: any Hewn-vs-Caveman/terse number is
   labeled "observational under asymmetric CLAUDE.md exposure (see T0
   calibration)". Causal claims ("Hewn saves X%") only made for
   Hewn-vs-baseline (where both inherit CLAUDE.md, apples-to-apples).

## Goal

Produce benchmark evidence for Hewn's open release. Compare Hewn vs
Verbose Claude vs Caveman (Full + ultra-directive variant) using
Caveman's own methodology in T1a + Hewn-specific extensions in T1b-T5.
All runs via `claude -p` CLI (OAuth, no API key billing).

## Constraints (hard)

- No direct Anthropic API calls. Only `claude -p` via CLI.
- Model: `--model claude-opus-4-7` (full ID) on every call. Asserted via
  `modelUsage["claude-opus-4-7"].outputTokens == usage.output_tokens`.
- Language: English only.
- Fairness: T1a replicates Caveman `evals/llm_run.py` precisely. T0
  calibrates the CLAUDE.md asymmetry effect.
- Temperature: not pinnable; CLI default.
- Environment: NOT isolated. User's `~/.claude/CLAUDE.md` active.
  Asymmetry calibrated via T0 + documented.

## CLAUDE.md asymmetry — corrected analysis

User's `~/.claude/CLAUDE.md` content includes "Answer concisely. Drop
filler, hedging, and pleasantries..." (terseness instruction).

| Arm | Sees CLAUDE.md? | Mechanism |
|---|---|---|
| `baseline` | YES | no flag; CLAUDE.md is in default Claude Code system prompt |
| `terse` | NO | `--system-prompt` REPLACES |
| `caveman_full` | NO | `--system-prompt` REPLACES |
| `caveman_full_plus_ultra_directive` | NO | `--system-prompt` REPLACES |
| `hewn_prompt_only` | YES | `--append-system-prompt` ADDS |
| `hewn_full` | YES | `hewn -p` uses `--append-system-prompt` |

**Bias direction (corrected from v5)**:

- Comparing Hewn arms vs `baseline`: both have CLAUDE.md → apples-to-
  apples for output-token savings. Causal claim valid.
- Comparing Hewn arms vs `terse` / `caveman_*`: Hewn has
  CLAUDE.md+hewn prompt = double terseness reinforcement; Caveman has
  only its SKILL.md = single. Hewn output-token savings here may be
  **inflated in Hewn's favor**.
- T0 calibration measures the CLAUDE.md effect on `terse` and
  `caveman_full` directly so REPORT can quote both raw and corrected
  numbers.

## Caveman study findings

(unchanged) `evals/llm_run.py`: 1 run per (prompt, arm), 3 arms,
`--system-prompt`, tiktoken o200k_base. Honest delta = skill vs terse.

## Arms

| ID | System prompt content | Mechanism | T0 | T1a | T1b | T2 | T3 | T4 | T5 |
|---|---|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `baseline` | (none) | `claude -p --model claude-opus-4-7 <prompt>` |   | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `terse` | `"Answer concisely."` | `claude -p --model claude-opus-4-7 --system-prompt <content> <prompt>` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `terse_appended` | same content | `claude -p --model claude-opus-4-7 --append-system-prompt <content> <prompt>` | ✓ |   |   |   |   |   |   |
| `caveman_full` | terse + SKILL.md | `--system-prompt` |   | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `caveman_full_appended` | same content | `--append-system-prompt` | ✓ |   |   |   |   |   |   |
| `caveman_full_plus_ultra_directive` | caveman_full + ultra directive | `--system-prompt` |   |   | ✓ | ✓ | ✓ |   | ✓ |
| `hewn_prompt_only` | hewn_thinking_system_prompt.txt | `--append-system-prompt` |   |   | ✓ | ✓ | ✓ | ✓ | ✓ |
| `hewn_full` | (same content via `--append`) + hook | `bash <repo>/integrations/claude-code/bin/hewn -p ...` |   |   | ✓ | ✓ | ✓ | ✓ | ✓ |

`run.py` reads each arm file and passes its CONTENT (not path) as the
flag value. Smoke test verifies via sentinel.

## Tracks

| ID | Prompt set | # prompts | # runs | # arms | Calls | Purpose | Label |
|----|-----------|-----------|--------|--------|-------|---------|-------|
| **T0** | `short_en.txt` (10) | 10 | 1 | 2 (terse_appended, caveman_full_appended) | 20 | CLAUDE.md asymmetry calibration | Calibration |
| **T1a** | `short_en.txt` | 10 | 1 | 3 (baseline, terse, caveman_full) | 30 | Strict Caveman replication | Caveman parity |
| T1b | same | 10 | 3 | 6 | 180 | Extended | Hewn extension |
| T2 | `vibe_en.txt` (5) | 5 | 3 | 6 | 90 | Vibe / non-tech | Hewn extension |
| T3 | `long_en.txt` (3, ~16k handbook) | 3 | 3 | 6 | 54 | Long context | Hewn extension |
| T4 | `multiturn_en.json` (2 seq × 5 turns) | 10 turns | 2 | 5 | 100 | Drift + isolated hook value | Hewn extension |
| T5 | `expansive_en.txt` (2) | 2 | 2 | 6 | 24 | Honesty: Hewn loses | Hewn extension |

Total: 498 benchmark calls + ~498 judge ≈ 996. Time: 80-115 min.

## Arm-order randomization

(unchanged from v5) Factoradic permutation, seed `"hewn-bench-v1"`,
deterministic across versions/machines. T1a and T0 do NOT randomize
(single-run sequential).

## Multi-turn (T4) session isolation

(unchanged from v5) Explicit `session_id` capture + `--resume <id>` per
turn. Post-run validation no two distinct (seq, run, arm) share
session_id.

## Metrics captured per call

(unchanged from v5)

## Metrics derived

(unchanged from v5) Plus:

- **CLAUDE.md effect on terse** (T0) = `terse_appended.output_tokens
  − terse.output_tokens` per prompt
- **CLAUDE.md effect on caveman_full** (T0) = same for caveman_full
- **Asymmetry-corrected savings** = Hewn-vs-Caveman observational
  delta minus the CLAUDE.md effect quantified in T0 (reported as a
  bracketed range in REPORT, not as a hard number)

## Judge methodology

(unchanged from v5)

## Directory layout

(unchanged from v5; `arms/` adds `terse_appended.txt` and
`caveman_full_appended.txt` — same content as `terse.txt` /
`caveman_full.txt`, separate files for clarity. `snapshots/` adds
`results_T0.json`)

## Execution order

1. Fetch Caveman repo at pinned commit; SHA256 SKILL.md; copy to
   `caveman_source/`.
2. Write harness: `run.py`, `judge.py`, `measure.py`.
3. Write prompts + rubrics + arms (incl. T0 arms).
4. Smoke test 1 — model assertion.
5. Smoke test 2 — sentinel arm (content not path).
6. Smoke test 3 — hewn_full hook delta in `cache_creation_input_tokens`.
7. Smoke test 4 — multi-turn `--resume` system-prompt persistence.
8. **T0 calibration** — measures CLAUDE.md effect on terse/caveman
   compression. Run before claiming Hewn-vs-Caveman numbers.
9. **T1a** — strict Caveman parity; compare to Caveman published numbers
   ±25% tol.
10. T1b, T2, T3, T5 runs.
11. T4 multi-turn run + post-run session-isolation validation.
12. Judge pass on all responses.
13. Generate REPORT.md + evidence/.
14. Commit snapshots + report.

## Honesty commitments

(updated from v5)

- T5 surfaces where Hewn loses; reported prominently.
- T1a labeled "Caveman parity" using exact methodology.
- All raw JSON snapshots committed.
- README labels match-vs-extend explicitly.
- `caveman_full_plus_ultra_directive` NEVER called "Caveman Ultra".
- **CLAUDE.md asymmetry**: Hewn-vs-Caveman / Hewn-vs-terse comparisons
  are observational under asymmetric exposure and may be **inflated in
  Hewn's favor**. Causal claims restricted to Hewn-vs-baseline (both
  arms inherit CLAUDE.md).
- T0 calibration delta reported alongside Hewn-vs-Caveman numbers as a
  contamination context.
- Hook injection cost via `cache_creation_input_tokens` delta.
- T4 hook value = (hewn_prompt_only - hewn_full) delta only.
- Judge failure rate per track.

## Open risks

- T0 calibration measures CLAUDE.md effect on Caveman's prompts only;
  the effect on Hewn's prompt may differ qualitatively (different
  interaction with double-terseness instruction). T0 gives a magnitude
  estimate, not a perfect correction.
- Caveman's published numbers also ran under their own CLAUDE.md
  (presumed); ±25% tolerance for parity.
- Temperature unpinnable; variance via stdev (T1b+).
- `--resume` persistence: validated step 7.
- Rate limits: backoff + idempotent skip.
- `--append-system-prompt` for hewn arms inherits Claude Code default
  system prompt + user CLAUDE.md → larger input. Visible in
  `cache_creation_input_tokens`. Output-token claims contextualized via
  T0.

## What this plan does NOT cover

- Sonnet 4.6
- Cross-provider
- Human user studies
- Languages other than English
- Caveman official `/caveman ultra` skill-runtime invocation
- TTFT
- Pristine isolation (user CLAUDE.md remains active)
- Perfect bias correction (T0 quantifies, doesn't eliminate)
