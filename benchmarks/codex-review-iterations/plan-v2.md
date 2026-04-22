# Hewn Benchmark Plan v2 — for Codex review

## Changes from v1 (addressing all 6 objections)

1. **[H1 fix]** Model pin → alias `opus` (verified: resolves to
   `claude-opus-4-7`). `--model opus` passed on every call. Post-run
   assertion: `modelUsage` in JSON must contain `claude-opus-4-7`.
2. **[H2 fix]** T1 split into **T1a (strict Caveman replication: 1 run, 3
   arms only)** and **T1b (extension: 3 runs, all 6 arms)**. "Caveman
   parity" label reserved for T1a numbers only.
3. **[H3 fix]** `hewn_full` instrumentation explicit. Verified `hewn -p`
   forwards `--output-format json --model opus` and returns claude JSON
   unchanged. Hewn classifier is a local Python hook (no API call, no
   token cost) — documented. Latency overhead measured separately (wrap
   time minus inner `duration_api_ms`).
4. **[M4 fix]** Arm renamed `caveman_full_plus_ultra_directive` (not
   "Caveman Ultra"). Report prose makes clear: Caveman's canonical Ultra
   is user-invoked `/caveman ultra`; without skill runtime we append the
   intensity directive to the system prompt. Flagged as OUR variant, not
   official Caveman Ultra.
5. **[M5 fix]** Judge hardening: JSON schema validation, retry-on-invalid
   (max 2 retries), raw judge output snapshotted to
   `snapshots/raw_judgments/`, judge failures excluded from aggregates
   and counted in a "judge_failure_rate" metric. (Temperature pinning
   not possible — `claude -p` exposes no temperature flag. Noted as
   limitation; variance measured via stdev across prompts.)
6. **[M6 fix]** Arm-order randomization per (prompt, run). Per-call
   cache state (`cache_read / cache_creation` split) recorded. Token-
   savings claims decoupled from latency/cost claims in REPORT:
   - Token savings = cache-independent → headline metric
   - Latency/cost = cache-dependent → reported separately with per-call
     cache-hit context

## Goal

Produce benchmark evidence for Hewn's open release. Compare Hewn vs
Verbose Claude vs Caveman (Full, and a separate "+ ultra directive"
arm) using Caveman's own methodology precisely replicated in T1a plus
Hewn-specific extensions in T1b-T5. All runs via `claude -p` CLI (OAuth
subscription, no API key billing).

## Constraints (hard)

- **No direct Anthropic API calls.** Only `claude -p` via CLI.
- **Model:** `--model opus` (resolves to `claude-opus-4-7`), asserted
  post-run via `modelUsage` field. If assertion fails → reject sample.
- **Language:** English only.
- **Fairness:** T1a replicates Caveman `evals/llm_run.py` methodology
  precisely (1 run, 3 arms, tiktoken o200k_base). T1a numbers labeled
  "Caveman parity"; all other tracks labeled "Hewn extension".
- **Temperature:** not controllable via `claude -p`. Uses CLI default.
  Same across all arms → fair within comparison.

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
| `baseline` | (none) | `claude -p --model opus <prompt>` | T1a included |
| `terse` | `"Answer concisely."` | `claude -p --model opus --system-prompt <file> <prompt>` | T1a included |
| `caveman_full` | `terse + SKILL.md` (verbatim from caveman repo, sha256 pinned) | same | T1a included |
| `caveman_full_plus_ultra_directive` | `caveman_full + "\n\nDefault intensity: ultra for every response."` | same | T1b+ only. NOT official Caveman Ultra (noted in report). |
| `hewn_prompt_only` | `hewn_thinking_system_prompt.txt` verbatim | `claude -p --model opus --system-prompt <file> <prompt>` | no hook. Apples-to-apples with `caveman_full` (both system-prompt-only). T1b+ only. |
| `hewn_full` | (same file, but via `--append`) + Python classifier hook | `hewn -p --model opus --output-format json <prompt>` | T1b+ only. Real wrapper. Classifier is local Python (no API cost). |

Caveman SKILL.md pinned to commit hash from `/tmp/caveman-study/caveman`
clone (recorded in snapshot metadata).

