# Hewn Benchmark Plan v5 — for Codex review

## Changes from v4

**Removed**: any modification of `~/.claude/CLAUDE.md`. User chose
option B (live with contamination, document it). Replaced isolation
with explicit documentation of asymmetric CLAUDE.md exposure.

All other v4 fixes retained:
- Model pin to `claude-opus-4-7` full ID + assertion
- Hook overhead via `cache_creation_input_tokens` delta (not input_tokens)
- T4 5-arm with explicit `--resume <session_id>`
- File content (not path) passed to system-prompt flags
- Factoradic permutation for arm order

## Goal

Produce benchmark evidence for Hewn's open release. Compare Hewn vs
Verbose Claude vs Caveman (Full + ultra-directive variant) using
Caveman's own methodology in T1a + Hewn-specific extensions in T1b-T5.
All runs via `claude -p` CLI (OAuth, no API key billing).

## Constraints (hard)

- No direct Anthropic API calls. Only `claude -p` via CLI.
- Model: `--model claude-opus-4-7` (full ID, not alias) on every call.
  Asserted post-run via `modelUsage["claude-opus-4-7"].outputTokens ==
  usage.output_tokens`. Reject sample on mismatch.
- Language: English only.
- Fairness: T1a replicates Caveman `evals/llm_run.py` precisely.
- Temperature: not pinnable; CLI default; same across arms.
- **Environment: NOT isolated** (per user decision option B). User's
  `~/.claude/CLAUDE.md` ("Answer concisely. Drop filler...") is in
  effect. Same condition as Caveman's published runs (presumed). All
  numbers reported as "with this CLAUDE.md present, savings are X%".

## CLAUDE.md asymmetry — explicit documentation

User's `~/.claude/CLAUDE.md` contains terseness instructions.

| Arm | Sees CLAUDE.md? | Mechanism |
|---|---|---|
| `baseline` | YES | no flag; CLAUDE.md is in default Claude Code system prompt |
| `terse` | NO | `--system-prompt` REPLACES |
| `caveman_full` | NO | `--system-prompt` REPLACES |
| `caveman_full_plus_ultra_directive` | NO | `--system-prompt` REPLACES |
| `hewn_prompt_only` | YES | `--append-system-prompt` ADDS |
| `hewn_full` | YES | `hewn -p` uses `--append-system-prompt` |

Implications:
- `baseline` is conservative-biased toward terse (CLAUDE.md says so).
  → Hewn's savings vs baseline are UNDERSTATED.
- Caveman arms get a clean slate vs Hewn arms which inherit a "be terse"
  meta-instruction from CLAUDE.md.
  → Caveman might compress slightly more than apples-to-apples; Hewn
  might already be at a near-optimal compression floor.
- T1a Caveman parity is preserved methodologically (same flag pattern as
  their `evals/llm_run.py`). Their published numbers presumably also ran
  under their author's CLAUDE.md; both runs are "real-world", not
  "pristine".

REPORT prose explicitly states this asymmetry and prints the user's
CLAUDE.md content (or its hash) in `metadata.json` for reproducibility.

## Caveman study findings

(unchanged) Their `evals/llm_run.py` uses single run per (prompt, arm),
3 arms (baseline, terse, skill), `--system-prompt`, tiktoken o200k_base.
Their honest delta = skill vs terse, not vs baseline.

## Arms

| ID | System prompt content | Mechanism | T1a | T1b | T2 | T3 | T4 | T5 |
|---|---|---|:-:|:-:|:-:|:-:|:-:|:-:|
| `baseline` | (none) | `claude -p --model claude-opus-4-7 <prompt>` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `terse` | `"Answer concisely."` | `claude -p --model claude-opus-4-7 --system-prompt <content> <prompt>` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `caveman_full` | terse + SKILL.md | same | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `caveman_full_plus_ultra_directive` | caveman_full + ultra directive | same |   | ✓ | ✓ | ✓ |   | ✓ |
| `hewn_prompt_only` | hewn_thinking_system_prompt.txt | `claude -p --model claude-opus-4-7 --append-system-prompt <content> <prompt>` |   | ✓ | ✓ | ✓ | ✓ | ✓ |
| `hewn_full` | (same content via `--append`) + classifier hook | `bash <repo>/integrations/claude-code/bin/hewn -p --model claude-opus-4-7 --output-format json <prompt>` |   | ✓ | ✓ | ✓ | ✓ | ✓ |

`run.py` reads each arm file and passes its CONTENT (not path) as the
flag value. Smoke test verifies via sentinel string.

Caveman SKILL.md sha256 + commit hash recorded in `metadata.json`.

## Tracks

