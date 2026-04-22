# Hewn Benchmark Plan v3 — for Codex review

## Changes from v2 (addressing all 5 new objections)

1. **[H1 fix v3]** Pin to full model ID `--model claude-opus-4-7`
   (verified executable). Assertion: `modelUsage["claude-opus-4-7"]
   .outputTokens` must equal `usage.output_tokens`. If only helper-model
   tokens appear (e.g. only haiku), reject sample.
2. **[H2 fix v3]** Hewn classifier hook documented correctly: NO extra
   API call (Python local), but DOES inject `[TURN CLASSIFICATION:
   <route>]` as `additionalContext` → small input-token addition. We
   measure this naturally via `input_tokens_anthropic`. Report adds
   explicit "hewn_full input-token overhead vs hewn_prompt_only" line
   per track.
3. **[H3 fix v3]** T4 multi-turn uses explicit `session_id` capture +
   `--resume <id>` per turn (no bare `--resume` / `-c`). Smoke test
   verifies isolation across (sequence, run, arm) for both `claude` and
   `hewn`. Documented contamination check: post-run, scan all snapshots
   to confirm no two distinct (seq, run, arm) combos share a session_id.
4. **[M4 fix v3]** T4 expanded to 5 arms by adding `hewn_prompt_only`
   (same `--append-system-prompt` path as `hewn_full` minus the hook).
   Now hook value = (hewn_prompt_only - hewn_full) delta, isolating the
   hook's contribution. T4 arms: baseline, terse, caveman_full,
   hewn_prompt_only, hewn_full = 5 arms.
5. **[M5 fix v3]** Arm-order randomization uses
   `sha256(f"{SEED}:{prompt_id}:{run_index}").hexdigest()` mod n!. Seed
   recorded in `snapshots/metadata.json`. Computed arm order persisted
   per call in `arm_order_index` field (already in v2 spec). Stable
   across processes / Python versions.

## Goal

Produce benchmark evidence for Hewn's open release. Compare Hewn vs
Verbose Claude vs Caveman (Full + ultra-directive variant) using
Caveman's own methodology precisely replicated in T1a plus Hewn-specific
extensions in T1b-T5. All runs via `claude -p` CLI (OAuth subscription,
no API key billing).

## Constraints (hard)

- **No direct Anthropic API calls.** Only `claude -p` via CLI.
- **Model:** `--model claude-opus-4-7` on every call (full ID, not
  alias). Asserted post-run via `modelUsage["claude-opus-4-7"].
  outputTokens == usage.output_tokens`. Reject sample on mismatch.
- **Language:** English only.
- **Fairness:** T1a replicates Caveman `evals/llm_run.py` methodology
  precisely (1 run, 3 arms, tiktoken o200k_base). T1a numbers labeled
  "Caveman parity"; all other tracks labeled "Hewn extension".
- **Temperature:** not controllable via `claude -p`. Uses CLI default.
  Same across all arms → fair within comparison. Variance reflected in
  stdev (T1b+).

## Caveman study findings (what they actually measure)

From https://github.com/juliusbrussee/caveman:

- `evals/llm_run.py`: **1 run per (prompt, arm)**, `claude -p
  --system-prompt <x>`, tiktoken `o200k_base` for output tokens,
  reports median/mean/min/max/stdev **across prompts**. Arms:
  `__baseline__` (no sys), `__terse__` ("Answer concisely."),
  `<skill>` ("Answer concisely.\n\n" + SKILL.md).
- `benchmarks/run.py`: uses Anthropic SDK (forbidden for us). Multiple
  trials. Not replicated here.
- **Not measured by Caveman:** latency, fidelity, quality rubric,
  cross-run variance, intensity variants (ultra/lite).

Honest delta per Caveman's own README: `<skill>` vs `__terse__`, NOT
`<skill>` vs `__baseline__`.

## Arms