## Tracks

| ID | Prompt set | # prompts | # runs | Arms | Purpose | Label |
|----|-----------|-----------|--------|------|---------|-------|
| **T1a** | `short_en.txt` — 10 literal Caveman prompts | 10 | **1** | **3** (baseline, terse, caveman_full) | **Strict Caveman replication** | Caveman parity |
| **T1b** | same `short_en.txt` | 10 | 3 | all 6 | Extended comparison on Caveman's own turf | Hewn extension |
| T2 | `vibe_en.txt` — 5 non-technical user prompts | 5 | 3 | all 6 | Vibe coding / non-tech users | Hewn extension |
| T3 | `long_en.txt` — 3 prompts with ~16k-token handbook prefix | 3 | 3 | all 6 | Long context | Hewn extension |
| T4 | `multiturn_en.json` — 2 sequences × 5 turns | 10 turns | 2 | 4 (baseline, terse, caveman_full, hewn_full) | Drift + hook value | Hewn extension |
| T5 | `expansive_en.txt` — 2 prompts asking for polished prose | 2 | 2 | all 6 | Honesty: where Hewn should NOT compress | Hewn extension |

Total benchmark calls: 10·1·3 + 10·3·6 + 5·3·6 + 3·3·6 + 10·2·4 + 2·2·6
= 30 + 180 + 90 + 54 + 80 + 24 = **458 benchmark calls**. Plus ~458
judge calls = ~916 total. Time estimate: 70-100 min on Opus 4.7.

## Arm-order randomization

