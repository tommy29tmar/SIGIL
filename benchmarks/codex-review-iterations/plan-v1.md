# Hewn Benchmark Plan — for Codex review

## Goal

Produce benchmark evidence for Hewn's open release. Compare Hewn vs
Verbose Claude vs Caveman (Full + Ultra) using Caveman's own methodology
as the fairness baseline, plus Hewn-specific extensions. All runs via
`claude -p` CLI (OAuth subscription, no API key billing).

## Constraints (hard)

- **No direct Anthropic API calls.** Only `claude -p` via CLI.
- **Model:** Opus 4.7 (`claude-opus-4-7[1m]`) across all arms.
- **Language:** English only.
- **Fairness:** Replicate Caveman's `evals/llm_run.py` methodology
  precisely for Track 1 (the "apples-to-apples" track).

## Caveman study findings (what they actually measure)

From https://github.com/juliusbrussee/caveman:

- `evals/llm_run.py`: single run per (prompt, arm), `claude -p
  --system-prompt <x>`, tiktoken `o200k_base` for output tokens,
  reports median/mean/min/max/stdev. Arms: `__baseline__` (no sys),
  `__terse__` ("Answer concisely."), `<skill>` ("Answer concisely.\n\n"
  + SKILL.md).
- `benchmarks/run.py`: uses Anthropic SDK (forbidden for us). Multiple
  trials, median. Measures input_tokens, output_tokens, stop_reason.
- **Not measured by Caveman:** latency, fidelity, quality rubric,
  cross-arm variance.

Honest delta per Caveman's own README: `<skill>` vs `__terse__`, NOT
`<skill>` vs `__baseline__` (which conflates with generic terseness).

## Arms (6)

1. `baseline` — no `--system-prompt`
2. `terse` — `--system-prompt "Answer concisely."`
3. `caveman_full` — `--system-prompt "Answer concisely.\n\n" + SKILL.md`
   (copied verbatim from caveman/skills/caveman/SKILL.md)
4. `caveman_ultra` — same as `caveman_full` + appended instruction
   "Default intensity: ultra for every response."
5. `hewn_prompt_only` — `--system-prompt <hewn_thinking_system_prompt>`
   (no hook; apples-to-apples with caveman which has no hook)
6. `hewn_full` — `hewn -p` real wrapper (prompt + classifier hook)

## Tracks

| ID | Prompt set | # prompts | # runs | Arms | Purpose |
|----|-----------|-----------|--------|------|---------|
| T1 | `short_en.txt` — 10 literal Caveman prompts (attributed) | 10 | 3 | all 6 | Caveman-parity |
| T2 | `vibe_en.txt` — 5 non-technical user prompts | 5 | 3 | all 6 | Vibe coding / non-tech users |
| T3 | `long_en.txt` — 3 prompts with ~16k-token handbook prefix | 3 | 3 | all 6 | Long context, Hewn strength |
| T4 | `multiturn_en.json` — 2 sequences × 5 turns | 10 turns | 2 | 4 (baseline, terse, caveman_full, hewn_full) | Drift + hook value |
| T5 | `expansive_en.txt` — 2 prompts asking for polished prose | 2 | 2 | all 6 | Honesty: where Hewn should NOT compress |

Total `claude -p` invocations: 10·3·6 + 5·3·6 + 3·3·6 + 10·2·4 + 2·2·6
= 180 + 90 + 54 + 80 + 24 = **428 benchmark calls** + ~428 judge calls
= ~860 total. Time estimate: 60-90 min on Opus 4.7.

## Metrics captured per call

All from `claude -p --output-format json` (native, no approximation
except tiktoken which is additive):

- `output_tokens_anthropic` (ground truth)
- `output_tokens_tiktoken` (tiktoken `o200k_base`; Caveman-parity primary)
- `input_tokens_anthropic`
- `cache_read_input_tokens`, `cache_creation_input_tokens`
- `duration_ms` (wall-clock)
- `duration_api_ms` (API-side only)
- `total_cost_usd` (informational, not billed on subscription)
- `stop_reason`
- `text` (full response)
- `num_turns`

## Metrics derived / computed