| ID | System prompt | Mechanism | Notes |
|---|---|---|---|
| `baseline` | (none) | `claude -p --model claude-opus-4-7 <prompt>` | T1a included |
| `terse` | `"Answer concisely."` | `claude -p --model claude-opus-4-7 --system-prompt <file> <prompt>` | T1a included |
| `caveman_full` | `terse + SKILL.md` (verbatim from caveman repo, sha256 pinned) | same | T1a included |
| `caveman_full_plus_ultra_directive` | `caveman_full + "\n\nDefault intensity: ultra for every response."` | same | T1b+ only. NOT official Caveman Ultra. |
| `hewn_prompt_only` | `hewn_thinking_system_prompt.txt` verbatim | `claude -p --model claude-opus-4-7 --append-system-prompt <file> <prompt>` | no hook. Same `--append` path as `hewn_full` minus hook. T1b+ and T4. |
| `hewn_full` | (same file, via `--append`) + Python classifier hook | `hewn -p --model claude-opus-4-7 --output-format json <prompt>` | T1b+ and T4. Real wrapper. Classifier is local Python (no API call), but injects `additionalContext` (extra input tokens, measured). |

Note on `hewn_prompt_only` mechanism: changed from `--system-prompt` to
`--append-system-prompt` so it shares the exact path with `hewn_full`
(only difference = no hook). This isolates the hook's contribution.
Apples-to-apples with `caveman_full` is therefore **less direct**
(caveman uses `--system-prompt` which replaces; hewn_prompt_only uses
`--append` which adds to default Claude Code system prompt). Reported
honestly in REPORT: T1a/T1b strict apples-to-apples comparisons exclude
`hewn_prompt_only`; full comparison treats hewn arms as having extra
default-system-prompt context (which inflates input_tokens but should
not affect output_tokens-savings claims).

Caveman SKILL.md pinned to commit hash from cloned repo (recorded in
`snapshots/metadata.json`).

## Tracks

| ID | Prompt set | # prompts | # runs | Arms | Purpose | Label |
|----|-----------|-----------|--------|------|---------|-------|
| **T1a** | `short_en.txt` — 10 literal Caveman prompts | 10 | **1** | **3** (baseline, terse, caveman_full) | **Strict Caveman replication** | Caveman parity |
| **T1b** | same `short_en.txt` | 10 | 3 | all 6 | Extended comparison on Caveman's own turf | Hewn extension |
| T2 | `vibe_en.txt` — 5 non-technical user prompts | 5 | 3 | all 6 | Vibe coding / non-tech users | Hewn extension |
| T3 | `long_en.txt` — 3 prompts with ~16k-token handbook prefix | 3 | 3 | all 6 | Long context | Hewn extension |
| T4 | `multiturn_en.json` — 2 sequences × 5 turns | 10 turns | 2 | **5** (baseline, terse, caveman_full, hewn_prompt_only, hewn_full) | Drift + isolated hook value | Hewn extension |
| T5 | `expansive_en.txt` — 2 prompts asking for polished prose | 2 | 2 | all 6 | Honesty: where Hewn should NOT compress | Hewn extension |

Total benchmark calls: 10·1·3 + 10·3·6 + 5·3·6 + 3·3·6 + 10·2·5 + 2·2·6
= 30 + 180 + 90 + 54 + 100 + 24 = **478 benchmark calls**. Plus ~478
judge calls = ~956 total. Time estimate: 75-110 min on Opus 4.7.

## Arm-order randomization

Per (prompt_id, run_index) we compute a deterministic permutation of
arms using:

```python
import hashlib
seed = "hewn-bench-v1"  # recorded in metadata.json
key = f"{seed}:{prompt_id}:{run_index}"
digest_int = int(hashlib.sha256(key.encode()).hexdigest(), 16)
# use digest_int as seed for random.Random for permutation
```

Stable across processes, Python versions, machines. Seed recorded.
Computed arm order persisted as `arm_order_index` per call snapshot.