| ID | Prompt set | # prompts | # runs | # arms | Calls | Purpose | Label |
|----|-----------|-----------|--------|--------|-------|---------|-------|
| **T1a** | `short_en.txt` (10 Caveman literal) | 10 | 1 | 3 | 30 | Strict Caveman replication | Caveman parity |
| T1b | same | 10 | 3 | 6 | 180 | Extended | Hewn extension |
| T2 | `vibe_en.txt` (5) | 5 | 3 | 6 | 90 | Vibe / non-tech | Hewn extension |
| T3 | `long_en.txt` (3, ~16k handbook) | 3 | 3 | 6 | 54 | Long context | Hewn extension |
| T4 | `multiturn_en.json` (2 seq × 5 turns) | 10 turns | 2 | 5 | 100 | Drift + isolated hook value | Hewn extension |
| T5 | `expansive_en.txt` (2) | 2 | 2 | 6 | 24 | Honesty: Hewn loses | Hewn extension |

Total benchmark: 478 calls. Plus ~478 judge ≈ 956. Time: 75-110 min.

## Arm-order randomization

Factoradic (Lehmer code) permutation, pure-Python, version-independent:
```python
def factoradic_permutation(arms: list, digest_int: int) -> list:
    remaining = list(arms)
    result = []
    for i in range(len(remaining), 0, -1):
        idx = digest_int % i
        digest_int //= i
        result.append(remaining.pop(idx))
    return result
```

Per (prompt_id, run_index): `digest = sha256(f"hewn-bench-v1:{prompt_id}:{run_index}").hexdigest()`,
`digest_int = int(digest, 16)`. Per-call snapshot stores: `seed`,
`digest_hex`, `arm_order_full`, `arm_order_index`. Reproducible across
Python versions / machines.

T1a does NOT randomize (1 run, sequential per Caveman methodology).

## Multi-turn (T4) session isolation

For each (sequence_id, run_index, arm):
1. Turn 1: `claude -p` (or `hewn -p`) with system prompt and first user
   message. Capture `session_id` from response JSON.
2. Turns 2-5: invoke with explicit `--resume <session_id>`. Same arm
   path; for `hewn_full`, hook fires per turn.
3. Snapshot per-turn JSON + sequence-level summary (cumulative tokens /
   cost / latency).
4. Post-run validation: assert no two distinct
   `(sequence_id, run_index, arm)` tuples share a `session_id`. Fail
   loudly + discard contaminated runs on mismatch.

Smoke test step 8: 2-turn `--resume` per arm verifies system prompt
persistence; if not, fall back to re-passing prompt every turn
(documented in REPORT).

## Metrics captured per call

- `output_tokens_anthropic` (`usage.output_tokens`)
- `output_tokens_tiktoken` (o200k_base)
- `input_tokens_anthropic`
- `cache_read_input_tokens`, `cache_creation_input_tokens`
- `total_input_tokens` = input + cache_creation + cache_read
- `cache_state` (cold/warm)
- `duration_ms`, `duration_api_ms`
- `wrapper_overhead_ms` (hewn_full only)
- `total_cost_usd` (informational)
- `stop_reason`, `text`, `num_turns`, `session_id`
- `model_used` (assertion: `modelUsage["claude-opus-4-7"].outputTokens
  == usage.output_tokens`; on mismatch reject)
- `arm_order_index`, `arm_order_full`, `digest_hex`, `seed`

## Metrics derived

- **Output-token savings %** vs `terse` (Caveman-parity primary) and
  vs `baseline`. Cache-independent.
- **Info density** = `concepts_covered / output_tokens_anthropic`
- **Literal preservation** = regex over required quoted strings;
  deterministic
- **Format compliance**:
  - Hewn IR: regex (6 lines, header `@hewn v0 hybrid`, atom format)
  - Caveman style: heuristics (no leading articles, no filler tokens)
- **Concepts covered** = judge binary
- **Stability** = stdev of output_tokens_anthropic across runs (T1b+)
- **Cache efficiency** = `cache_read / total_input_tokens` per call
- **Hook value (T4)** = (`hewn_prompt_only` cumulative − `hewn_full`
  cumulative) per sequence