- **Savings %** vs `__terse__` (Caveman-parity) and vs `baseline` (both reported)
- **Info density** = `concepts_covered / output_tokens`
- **Literal preservation** = regex: required quoted strings present in response
- **Format compliance** = Hewn IR valid (6 lines, atom format); caveman-style (no articles, fragments)
- **Concepts covered** = judge binary per concept from hardcoded rubric
- **Stability** = stdev of output_tokens across runs per (prompt, arm)
- **Cache efficiency** = cache_read / total_input in multi-turn
- **Cumulative multi-turn cost** = sum of all turns in a sequence
- **Readability for non-tech** (T2 only) = judge persona binary

## Judge methodology

Separate `claude -p` calls, Opus 4.7, with hardcoded rubrics:

- Input: `{prompt, response_text, concept_list}`
- Output: strict JSON `{concept_name: bool}` for each concept
- No free-form scoring, no "rate 1-10" — only deterministic binary presence
- Blind: judge does not see which arm produced the response
- Separate pass for "non-tech readability" (T2) with persona prompt

## Directory layout

```
benchmarks/
├── README.md               # methodology, attribution, what we match vs extend
├── run.py                  # subprocess wrapper for claude -p
├── judge.py                # concepts + readability judge
├── measure.py              # reads snapshots, outputs report markdown
├── prompts/
│   ├── short_en.txt        # 10 Caveman literal (header: source attribution)
│   ├── vibe_en.txt
│   ├── long_en.txt
│   ├── long_handbook.txt   # ~16k token Atlas API handbook
│   ├── multiturn_en.json   # 2 sequences of 5 turns
│   └── expansive_en.txt
├── rubrics/
│   ├── concepts.json       # {prompt_id: [required_concepts]}
│   └── literals.json       # {prompt_id: [required_literal_strings]}
├── arms/
│   ├── baseline.txt        (empty)
│   ├── terse.txt
│   ├── caveman_full.txt    # terse + SKILL.md
│   ├── caveman_ultra.txt   # + ultra directive
│   └── hewn_prompt.txt     # copy of hewn_thinking_system_prompt.txt
├── snapshots/
│   ├── raw/<track>/<arm>/<prompt_id>_r<N>.json  # full claude -p JSON
│   ├── results_T1..T5.json # aggregated per track
│   └── judgments.json
└── report/
    ├── REPORT.md           # tables + narrative
    └── evidence/           # 6-8 side-by-side full-text examples
```

## Execution order

1. Write harness (`run.py`, `judge.py`, `measure.py`)
2. Write prompts + rubrics + arms
3. Smoke test: T1 baseline arm only, 1 prompt, verify JSON capture works
4. Full T1 run (Caveman parity) — verify numbers match Caveman's own claims
5. T2, T3, T4, T5 in that order
6. Judge pass on all captured responses
7. Generate REPORT.md + evidence dir
8. Commit snapshots + report for release

## Honesty commitments

- T5 adversarial track runs specifically to surface where Hewn should
  NOT win (expansive prose). Reported prominently.
- Primary Caveman-parity numbers (T1) computed with their exact
  methodology and tokenizer.
- Raw `claude -p` JSON snapshots committed so any claim can be
  re-derived from source.
- README.md will clearly label "what we match from Caveman" vs "what we
  extended with Hewn-specific metrics."

## Open risks

- `claude -p` with `--system-prompt` may still have Claude Code internal
  overhead (haiku classifier, tool instructions) that skews numbers.
  Mitigation: same overhead in every arm. For extra rigor, test
  `claude --bare -p --system-prompt ...` mode and record both.
- Multi-turn via `--resume` needs validation that `--system-prompt`
  persists across resumes. Will smoke-test before full T4 run.
- Opus 4.7 rate limits on Max subscription: if hit, fall back to
  sequential with sleep. Plan for 90-min upper bound.
- Tiktoken `o200k_base` ≠ Claude BPE. Matches Caveman's own caveat;
  report both counts, primary comparison uses tiktoken for parity.

## What this plan does NOT cover (deliberately)

- Sonnet 4.6 comparison (user wants Opus-only)
- Cross-provider (GPT, Gemini)
- User-study quality (no humans in the loop)
- Languages other than English