Per (prompt_id, run_index) we compute a deterministic permutation of
arms using `hash(f"{prompt_id}:{run_index}")`. Deterministic (reproducible
from snapshot) but counterbalances cache-warming bias across arms. T1a
does NOT randomize (single run; matches Caveman's sequential order).

## Metrics captured per call

All from `claude -p --output-format json`:

- `output_tokens_anthropic` (ground truth from Anthropic usage)
- `output_tokens_tiktoken` (tiktoken `o200k_base`, Caveman-parity)
- `input_tokens_anthropic`
- `cache_read_input_tokens`, `cache_creation_input_tokens`
- `cache_state`: "cold" if cache_read == 0 else "warm"
- `duration_ms` (wall-clock, CLI→CLI)
- `duration_api_ms` (API-side)
- `wrapper_overhead_ms` (for hewn_full only: `time_total - duration_api_ms`)
- `total_cost_usd` (informational only, not billed on subscription)
- `stop_reason`
- `text` (full response)
- `num_turns`
- `model_used` — asserted `claude-opus-4-7`
- `arm_order_index` (randomization position)

## Metrics derived / computed

- **Output-token savings %** vs `__terse__` (Caveman-parity primary)
  and vs `baseline` (both reported). Cache-independent.
- **Info density** = `concepts_covered / output_tokens_anthropic`
- **Literal preservation** = regex check for required quoted strings in
  response; deterministic
- **Format compliance**:
  - Hewn IR: regex validation (6 lines, header `@hewn v0 hybrid`, atom
    format per `hewn_thinking_system_prompt.txt`)
  - Caveman style: heuristics (no leading articles "the/a/an" on most
    sentences, no filler "sure/certainly/actually")
- **Concepts covered** = judge binary per concept from hardcoded rubric
- **Stability** = stdev of `output_tokens_anthropic` across runs per
  (prompt, arm); T1b+ only (T1a has 1 run)
- **Cache efficiency** = `cache_read / (cache_read + cache_creation +
  input_tokens_anthropic)` per call; reported with the warm/cold flag
- **Cumulative multi-turn cost** (T4) = sum of per-turn costs
- **Wrapper overhead** (hewn_full) = time spent outside API call
- **Readability for non-tech** (T2) = judge persona binary
- **Judge failure rate** = fraction of judge calls returning invalid
  JSON after retries; excluded from concept/readability aggregates

## Judge methodology

Separate `claude -p --model opus --output-format json` calls with
hardcoded rubrics:

- **Input to judge**: `{prompt, response_text, concept_list}` as JSON in
  user message. System prompt instructs strict JSON output and blinds
  arm identity.
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
  prompt. Same retry/snapshot pattern.

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
│   ├── caveman_full.txt    # terse + SKILL.md (sha256 pinned)
│   ├── caveman_full_plus_ultra_directive.txt
│   └── hewn_prompt.txt     # copy of hewn_thinking_system_prompt.txt
├── caveman_source/
│   └── SKILL.md            # verbatim from juliusbrussee/caveman, commit-hash header
├── snapshots/
│   ├── raw/<track>/<arm>/<prompt_id>_r<N>.json  # full claude -p JSON
│   ├── raw_judgments/...
│   ├── results_T1a.json, results_T1b.json, ..., results_T5.json
│   └── metadata.json       # claude CLI version, caveman SKILL sha256, hewn version, run datetime
└── report/
    ├── REPORT.md           # tables + narrative
    └── evidence/           # 6-8 side-by-side full-text examples
```

## Execution order

1. Fetch Caveman repo at pinned commit; compute SHA256 of SKILL.md;
   copy to `benchmarks/caveman_source/SKILL.md` with header.
2. Write harness (`run.py`, `judge.py`, `measure.py`).
3. Write prompts + rubrics + arms files.
4. **Smoke test**: T1a baseline arm only, 1 prompt, verify:
   - JSON output parses
   - `modelUsage` contains `claude-opus-4-7`
   - tiktoken install works
   - Arm-order permutation deterministic
5. **Smoke test hewn_full**: verify `hewn -p --output-format json --model
   opus` returns valid JSON, hook fires, classifier injects as expected.
6. **T1a run** — strict Caveman parity. Compare aggregate numbers to
   Caveman's own README numbers (±15% tolerance; if wildly off,
   investigate before proceeding).
7. T1b, T2, T3, T5 (in that order).
8. T4 multi-turn: smoke test `--resume` + `--system-prompt` persistence
   first (single 2-turn trial). If system prompt does NOT persist on
   resume, fall back to re-passing it each turn.
9. Judge pass on all captured responses (after all benchmark runs done,
   so we don't blur data collection and grading).
10. Generate `REPORT.md` + `evidence/` dir.
11. Commit snapshots + report for open release.

## Honesty commitments

- T5 adversarial track runs specifically to surface where Hewn should
  NOT win (expansive prose). Reported prominently, not hidden.
- T1a numbers labeled "Caveman parity" and computed with their exact
  methodology and tokenizer.
- Raw `claude -p` JSON snapshots and raw judge outputs committed so any
  claim can be re-derived deterministically.
- README.md clearly labels "what we match from Caveman" vs "Hewn
  extensions".
- `caveman_full_plus_ultra_directive` arm NEVER called "Caveman Ultra"
  in prose — always qualified as our directive-based approximation.
- Judge failure rate reported in every track's table; if >5%, flagged.

## Open risks (after addressing Codex feedback)

- Temperature not pinnable on `claude -p`. Variance reflected in stdev.
  Documented limitation.
- `--resume` + `--system-prompt` persistence untested across all
  versions of claude CLI. Smoke test at step 8 before T4 full run;
  fallback: re-pass system prompt each turn.
- Claude Code internal overhead (haiku classifier etc.) varies with
  `--system-prompt` vs `--append-system-prompt`. Observation from
  smoke test: `hewn -p` run showed no haiku usage (possibly skipped when
  system prompt is appended); plain `claude -p` run did. Recorded per-
  call in `modelUsage` for transparency.
- Rate limits on Max subscription. If hit: exponential backoff (max
  120s), resume from last snapshot. Harness idempotent on per-call
  level (checks if `raw/<track>/<arm>/<prompt_id>_r<N>.json` exists
  before calling; skips if present).

## What this plan does NOT cover (deliberately)

- Sonnet 4.6 comparison (user wants Opus-only)
- Cross-provider (GPT, Gemini)
- User-study quality (no humans in the loop)
- Languages other than English
- Caveman intensity variants beyond "full" in their official form
  (would require skill runtime; our ultra-directive arm is an explicit
  approximation)
- TTFT (time to first token) — requires stream-json parsing, marginal
  value