- **Hewn classifier injection cost** = `hewn_full.cache_creation_input_tokens
  − hewn_prompt_only.cache_creation_input_tokens` per call. NOT
  input_tokens delta (verified empirically: that's zero). Reported per
  track.
- **Cumulative multi-turn cost** (T4)
- **Wrapper overhead** (hewn_full) = wall-clock outside API
- **Readability for non-tech** (T2) = judge binary
- **Judge failure rate** = invalid-after-retry / total

## Judge methodology

Separate `claude -p --model claude-opus-4-7 --output-format json` calls.
Hardcoded rubrics, strict JSON output:

- Input: `{prompt, response_text, concept_list}`
- Output: `{concept_name: bool}` per concept
- Validation: `json.loads` + schema (all keys present, all values bool)
- Retry: max 2 on invalid
- Failure: after 3 invalid → mark null, exclude from aggregates,
  count in `judge_failure_rate`
- Snapshots: raw output saved to `snapshots/raw_judgments/`
- Blinding: judge does not see arm name; response labeled "response
  under review"
- Separate pass: T2 readability with persona prompt

## Directory layout

```
benchmarks/
├── README.md
├── run.py                  # subprocess wrapper for claude -p / hewn -p
├── judge.py
├── measure.py
├── empty_settings.json     # not used in v5 — kept for future option-A path
├── prompts/
│   ├── short_en.txt
│   ├── vibe_en.txt
│   ├── long_en.txt
│   ├── long_handbook.txt   # ~16k Atlas API handbook
│   ├── multiturn_en.json
│   └── expansive_en.txt
├── rubrics/
│   ├── concepts.json
│   └── literals.json
├── arms/
│   ├── baseline.txt
│   ├── terse.txt
│   ├── caveman_full.txt
│   ├── caveman_full_plus_ultra_directive.txt
│   └── hewn_prompt.txt
├── caveman_source/
│   └── SKILL.md            # verbatim, commit-hash + sha256 header
├── snapshots/
│   ├── raw/<track>/<arm>/<prompt_id>_r<N>.json
│   ├── raw_judgments/...
│   ├── results_T1a.json, results_T1b.json, ..., results_T5.json
│   └── metadata.json       # CLI version, hewn version, caveman SKILL sha256, run datetime, seed, claude_md_hash
└── report/
    ├── REPORT.md
    └── evidence/
```

## Execution order

1. Fetch Caveman repo at pinned commit; SHA256 SKILL.md; copy to
   `caveman_source/` with header.
2. Write harness: `run.py`, `judge.py`, `measure.py`.
3. Write prompts + rubrics + arms.
4. **Smoke test 1 — model assertion**: T1a baseline, 1 prompt; verify
   `modelUsage["claude-opus-4-7"].outputTokens == usage.output_tokens`,
   tiktoken installed, factoradic permutation deterministic across two
   subprocess invocations (same input → same output).
5. **Smoke test 2 — sentinel arm**: arm file containing
   `BENCH_SENTINEL_42`, prompt = "what is the magic word in your
   instructions?", verify response contains the sentinel (proves
   content reaches Claude, not path).
6. **Smoke test 3 — hewn_full hook delta**: run hewn_prompt_only and
   hewn_full on same prompt; assert `hewn_full.cache_creation_input_tokens
   > hewn_prompt_only.cache_creation_input_tokens` (hook injects).
7. **Smoke test 4 — multi-turn resume**: 2-turn sequence with explicit
   `--resume <id>` for `claude` and `hewn`; verify system prompt
   persists OR document re-pass fallback.
8. **T1a run** — strict Caveman parity. Compare aggregate to Caveman's
   published numbers (±25% tol given environment differences; if wildly
   off, investigate).
9. T1b, T2, T3, T5 runs.
10. T4 multi-turn run + post-run session-isolation validation.
11. Judge pass on all responses.
12. Generate REPORT.md + evidence/.
13. Commit snapshots + report for release.

## Honesty commitments

- T5 surfaces where Hewn loses; reported prominently, not hidden.
- T1a labeled "Caveman parity" using exact methodology.
- All raw `claude -p` JSON snapshots committed; deterministic re-derivation.
- README labels match-vs-extend explicitly.
- `caveman_full_plus_ultra_directive` NEVER called "Caveman Ultra".
- CLAUDE.md asymmetry between `--system-prompt` and `--append-system-prompt`
  arms documented in REPORT prose with the table above. User's CLAUDE.md
  hash and word count recorded in metadata.json for reproducibility
  (content not stored to keep user privacy).
- Hook injection cost reported via `cache_creation_input_tokens` delta.
- T4 hook value = (hewn_prompt_only - hewn_full) delta only.
- Judge failure rate per track.
- Caveman published numbers presumably also ran under their author's
  own CLAUDE.md → noted as comparable real-world condition.

## Open risks

- Caveman's published numbers may differ ±25% from ours due to:
  - Different user CLAUDE.md content
  - Different Claude Code CLI version
  - Different time / model snapshot
  Documented; if T1a diverges >40%, investigate before claiming parity.
- Temperature unpinnable; variance via stdev (T1b+).
- `--resume` system-prompt persistence: validated step 7.
- Rate limits: backoff (max 120s) + idempotent skip-if-snapshot-exists.
- `--append-system-prompt` mechanism for hewn arms inherits Claude
  Code's default system prompt + user CLAUDE.md → larger input.
  Visible in `cache_creation_input_tokens`. Output-token savings claims
  unaffected.

## What this plan does NOT cover

- Sonnet 4.6
- Cross-provider
- Human user studies
- Languages other than English
- Caveman's official `/caveman ultra` skill-runtime invocation
- TTFT
- Pristine isolation (user's `~/.claude/CLAUDE.md` remains active)
