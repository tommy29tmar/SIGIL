# Hewn vs Verbose Claude vs Caveman — benchmark report

_Generated: 2026-04-22T12:31:45.576896+00:00_
_Model: `claude-opus-4-7`_
_Claude CLI: 2.1.117 (Claude Code)_
_Hewn repo commit: c869a0963512e6941884942d19aa82c5e7fadf80_
_Caveman repo commit pinned: 84cc3c14fa1e10182adaced856e003406ccd250d_
_Caveman SKILL.md sha256: `1762eb9ab0b566d70f51b040dbfd77d1f5be89cfa70da874564bda38c111be7c`_
_Random seed: `hewn-bench-v1`_
_Environment: NOT isolated (option B). User CLAUDE.md hash: `fed963e9ef7e` (169 words)._

## What this report measures

Six arms tested via `claude -p` / `hewn -p` (OAuth subscription, no
direct API key billing):

| Arm | Mechanism |
|---|---|
| `baseline` | `claude -p`, no system prompt |
| `terse` | `claude -p --system-prompt "Answer concisely."` |
| `caveman_full` | `claude -p --system-prompt "Answer concisely.\n\n" + caveman SKILL.md` (vendored from caveman repo) |
| `caveman_full_plus_ultra_directive` | `caveman_full` + appended "Default intensity: ultra…" — **NOT** Caveman's official Ultra (needs skill runtime); our directive-based variant |
| `hewn_prompt_only` | `claude -p --append-system-prompt <hewn prompt>` (no hook) |
| `hewn_full` | `hewn -p` real wrapper (prompt + classifier hook) |

Tracks:

- **T0** — append-vs-replace exposure calibration (10 prompts × 1 run × 4 arms)
- **T1a** — strict Caveman parity, replicates their `evals/llm_run.py` (10 prompts × 1 run × 3 arms)
- **T1b** — extended on Caveman's own prompts (10 × 3 × 6)
- **T2** — vibe / non-tech user prompts (5 × 3 × 6)
- **T3** — long context (~5k handbook + task) (3 × 3 × 6)
- **T4** — multi-turn 5-turn sequences (2 × 2 × 5)
- **T5** — expansive prose (honesty: where Hewn should NOT win) (2 × 2 × 6)

## Honesty box

- **Caveman parity** label applies ONLY to T1a (1 run, 3 arms, tiktoken,
  matches `evals/llm_run.py`).
- **Hewn-vs-baseline** is causal: both arms inherit Claude Code's default
  system prompt + user CLAUDE.md.
- **Hewn-vs-Caveman/terse** is **observational under asymmetric
  exposure**: `--system-prompt` replaces, `--append-system-prompt` adds.
  T0 calibrates the magnitude on `short_en`; T2-T5 reported as raw
  observational only (no per-prompt calibration).
- `caveman_full_plus_ultra_directive` is OUR directive-based variant,
  NOT Caveman's official Ultra (which is invoked via `/caveman ultra`
  through the skill runtime, unavailable in `--system-prompt` mode).
- All raw `claude -p` JSON snapshots committed under
  `benchmarks/snapshots/raw/` for deterministic re-derivation.
- Hewn classifier hook is local Python (no extra API call), but DOES
  inject `additionalContext` → measured as `cache_creation_input_tokens`
  delta, NOT `input_tokens` delta (verified empirically).


## T1a — Strict Caveman parity