T1a does NOT randomize (single run; matches Caveman's sequential order).

## Multi-turn (T4) session isolation

For each (sequence_id, run_index, arm):
1. Turn 1: invoke `claude -p` (or `hewn -p`) with system prompt and
   first user message. Capture `session_id` from JSON response.
2. Turns 2-5: invoke with `--resume <session_id>` (explicit ID, never
   bare). Same arm path; for `hewn_full`, hook fires per turn naturally.
3. Snapshot per-turn JSON + sequence-level summary (cumulative tokens /
   cost / latency).
4. **Post-run validation**: scan all snapshots; assert no two distinct
   `(sequence_id, run_index, arm)` tuples share a `session_id`. If they
   do, fail loudly and discard contaminated runs.

Does `--system-prompt` / `--append-system-prompt` persist across
`--resume`? **Smoke test before T4** (single 2-turn trial per arm). If
NOT persisted, fall back to re-passing the system prompt every turn
(documented in REPORT).

## Metrics captured per call

All from `claude -p --output-format json`:

- `output_tokens_anthropic` (ground truth from `usage.output_tokens`)
- `output_tokens_tiktoken` (tiktoken `o200k_base`, Caveman-parity)
- `input_tokens_anthropic` (`usage.input_tokens`)
- `cache_read_input_tokens`, `cache_creation_input_tokens`
- `cache_state`: "cold" if `cache_read == 0` else "warm"
- `duration_ms` (wall-clock, CLI→CLI)
- `duration_api_ms` (API-side)
- `wrapper_overhead_ms` (`hewn_full` only: `time_total - duration_api_ms`)
- `total_cost_usd` (informational, not billed on Max sub)
- `stop_reason`
- `text` (full response)
- `num_turns`
- `model_used` — assertion: `modelUsage["claude-opus-4-7"].outputTokens
  == usage.output_tokens`; on mismatch, reject sample
- `arm_order_index`
- `session_id` (for T4 isolation)

## Metrics derived / computed

- **Output-token savings %** vs `__terse__` (Caveman-parity primary)
  and vs `baseline` (both reported). Cache-independent.
- **Info density** = `concepts_covered / output_tokens_anthropic`
- **Literal preservation** = regex check for required quoted strings in
  response; deterministic
- **Format compliance**:
  - Hewn IR: regex validation (6 lines, header `@hewn v0 hybrid`, atom
    format per `hewn_thinking_system_prompt.txt`)
  - Caveman style: heuristics (no leading articles, no filler tokens)
- **Concepts covered** = judge binary per concept from hardcoded rubric
- **Stability** = stdev of `output_tokens_anthropic` across runs per
  (prompt, arm); T1b+ only
- **Cache efficiency** = `cache_read / (cache_read + cache_creation +
  input_tokens_anthropic)` per call; reported with warm/cold flag
- **Hook value (T4)** = (hewn_prompt_only metrics - hewn_full metrics)
  delta per turn
- **Hewn input-token overhead** = `hewn_full.input_tokens_anthropic -
  hewn_prompt_only.input_tokens_anthropic` per call. Reflects classifier
  injection cost. Reported per track.
- **Cumulative multi-turn cost** (T4) = sum of per-turn costs/tokens
- **Wrapper overhead** (`hewn_full`) = wall-clock outside API
- **Readability for non-tech** (T2) = judge persona binary
- **Judge failure rate** = fraction of judge calls returning invalid
  JSON after retries; excluded from concept/readability aggregates

## Judge methodology

Separate `claude -p --model claude-opus-4-7 --output-format json` calls
with hardcoded rubrics:

- **Input to judge**: `{prompt, response_text, concept_list}` as JSON
  in user message. System prompt instructs strict JSON output and
  blinds arm identity.
- **Output**: strict JSON `{concept_name: bool}` for each concept.
- **Validation**: `json.loads` + schema check (all required keys, all
  values boolean).
- **Retry**: up to 2 retries on schema failure.
- **Failure handling**: after 3 invalid outputs, mark judge result as
  `null` and exclude from aggregates. Track in `judge_failure_rate`.
- **Snapshots**: raw judge output saved to
  `snapshots/raw_judgments/<track>/<arm>/<prompt_id>_r<N>.json`.
- **Blinding**: judge does NOT see arm name. Response labeled "response
  under review".
- **Separate pass** for "non-tech readability" (T2 only) with persona
  prompt.

## Directory layout

```
benchmarks/
├── README.md               # methodology, attribution, match-vs-extend
├── run.py                  # subprocess wrapper for claude -p / hewn -p
├── judge.py                # concepts + readability + retry logic
├── measure.py              # reads snapshots, outputs REPORT.md
├── prompts/
│   ├── short_en.txt        # 10 Caveman literal (attribution header)
│   ├── vibe_en.txt
│   ├── long_en.txt
│   ├── long_handbook.txt   # ~16k Atlas API handbook
│   ├── multiturn_en.json   # 2 sequences of 5 turns
│   └── expansive_en.txt
├── rubrics/
│   ├── concepts.json       # {prompt_id: [required_concepts]}
│   └── literals.json       # {prompt_id: [required_literal_strings]}
├── arms/
│   ├── baseline.txt        (empty)
│   ├── terse.txt
│   ├── caveman_full.txt
│   ├── caveman_full_plus_ultra_directive.txt
│   └── hewn_prompt.txt
├── caveman_source/
│   └── SKILL.md            # verbatim from juliusbrussee/caveman, commit-hash header
├── snapshots/
│   ├── raw/<track>/<arm>/<prompt_id>_r<N>.json   # full claude -p JSON
│   ├── raw_judgments/...
│   ├── results_T1a.json, results_T1b.json, ..., results_T5.json
│   └── metadata.json       # claude CLI version, caveman SKILL sha256, hewn version, run datetime, randomization seed
└── report/
    ├── REPORT.md
    └── evidence/           # 6-8 side-by-side full-text examples
```

## Execution order

1. Fetch Caveman repo at pinned commit; compute SHA256 of SKILL.md;
   copy to `benchmarks/caveman_source/SKILL.md` with header.
2. Write harness (`run.py`, `judge.py`, `measure.py`).
3. Write prompts + rubrics + arms files.
4. **Smoke test**: T1a baseline arm only, 1 prompt, verify:
   - JSON parses, `modelUsage["claude-opus-4-7"].outputTokens ==
     usage.output_tokens`
   - tiktoken install works
   - Arm-order permutation deterministic across processes
5. **Smoke test `hewn_full`**: verify `hewn -p --output-format json
   --model claude-opus-4-7 <prompt>` returns valid JSON, hook fires,
   classifier injects `[TURN CLASSIFICATION: <route>]` (visible in
   `usage.input_tokens` delta vs `hewn_prompt_only`).
6. **Smoke test multi-turn**: 2-turn sequence with explicit
   `session_id` capture + `--resume <id>` for both `claude` and `hewn`.
   Verify system prompt persists; if not, document fallback (re-pass
   per turn).
7. **T1a run** — strict Caveman parity. Compare aggregate to Caveman's
   own README numbers (±15% tolerance; if wildly off, investigate).
8. T1b, T2, T3, T5 (in order).
9. T4 multi-turn run with session-isolation validation pass.
10. Judge pass on all captured responses.
11. Generate `REPORT.md` + `evidence/` dir.
12. Commit snapshots + report.

## Honesty commitments

- T5 adversarial track surfaces where Hewn should NOT win (expansive
  prose). Reported prominently.
- T1a numbers labeled "Caveman parity" using their exact methodology.
- All raw JSON snapshots committed (deterministic re-derivation).
- README labels match-vs-extend explicitly.
- `caveman_full_plus_ultra_directive` arm NEVER called "Caveman Ultra"
  in prose.
- `hewn_prompt_only` and `hewn_full` use `--append-system-prompt`, not
  `--system-prompt`. This means they inherit Claude Code's default
  system prompt → larger input. Documented; output-token-savings claims
  unaffected.
- Judge failure rate reported in every track's table.
- T4 hook-value claim attributed to (hewn_prompt_only - hewn_full)
  delta, not (caveman_full - hewn_full).

## Open risks

- Temperature not pinnable on `claude -p`. Variance reflected in stdev.
- `--resume` + system-prompt persistence: validated in step 6 smoke
  test. Fallback documented.
- Claude Code internal helper-model usage (haiku) varies by `--system-
  prompt` vs `--append-system-prompt`. Recorded per call in
  `modelUsage` field.
- Rate limits on Max subscription: exponential backoff (max 120s),
  resume from last snapshot. Harness idempotent (skip if
  `raw/.../<prompt_id>_r<N>.json` exists).
- `--append-system-prompt` mechanism for hewn arms means input tokens
  not directly comparable to `--system-prompt` arms. Output-token
  comparisons unaffected.

## What this plan does NOT cover (deliberately)

- Sonnet 4.6 comparison (Opus-only by user request)
- Cross-provider (GPT, Gemini)
- Human user studies
- Languages other than English
- Caveman intensity variants in their official invocation form
  (requires skill runtime)
- TTFT (stream-json parsing, marginal)
