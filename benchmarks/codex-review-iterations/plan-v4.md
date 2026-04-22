# Hewn Benchmark Plan v4 — for Codex review

## Changes from v3 (4 new objections addressed)

1. **[H1 fix v4]** Hook overhead measured via `cache_creation_input_tokens`
   delta, not `input_tokens` delta. Verified empirically: smoke test
   showed `usage.input_tokens` identical (6 vs 6) but
   `cache_creation_input_tokens` increased by ~300 tokens with the hook.
   Total input footprint metric:
   `total_input = input_tokens + cache_creation_input_tokens + cache_read_input_tokens`
   stratified by warm/cold cache state. Smoke test step asserts the
   delta appears in cache_creation, not input_tokens.

2. **[H2 fix v4]** Benchmark environment isolation. The user's
   `~/.claude/CLAUDE.md` contains terseness instructions and contaminates
   `baseline` plus all `--append-system-prompt` arms (CLAUDE.md is part of
   Claude Code's default system prompt that `--append` adds to).
   `--system-prompt` replaces it cleanly; `--append-system-prompt` does
   not. `claude --bare` would fix this but requires `ANTHROPIC_API_KEY`
   (forbidden by user).
   
   **Mitigation harness**:
   - Pre-run: backup `~/.claude/CLAUDE.md` → `~/.claude/CLAUDE.md.bench-backup-<timestamp>`,
     replace with empty file. Atomic via `os.rename` then `open(path, 'w').close()`.
   - Post-run (and atexit + signal handlers SIGINT/SIGTERM): restore
     backup. Idempotent: if backup exists and live file is empty/missing,
     restore.
   - Pre-run: `cd` to fresh `mktemp -d` directory (no project CLAUDE.md
     auto-discovery).
   - For non-hewn arms: pass `--settings <empty-settings.json>` to prevent
     user hooks from firing.
   - For `hewn_full`: hewn wrapper generates its own `--settings`
     tmpfile; that's the only hook that fires.
   - Recorded in `snapshots/metadata.json`: `claude_md_isolated: true`,
     `cwd_temp: <path>`, `settings_overridden: true`.
   - **Crash safety**: also a standalone `restore_claude_md.sh` script
     that the user can run manually if the harness dies before
     restoring.

3. **[M3 fix v4]** `run.py` reads arm files and passes their **content**
   (not path) as the value of `--system-prompt` / `--append-system-prompt`.
   Smoke test asserts: pass a sentinel string ("BENCH_SENTINEL_42")
   in an arm file, run with that arm, prompt = "what is the magic word
   in your instructions?", verify response contains "BENCH_SENTINEL_42".
   This proves contents (not path) reach Claude.

4. **[M4 fix v4]** Arm-order randomization uses factoradic permutation
   (Lehmer code), pure-Python, version-independent:
   ```python
   def factoradic_permutation(n_arms: int, digest_int: int, arms: list) -> list:
       arms = list(arms)
       result = []
       remaining = arms[:]
       for i in range(n_arms, 0, -1):
           idx = digest_int % i
           digest_int //= i
           result.append(remaining.pop(idx))
       return result
   ```
   Seed: `"hewn-bench-v1"` (recorded). Per-call snapshot stores: `seed`,
   `digest_hex`, `arm_order_full` (list), `arm_order_index`. Reproducible
   across Python versions, machines.

## Goal

Produce benchmark evidence for Hewn's open release. Compare Hewn vs
Verbose Claude vs Caveman (Full + ultra-directive variant) using
Caveman's own methodology precisely replicated in T1a plus Hewn-specific
extensions in T1b-T5. All runs via `claude -p` CLI (OAuth subscription,
no API key billing). Environment isolated to remove user CLAUDE.md
contamination.

## Constraints (hard)

- **No direct Anthropic API calls.** Only `claude -p` via CLI.
- **Model:** `--model claude-opus-4-7` on every call. Asserted post-run
  via `modelUsage["claude-opus-4-7"].outputTokens == usage.output_tokens`.
- **Language:** English only.
- **Fairness:** T1a replicates Caveman `evals/llm_run.py`. Other tracks
  Hewn extensions.
- **Temperature:** not pinnable; CLI default; same across arms.
- **Environment:** harness isolates user CLAUDE.md and global hooks.

## Caveman study findings

(unchanged from v3)

## Arms

| ID | System prompt | Mechanism | Notes |
|---|---|---|---|
| `baseline` | (none) | `claude -p --model claude-opus-4-7 --settings <empty> <prompt>` | T1a included. Isolated cwd, no CLAUDE.md. |
| `terse` | `"Answer concisely."` | `claude -p --model claude-opus-4-7 --settings <empty> --system-prompt <content> <prompt>` | T1a included |
| `caveman_full` | `terse + SKILL.md` (verbatim, sha256 pinned) | same | T1a included |
| `caveman_full_plus_ultra_directive` | `caveman_full + ultra directive` | same | T1b+ only. NOT official Caveman Ultra. |
| `hewn_prompt_only` | `hewn_thinking_system_prompt.txt` content | `claude -p --model claude-opus-4-7 --settings <empty> --append-system-prompt <content> <prompt>` | no hook. T1b+ and T4. |
| `hewn_full` | (same content via `--append`) + Python classifier hook | `bash <repo>/integrations/claude-code/bin/hewn -p --model claude-opus-4-7 --output-format json <prompt>` | T1b+ and T4. Real wrapper; hook injects classification. |

Caveman SKILL.md pinned to commit hash from cloned `juliusbrussee/caveman`
repo (recorded in `snapshots/metadata.json`).

Empty settings file (`<empty>`): `{"hooks": {}}` → disables user hooks
without changing other Claude Code defaults.

## Tracks

(unchanged from v3, T4 has 5 arms including hewn_prompt_only)

| ID | Prompt set | # prompts | # runs | Arms | Purpose | Label |
|----|-----------|-----------|--------|------|---------|-------|
| **T1a** | `short_en.txt` (10 Caveman literal) | 10 | 1 | 3 (baseline, terse, caveman_full) | Strict Caveman replication | Caveman parity |
| T1b | same | 10 | 3 | all 6 | Extended | Hewn extension |
| T2 | `vibe_en.txt` (5) | 5 | 3 | all 6 | Vibe / non-tech | Hewn extension |
| T3 | `long_en.txt` (3, ~16k handbook) | 3 | 3 | all 6 | Long context | Hewn extension |
| T4 | `multiturn_en.json` (2 seq × 5 turns) | 10 turns | 2 | 5 (incl. hewn_prompt_only) | Drift + isolated hook value | Hewn extension |
| T5 | `expansive_en.txt` (2) | 2 | 2 | all 6 | Honesty: Hewn loses | Hewn extension |

Total: ~478 calls + ~478 judge ≈ 956. Time: 75-110 min.

## Arm-order randomization

Factoradic permutation (above), seed `"hewn-bench-v1"`. Per-call
snapshot persists `seed`, `digest_hex`, `arm_order_full`,
`arm_order_index`. Reproducible across Python versions/machines.

T1a does NOT randomize (1 run, sequential per Caveman methodology).

## Multi-turn (T4) session isolation

(unchanged from v3) Explicit `session_id` capture from turn 1, passed
as `--resume <id>` for turns 2-5. Post-run validation: no two
`(seq, run, arm)` tuples share session_id.

Smoke test step 6: 2-turn `--resume` per arm verifies system prompt
persistence; fallback documented if not.

## Metrics captured per call

- `output_tokens_anthropic`, `output_tokens_tiktoken` (o200k_base)
- `input_tokens_anthropic`
- `cache_read_input_tokens`, `cache_creation_input_tokens`
- `total_input_tokens` = `input_tokens + cache_creation + cache_read`
- `cache_state`: cold if `cache_read==0` else warm
- `duration_ms`, `duration_api_ms`
- `wrapper_overhead_ms` (hewn_full only)
- `total_cost_usd` (informational)
- `stop_reason`, `text`, `num_turns`, `session_id`
- `model_used` (asserted)
- `arm_order_index`, `arm_order_full`, `digest_hex`, `seed`

## Metrics derived

- **Output-token savings %** vs `__terse__` + vs `baseline`
- **Info density** = `concepts_covered / output_tokens_anthropic`
- **Literal preservation** = regex over required quoted strings
- **Format compliance** (Hewn IR / caveman style)
- **Concepts covered** = judge binary
- **Stability** = stdev of output_tokens_anthropic across runs (T1b+)
- **Cache efficiency** = `cache_read / total_input_tokens` per call
- **Hook value (T4)** = (`hewn_prompt_only` cumulative metrics −
  `hewn_full` cumulative metrics) per sequence
- **Hewn classifier injection cost** = `hewn_full.cache_creation_input_tokens
  − hewn_prompt_only.cache_creation_input_tokens` per call (NOT
  input_tokens delta — that's zero per smoke test). Reported per track.
- **Cumulative multi-turn cost** (T4)
- **Wrapper overhead** (`hewn_full`) = wall-clock outside API
- **Readability for non-tech** (T2) = judge binary
- **Judge failure rate** = invalid-after-retry / total

## Judge methodology

(unchanged from v3) Strict JSON schema, 2 retries, raw snapshots,
blinded, judge-failure-rate tracked.

## Directory layout

```
benchmarks/
├── README.md
├── run.py
├── judge.py
├── measure.py
├── isolate_env.py            # CLAUDE.md backup/restore + atexit + signals
├── restore_claude_md.sh      # manual recovery if harness crashes
├── empty_settings.json       # {"hooks": {}}
├── prompts/
│   ├── short_en.txt
│   ├── vibe_en.txt
│   ├── long_en.txt
│   ├── long_handbook.txt     # ~16k
│   ├── multiturn_en.json
│   └── expansive_en.txt
├── rubrics/
│   ├── concepts.json
│   └── literals.json
├── arms/
│   ├── baseline.txt          (empty)
│   ├── terse.txt
│   ├── caveman_full.txt
│   ├── caveman_full_plus_ultra_directive.txt
│   └── hewn_prompt.txt
├── caveman_source/
│   └── SKILL.md              # verbatim, commit-hash header
├── snapshots/
│   ├── raw/<track>/<arm>/<prompt_id>_r<N>.json
│   ├── raw_judgments/...
│   ├── results_T1a.json … results_T5.json
│   └── metadata.json         # CLI version, sha256s, hewn version, run datetime, seed, isolation flags
└── report/
    ├── REPORT.md
    └── evidence/
```

## Execution order

1. Fetch Caveman repo at pinned commit; SHA256 `SKILL.md`; copy to
   `caveman_source/` with header.
2. Write harness (`run.py`, `judge.py`, `measure.py`, `isolate_env.py`,
   `restore_claude_md.sh`).
3. Write prompts + rubrics + arms.
4. **Isolate env**: backup CLAUDE.md, replace with empty; cd to fresh
   `mktemp -d`. Register atexit + SIGINT/SIGTERM handlers to restore.
5. **Smoke test 1 — model assertion**: T1a baseline, 1 prompt; verify
   `modelUsage["claude-opus-4-7"].outputTokens == usage.output_tokens`,
   tiktoken installed, factoradic permutation deterministic across two
   subprocess invocations.
6. **Smoke test 2 — sentinel arm**: arm file with `BENCH_SENTINEL_42`,
   prompt asks for the magic word, verify response contains sentinel
   (proves content, not path, reaches Claude).
7. **Smoke test 3 — hewn_full hook**: run hewn_prompt_only and
   hewn_full on same prompt; assert `hewn_full.cache_creation_input_tokens
   > hewn_prompt_only.cache_creation_input_tokens` (hook injects context).
8. **Smoke test 4 — multi-turn**: 2-turn sequence with explicit
   `--resume <id>`; verify system prompt persists OR document fallback.
9. **T1a run** — strict Caveman parity. Compare to Caveman's published
   numbers (±15% tol; if wildly off, investigate isolation completeness).
10. T1b, T2, T3, T5 runs.
11. T4 multi-turn run + post-run session-isolation validation.
12. Judge pass on all responses.
13. Generate REPORT.md + evidence/.
14. **Restore env**: restore CLAUDE.md from backup. Verify identical
    SHA256 to original.
15. Commit snapshots + report.

## Honesty commitments

- T5 surfaces where Hewn loses; reported prominently.
- T1a labeled "Caveman parity" using their exact methodology.
- Raw JSON snapshots committed; deterministic re-derivation.
- README labels match-vs-extend explicitly.
- `caveman_full_plus_ultra_directive` NEVER called "Caveman Ultra".
- Hewn arms use `--append`; Caveman arms use `--system-prompt`.
  Asymmetric; documented. With CLAUDE.md isolated, the only remaining
  asymmetry is Claude Code's default system prompt being added to Hewn
  arms (visible in `cache_creation_input_tokens`). Documented in REPORT.
- Hewn hook injection cost reported via `cache_creation_input_tokens`
  delta, not input_tokens delta.
- T4 hook value attributed to (hewn_prompt_only - hewn_full) delta.
- Judge failure rate per track.
- Environment isolation flags in metadata.

## Open risks

- Crash mid-run leaves CLAUDE.md replaced. Mitigation: atexit + signal
  handlers + standalone `restore_claude_md.sh`.
- Caveman's published numbers were measured in their author's own
  CLAUDE.md environment (presumed). Our isolated baseline may diverge
  ±15%. Documented; if diverges >25%, investigate before claiming
  parity.
- Temperature unpinnable; variance via stdev.
- `--resume` system-prompt persistence: validated step 8.
- Rate limits: backoff + idempotent skip-if-snapshot-exists.
- `--settings <empty>` may not fully disable plugins/MCP. If smoke
  tests show extra tools loading, add `--disable-slash-commands` and
  document.

## What this plan does NOT cover

(unchanged) Sonnet, cross-provider, human studies, non-English,
official Caveman ultra invocation, TTFT.