Replicates Caveman `evals/llm_run.py` methodology precisely: `claude -p --system-prompt <x>`, **1 run per arm**, 10 prompts vendored verbatim from caveman repo, output tokens via tiktoken `o200k_base` (matches Caveman's `evals/measure.py`).

**Honest delta** per Caveman's own README: skill vs `__terse__`, NOT skill vs baseline.

| Prompt | baseline | terse | caveman_full | savings vs terse |
|---|---:|---:|---:|---:|
| `cors-errors` | 306 | 336 | 129 | 62% |
| `debounce-search` | 127 | 137 | 32 | 77% |
| `explain-db-pool` | 429 | 394 | 96 | 76% |
| `fix-node-memory-leak` | 319 | 307 | 223 | 27% |
| `git-rebase-vs-merge` | 191 | 131 | 49 | 63% |
| `hash-table-collisions` | 332 | 267 | 83 | 69% |
| `queue-vs-topic` | 141 | 162 | 60 | 63% |
| `react-rerender-parent` | 181 | 149 | 84 | 44% |
| `sql-explain` | 253 | 299 | 114 | 62% |
| `tcp-vs-udp` | 98 | 136 | 73 | 46% |
| **median** | | | | **62%** |
| **mean** | | | | **59%** |
| **range** | | | | **27% – 77%** |
| **stdev** | | | | **15%** |

Totals: baseline 2377 / terse 2318 (`2%` vs baseline) / caveman_full 943 (`59%` vs terse, `60%` vs baseline).

## T0 — Append-vs-replace exposure calibration

Measures the output-token delta between `--system-prompt` (replace) and `--append-system-prompt` (add to default + CLAUDE.md). Positive delta = appending makes output **longer**. Negative = appending compresses **more**.

Both arms use the same content (`Answer concisely.` for terse, same + Caveman SKILL.md for caveman_full). Only the flag differs.

| Prompt | terse (replace) | terse (append) | Δ tokens | caveman (replace) | caveman (append) | Δ tokens |
|---|---:|---:|---:|---:|---:|---:|
| `cors-errors` | 532 | 500 | -32 | 204 | 191 | -13 |
| `debounce-search` | 245 | 255 | +10 | 62 | 178 | +116 |
| `explain-db-pool` | 529 | 546 | +17 | 217 | 208 | -9 |
| `fix-node-memory-leak` | 469 | 587 | +118 | 410 | 492 | +82 |
| `git-rebase-vs-merge` | 263 | 150 | -113 | 73 | 169 | +96 |
| `hash-table-collisions` | 331 | 315 | -16 | 181 | 228 | +47 |
| `queue-vs-topic` | 235 | 262 | +27 | 124 | 182 | +58 |
| `react-rerender-parent` | 388 | 356 | -32 | 209 | 176 | -33 |
| `sql-explain` | 421 | 523 | +102 | 236 | 230 | -6 |
| `tcp-vs-udp` | 175 | 172 | -3 | 134 | 242 | +108 |
| **median** | | | **+3** | | | **+52** |
| **mean** | | | **+7** | | | **+44** |

_Interpretation: a positive median delta means stock Caveman/terse (replace) numbers underestimate compression vs. Hewn arms (append); observed Hewn-vs-Caveman savings on T1b/T2-T5 are inflated by approximately this magnitude._

## T1b — Extended short_en (Hewn extension)

All 6 arms × 3 runs × 10 prompts. Median across runs per (arm, prompt). Output tokens from Anthropic `usage.output_tokens` (ground truth, not tiktoken approximation).

Cell values: median(output_tokens). `hewn_full` includes the classifier hook overhead (extra `cache_creation_input_tokens`, see appendix).

### Output tokens per prompt × arm

| Prompt | baseline | terse | caveman_full | caveman+ultra | hewn_prompt_only | hewn_full |
|---|---:|---:|---:|---:|---:|---:|
| `cors-errors` | 423 | 432 | 248 | 219 | 732 | 175 |
| `debounce-search` | 225 | 212 | 61 | 53 | 253 | 88 |
| `explain-db-pool` | 661 | 583 | 98 | 62 | 694 | 259 |
| `fix-node-memory-leak` | 701 | 594 | 442 | 319 | 742 | 59 |
| `git-rebase-vs-merge` | 218 | 248 | 103 | 102 | 293 | 112 |
| `hash-table-collisions` | 309 | 324 | 145 | 178 | 513 | 231 |
| `queue-vs-topic` | 190 | 191 | 128 | 122 | 304 | 135 |
| `react-rerender-parent` | 315 | 388 | 140 | 131 | 489 | 162 |
| `sql-explain` | 266 | 414 | 178 | 118 | 588 | 120 |
| `tcp-vs-udp` | 181 | 171 | 125 | 95 | 164 | 151 |
| **mean** | **349** | **356** | **167** | **140** | **477** | **149** |

### Hewn-vs-comparator savings — `(appended, observed)` pair

Cross-track join: `appended` side from T0 single run; `observed` side and `hewn_full` from T1b median-of-3-runs.

**vs Caveman full** — savings = `comparator − hewn_full` tokens; positive = Hewn fewer tokens.

| Prompt | observed (T1b stock) | appended (T0 calibrated) |
|---|---:|---:|
| `cors-errors` | +73 | +16 |
| `debounce-search` | -27 | +90 |
| `explain-db-pool` | -161 | -51 |
| `fix-node-memory-leak` | +383 | +433 |
| `git-rebase-vs-merge` | -9 | +57 |
| `hash-table-collisions` | -86 | -3 |
| `queue-vs-topic` | -7 | +47 |
| `react-rerender-parent` | -22 | +14 |
| `sql-explain` | +58 | +110 |
| `tcp-vs-udp` | -26 | +91 |
| **median** | **-15** | **+52** |
| **mean** | **+17** | **+80** |

**vs terse** — same shape:

| Prompt | observed (T1b stock) | appended (T0 calibrated) |
|---|---:|---:|
| `cors-errors` | +257 | +325 |
| `debounce-search` | +124 | +167 |
| `explain-db-pool` | +324 | +287 |
| `fix-node-memory-leak` | +535 | +528 |
| `git-rebase-vs-merge` | +136 | +38 |
| `hash-table-collisions` | +93 | +84 |
| `queue-vs-topic` | +56 | +127 |
| `react-rerender-parent` | +226 | +194 |
| `sql-explain` | +294 | +403 |
| `tcp-vs-udp` | +20 | +21 |
| **median** | **+181** | **+180** |
| **mean** | **+206** | **+217** |

### Hewn-vs-baseline (causal — both arms inherit default+CLAUDE.md)

| Prompt | baseline | hewn_full | savings |
|---|---:|---:|---:|
| `cors-errors` | 423 | 175 | 59% |
| `debounce-search` | 225 | 88 | 61% |
| `explain-db-pool` | 661 | 259 | 61% |
| `fix-node-memory-leak` | 701 | 59 | 92% |
| `git-rebase-vs-merge` | 218 | 112 | 49% |
| `hash-table-collisions` | 309 | 231 | 25% |
| `queue-vs-topic` | 190 | 135 | 29% |
| `react-rerender-parent` | 315 | 162 | 49% |
| `sql-explain` | 266 | 120 | 55% |
| `tcp-vs-udp` | 181 | 151 | 17% |
| **median** | | | **52%** |
| **mean** | | | **49%** |
| **range** | | | **17% – 92%** |

### Stability (stdev of output_tokens across 3 runs per arm × prompt)

| Arm | mean stdev across prompts |
|---|---:|
| baseline | 54.7 |
| terse | 59.8 |
| caveman_full | 36.7 |
| caveman_full_plus_ultra_directive | 18.6 |
| hewn_prompt_only | 61.3 |
| hewn_full | 41.3 |

## T2 — Vibe / non-tech user prompts

3 runs × 5 prompts × 6 arms. Median across runs per (arm, prompt). Hewn-vs-Caveman/terse numbers are **observational under asymmetric exposure** (no T0-style appended-comparator calibration on these prompts).

### Output tokens per prompt × arm (median)

| Prompt | baseline | terse | caveman_full | caveman+ultra | hewn_prompt_only | hewn_full |
|---|---:|---:|---:|---:|---:|---:|
| `add-search-bar` | 197 | 117 | 266 | 199 | 339 | 51 |
| `login-button-broken` | 227 | 93 | 122 | 106 | 737 | 56 |
| `make-website-faster` | 43 | 94 | 59 | 131 | 626 | 48 |
| `spaghetti-code` | 442 | 422 | 427 | 451 | 564 | 65 |
| `typeerror-undefined-map` | 254 | 277 | 116 | 105 | 361 | 71 |
| **mean** | **233** | **201** | **198** | **198** | **525** | **58** |

### Hewn-vs-baseline (causal — both arms inherit default+CLAUDE.md)

| Prompt | baseline | hewn_full | savings |
|---|---:|---:|---:|
| `add-search-bar` | 197 | 51 | 74% |
| `login-button-broken` | 227 | 56 | 75% |
| `make-website-faster` | 43 | 48 | −12% |
| `spaghetti-code` | 442 | 65 | 85% |
| `typeerror-undefined-map` | 254 | 71 | 72% |
| **median** | | | **74%** |
| **mean** | | | **59%** |

### Wall-clock latency (median, ms)

| Prompt | baseline | terse | caveman_full | caveman+ultra | hewn_prompt_only | hewn_full |
|---|---:|---:|---:|---:|---:|---:|
| `add-search-bar` | 5397 | 3948 | 6454 | 5872 | 6393 | 3595 |
| `login-button-broken` | 4985 | 3396 | 4849 | 4063 | 14557 | 5039 |
| `make-website-faster` | 2479 | 3412 | 4133 | 4344 | 11769 | 4362 |
| `spaghetti-code` | 10576 | 10273 | 10834 | 12322 | 12766 | 4337 |
| `typeerror-undefined-map` | 7046 | 5795 | 4021 | 4078 | 7562 | 5602 |

## T3 — Long context (~5k handbook prefix)

3 runs × 3 prompts × 6 arms. Median across runs per (arm, prompt). Hewn-vs-Caveman/terse numbers are **observational under asymmetric exposure** (no T0-style appended-comparator calibration on these prompts).

### Output tokens per prompt × arm (median)

| Prompt | baseline | terse | caveman_full | caveman+ultra | hewn_prompt_only | hewn_full |
|---|---:|---:|---:|---:|---:|---:|
| `body-size-rollout-plan` | 1712 | 1548 | 1389 | 1630 | 1783 | 1758 |
| `rate-limit-xff-review` | 146 | 100 | 72 | 54 | 201 | 4457 |
| `transfer-handler-review` | 772 | 801 | 532 | 560 | 945 | 1205 |
| **mean** | **877** | **816** | **664** | **748** | **976** | **2473** |

### Hewn-vs-baseline (causal — both arms inherit default+CLAUDE.md)

| Prompt | baseline | hewn_full | savings |
|---|---:|---:|---:|
| `body-size-rollout-plan` | 1712 | 1758 | −3% |
| `rate-limit-xff-review` | 146 | 4457 | −2953% |
| `transfer-handler-review` | 772 | 1205 | −56% |
| **median** | | | **−56%** |
| **mean** | | | **−1004%** |

### Wall-clock latency (median, ms)

| Prompt | baseline | terse | caveman_full | caveman+ultra | hewn_prompt_only | hewn_full |
|---|---:|---:|---:|---:|---:|---:|
| `body-size-rollout-plan` | 31892 | 26159 | 25480 | 30524 | 32756 | 33747 |
| `rate-limit-xff-review` | 4864 | 2556 | 2968 | 2645 | 4990 | 78529 |
| `transfer-handler-review` | 12623 | 13293 | 9240 | 9540 | 17180 | 22537 |

## T4 — Multi-turn (drift + isolated hook value)

Each (arm, sequence, run) replays 5 user turns via explicit `--resume <session_id>`. Cumulative output tokens summed across all 5 turns.

### Cumulative output tokens per sequence × arm (median across 2 runs)

| Sequence | baseline | terse | caveman_full | hewn_prompt_only | hewn_full |
|---|---:|---:|---:|---:|---:|
| `debug-prod-incident` | 5550 | 2255 | 1612 | 5431 | 719 |
| `design-feature` | 8841 | 5585 | 6840 | 10303 | 4956 |

### Hook value — `(hewn_prompt_only − hewn_full)` cumulative deltas

Positive Δ output_tokens = hook makes hewn_full produce **fewer** tokens. Positive Δ cache_creation = hook injects extra `additionalContext` (expected; classifier injection is the hook's job).

| Sequence | Δ output_tokens (median) | Δ cache_creation_input (median) |
|---|---:|---:|
| `debug-prod-incident` | +4712 | -414 |
| `design-feature` | +5347 | -97 |

### Session-id isolation check

OK — no session_id collision across distinct (arm, seq, run) tuples.

## T5 — Expansive prose (honesty: Hewn should NOT win)

2 runs × 2 prompts × 6 arms. Median across runs per (arm, prompt). Hewn-vs-Caveman/terse numbers are **observational under asymmetric exposure** (no T0-style appended-comparator calibration on these prompts).

### Output tokens per prompt × arm (median)

| Prompt | baseline | terse | caveman_full | caveman+ultra | hewn_prompt_only | hewn_full |
|---|---:|---:|---:|---:|---:|---:|
| `outage-apology-email` | 481 | 483 | 538 | 450 | 457 | 481 |
| `smart-drafts-release-note` | 13 | 10 | 12 | 14 | 17 | 15 |
| **mean** | **247** | **247** | **275** | **232** | **237** | **248** |

### Hewn-vs-baseline (causal — both arms inherit default+CLAUDE.md)

| Prompt | baseline | hewn_full | savings |
|---|---:|---:|---:|
| `outage-apology-email` | 481 | 481 | 0% |
| `smart-drafts-release-note` | 13 | 15 | −11% |
| **median** | | | **−6%** |
| **mean** | | | **−6%** |

### Wall-clock latency (median, ms)

| Prompt | baseline | terse | caveman_full | caveman+ultra | hewn_prompt_only | hewn_full |
|---|---:|---:|---:|---:|---:|---:|
| `outage-apology-email` | 11520 | 10397 | 11910 | 11079 | 10673 | 12141 |
| `smart-drafts-release-note` | 1680 | 3024 | 1779 | 1629 | 1978 | 2429 |

## Quality — concepts coverage, literals, format compliance, judge failure rates

### T1a

| Arm | concepts covered (mean ratio) | literals preserved (mean) | IR valid (rate) | filler/100w (mean) | concept-judge failures | readability (mean true ratio) |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 95% | 100% | 0% | 0.1 | 0 | — |
| caveman_full | 91% | 100% | 0% | 0.0 | 0 | — |
| terse | 95% | 100% | 0% | 0.1 | 0 | — |

### T1b

| Arm | concepts covered (mean ratio) | literals preserved (mean) | IR valid (rate) | filler/100w (mean) | concept-judge failures | readability (mean true ratio) |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 96% | 93% | 0% | 0.2 | 0 | — |
| caveman_full | 95% | 93% | 0% | 0.0 | 0 | — |
| caveman_full_plus_ultra_directive | 93% | 80% | 0% | 0.1 | 0 | — |
| hewn_full | 91% | 100% | 10% | 0.0 | 0 | — |
| hewn_full_v1 | 96% | 100% | 10% | 0.2 | 0 | — |
| hewn_full_v2 | 38% | 20% | 100% | 0.0 | 0 | — |
| hewn_prompt_only | 99% | 100% | 0% | 0.1 | 0 | — |
| hewn_prompt_only_v1 | 96% | 93% | 0% | 0.2 | 0 | — |
| hewn_prompt_only_v2 | 98% | 100% | 0% | 0.2 | 0 | — |
| terse | 96% | 100% | 0% | 0.2 | 0 | — |

### T2

| Arm | concepts covered (mean ratio) | literals preserved (mean) | IR valid (rate) | filler/100w (mean) | concept-judge failures | readability (mean true ratio) |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 47% | 50% | 0% | 0.1 | 0 | 78% |
| caveman_full | 78% | 33% | 0% | 0.0 | 0 | 20% |
| caveman_full_plus_ultra_directive | 83% | 17% | 0% | 0.1 | 0 | 28% |
| hewn_full | 63% | 50% | 0% | 0.0 | 0 | 20% |
| hewn_full_v1 | 70% | 50% | 0% | 0.8 | 0 | 35% |
| hewn_full_v2 | 53% | 50% | 0% | 0.3 | 0 | 47% |
| hewn_full_v3 | 53% | 50% | 0% | 0.0 | 0 | 37% |
| hewn_prompt_only | 62% | 50% | 0% | 0.5 | 0 | 48% |
| hewn_prompt_only_v1 | 45% | 50% | 0% | 0.3 | 0 | 60% |
| hewn_prompt_only_v2 | 55% | 50% | 0% | 0.1 | 0 | 72% |
| hewn_prompt_only_v3 | 48% | 50% | 0% | 0.3 | 0 | 68% |
| terse | 65% | 50% | 0% | 0.4 | 0 | 43% |

### T3

| Arm | concepts covered (mean ratio) | literals preserved (mean) | IR valid (rate) | filler/100w (mean) | concept-judge failures | readability (mean true ratio) |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 5% | 0% | 0% | 0.5 | 0 | — |
| caveman_full | 5% | 0% | 0% | 0.0 | 0 | — |
| caveman_full_plus_ultra_directive | 5% | 0% | 0% | 0.0 | 0 | — |
| hewn_full | 39% | 33% | 0% | 0.1 | 0 | — |
| hewn_full_v1 | 27% | 42% | 0% | 0.1 | 0 | — |
| hewn_full_v2 | 12% | 8% | 0% | 0.0 | 0 | — |
| hewn_prompt_only | 6% | 0% | 0% | 0.0 | 0 | — |
| hewn_prompt_only_v1 | 5% | 0% | 0% | 0.0 | 0 | — |
| hewn_prompt_only_v2 | 5% | 0% | 0% | 0.1 | 0 | — |
| terse | 5% | 0% | 0% | 0.0 | 0 | — |

### T4

| Arm | concepts covered (mean ratio) | literals preserved (mean) | IR valid (rate) | filler/100w (mean) | concept-judge failures | readability (mean true ratio) |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 100% | — | 0% | 0.4 | 0 | — |
| caveman_full | 98% | — | 0% | 0.1 | 0 | — |
| hewn_full | 82% | — | 20% | 0.0 | 0 | — |
| hewn_full_v1 | 100% | — | 20% | 0.1 | 0 | — |
| hewn_full_v2 | 85% | — | 20% | 0.1 | 0 | — |
| hewn_prompt_only | 98% | — | 0% | 0.2 | 0 | — |
| hewn_prompt_only_v1 | 95% | — | 0% | 0.3 | 0 | — |
| hewn_prompt_only_v2 | 98% | — | 0% | 0.3 | 0 | — |
| terse | 95% | — | 0% | 0.3 | 0 | — |

### T5

| Arm | concepts covered (mean ratio) | literals preserved (mean) | IR valid (rate) | filler/100w (mean) | concept-judge failures | readability (mean true ratio) |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 0% | 0% | 0% | 0.4 | 0 | — |
| caveman_full | 0% | 0% | 0% | 0.3 | 0 | — |
| caveman_full_plus_ultra_directive | 0% | 0% | 0% | 0.2 | 0 | — |
| hewn_full | 0% | 0% | 0% | 0.2 | 0 | — |
| hewn_full_v1 | 0% | 0% | 0% | 0.5 | 0 | — |
| hewn_full_v2 | 0% | 0% | 0% | 0.2 | 0 | — |
| hewn_prompt_only | 0% | 0% | 0% | 0.5 | 0 | — |
| hewn_prompt_only_v1 | 0% | 0% | 0% | 0.3 | 0 | — |
| hewn_prompt_only_v2 | 0% | 0% | 0% | 3.5 | 0 | — |
| terse | 0% | 0% | 0% | 0.4 | 0 | — |
