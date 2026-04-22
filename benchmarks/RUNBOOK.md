# RUNBOOK — exact reproduction of the 2026-04-22 benchmark run

This is the literal sequence of every command, file, and decision used
to produce the artifacts in this directory. Re-running these steps in
order will produce a comparable result (modulo CLI/model drift; see
"Reference numbers" at the bottom).

## 0. Environment captured at original run

| Field | Value |
|---|---|
| Date (UTC) | 2026-04-22T00:56:33 |
| Host | `tommaso@<linux>` (Ubuntu, Linux 6.8.0-106-generic) |
| Shell | zsh |
| `claude` CLI | `2.1.117 (Claude Code)` |
| Model | `claude-opus-4-7` (full ID, NOT alias `opus`) |
| Hewn repo commit | `dd864d7db31fde7d200f72818e1ac6aea8497d95` |
| Caveman repo commit pinned | `84cc3c14fa1e10182adaced856e003406ccd250d` |
| Caveman SKILL.md sha256 | `1762eb9ab0b566d70f51b040dbfd77d1f5be89cfa70da874564bda38c111be7c` |
| Random seed | `hewn-bench-v1` |
| Auth | OAuth (Claude Code Max subscription). NO `ANTHROPIC_API_KEY`. |
| `~/.claude/CLAUDE.md` | present, sha256 `fed963e9ef7ef01d1da3ae8ec1ca0dc6903e5c2ccd58023b8ae8b6bb02e2112e`, 169 words, terseness instruction (`"Answer concisely. Drop filler, hedging, and pleasantries."`) — left in place per user decision (option B) |
| Python | 3.11+ (system Python) |
| `tiktoken` | installed via `pip install tiktoken` (version `0.12.0`) |

## 1. Prerequisites

```bash
# Verify claude CLI is on PATH and authenticated (OAuth Max sub):
claude --version
claude -p "hi" --output-format json | python3 -c "import json,sys;print(json.load(sys.stdin)['model'])"

# Install tokenizer:
pip install tiktoken

# Verify hewn wrapper exists at the expected path:
test -f /home/tommaso/dev/playground/SIGIL/integrations/claude-code/bin/hewn
```

## 2. Vendor Caveman SKILL.md at the pinned commit

```bash
mkdir -p /tmp/caveman-study
git clone --depth 1 https://github.com/juliusbrussee/caveman.git /tmp/caveman-study/caveman
cd /tmp/caveman-study/caveman
git checkout 84cc3c14fa1e10182adaced856e003406ccd250d   # pinned for reproducibility
sha256sum skills/caveman/SKILL.md
# expect: 1762eb9ab0b566d70f51b040dbfd77d1f5be89cfa70da874564bda38c111be7c
```

The vendored copy is committed under `benchmarks/caveman_source/SKILL.md`
with the upstream commit hash and sha256 in its header.

## 3. Files created (purpose summary)

```
benchmarks/
├── README.md                   # what + why; for repo readers
├── RUNBOOK.md                  # this file: how to reproduce
├── run.py                      # subprocess harness for claude -p / hewn -p
├── judge.py                    # concepts + readability judge (claude -p)
├── measure.py                  # snapshots → REPORT.md
├── extract_evidence.py         # snapshots → 8 side-by-side .md examples
├── prompts/
│   ├── short_en.txt            # 10 prompts, vendored from caveman/evals/prompts/en.txt
│   ├── vibe_en.txt             # 5 non-tech / vibe-coding prompts (Hewn)
│   ├── long_en.txt             # 3 prompts, paired at runtime with handbook
│   ├── long_handbook.txt       # ~5k-token Atlas API handbook prefix
│   ├── multiturn_en.json       # 2 sequences × 5 turns each
│   └── expansive_en.txt        # 2 polished-prose prompts (honesty: Hewn loses)
├── rubrics/
│   ├── concepts.json           # per prompt_id, list of required concepts (judge)
│   └── literals.json           # per prompt_id, required quoted strings (regex)
├── arms/
│   ├── baseline.txt            # (empty)
│   ├── terse.txt               # "Answer concisely."
│   ├── terse_appended.txt      # same content as terse, but T0 uses --append
│   ├── caveman_full.txt        # terse + caveman SKILL.md (verbatim)
│   ├── caveman_full_appended.txt  # same content, T0 uses --append
│   ├── caveman_full_plus_ultra_directive.txt  # caveman_full + ultra directive
│   └── hewn_prompt.txt         # copy of hewn_thinking_system_prompt.txt
├── caveman_source/SKILL.md     # vendored, sha256-attributed
├── snapshots/
│   ├── raw/<track>/<arm>/<prompt_id>_r<N>[_t<T>].json   # full claude -p JSON per call
│   ├── raw_judgments/<track>/<arm>/...                  # raw judge outputs + retry history
│   ├── judgments_<track>.json                           # parsed judge results
│   └── metadata.json
└── report/
    ├── REPORT.md
    └── evidence/01..08_*.md
```

All file contents are committed in commit `b141e4e`.

## 4. Arm construction (exact byte content)

| Arm | How `arms/*.txt` was built |
|---|---|
| `baseline.txt` | empty file (`""`) |
| `terse.txt` | literal `"Answer concisely."` (no trailing newline matters; we passed CONTENT) |
| `terse_appended.txt` | `cp arms/terse.txt arms/terse_appended.txt` |
| `caveman_full.txt` | `{ echo "Answer concisely."; echo; cat /tmp/caveman-study/caveman/skills/caveman/SKILL.md; } > arms/caveman_full.txt` |
| `caveman_full_appended.txt` | `cp arms/caveman_full.txt arms/caveman_full_appended.txt` |
| `caveman_full_plus_ultra_directive.txt` | `{ cat arms/caveman_full.txt; echo; echo "Default intensity: ultra for every response."; } > arms/caveman_full_plus_ultra_directive.txt` |
| `hewn_prompt.txt` | `cp integrations/claude-code/hewn_thinking_system_prompt.txt arms/hewn_prompt.txt` |

For the runner, `run.py:arm_content(arm)` reads the file and passes the
TEXT (not path) to `--system-prompt` / `--append-system-prompt`. Smoke 2
verifies this path on every fresh checkout.

## 5. Per-arm CLI invocation (what `run.py` actually executes)

```python
# run.py:build_cmd
if arm == "hewn_full":
    cmd = ["bash", "<repo>/integrations/claude-code/bin/hewn", "-p",
           "--model", "claude-opus-4-7", "--output-format", "json"]
elif arm in ("terse", "caveman_full", "caveman_full_plus_ultra_directive"):
    cmd = ["claude", "-p", "--model", "claude-opus-4-7",
           "--output-format", "json",
           "--system-prompt", <content of arms/<arm>.txt>]
elif arm in ("terse_appended", "caveman_full_appended", "hewn_prompt_only"):
    cmd = ["claude", "-p", "--model", "claude-opus-4-7",
           "--output-format", "json",
           "--append-system-prompt", <content of arms/<arm>.txt>]
elif arm == "baseline":
    cmd = ["claude", "-p", "--model", "claude-opus-4-7",
           "--output-format", "json"]

if resume_session_id is not None:           # T4 turns 2-5
    cmd += ["--resume", resume_session_id]
cmd.append(prompt)
```

Subprocess capture: `subprocess.run(cmd, capture_output=True, text=True)`,
then `json.loads(stdout)`. Wall-clock measured with `time.monotonic()`
around the call. Retries: 3, with 10s/30s/90s backoff on non-zero rc or
JSON parse failure.

## 6. Metrics captured per call (saved verbatim into the snapshot JSON)

From the JSON returned by `claude -p --output-format json`:

| Field | Source |
|---|---|
| `output_tokens_anthropic` | `usage.output_tokens` |
| `input_tokens_anthropic` | `usage.input_tokens` |
| `cache_creation_input_tokens` | `usage.cache_creation_input_tokens` |
| `cache_read_input_tokens` | `usage.cache_read_input_tokens` |
| `total_input_tokens` | sum of the three above |
| `cache_state` | `"warm"` if cache_read>0 else `"cold"` |
| `duration_ms` | `duration_ms` (CLI-reported wall-clock) |
| `duration_api_ms` | `duration_api_ms` (CLI-reported API time) |
| `wallclock_ms` | Python `time.monotonic()` delta |
| `wrapper_overhead_ms` | for `hewn_full`: `wallclock - duration_api_ms` |
| `total_cost_usd` | `total_cost_usd` (informational; subscription absorbs) |
| `stop_reason` | `stop_reason` |
| `num_turns` | `num_turns` |
| `session_id` | `session_id` (used for T4 multi-turn isolation) |
| `model_used` | comma-joined keys of `modelUsage` map |
| `assertion_pass` | `modelUsage["claude-opus-4-7"].outputTokens == usage.output_tokens` |
| `result` | `result` (full response text) |
| `output_tokens_tiktoken` | `len(tiktoken.get_encoding("o200k_base").encode(result))` (matches Caveman's `evals/measure.py`) |
| `raw_payload` | full original JSON (everything above is derived from it) |
| `arm_order_index`, `arm_order_full`, `digest_hex`, `seed`, `timestamp` | runner metadata |

The full JSON is written to
`snapshots/raw/<track>/<arm>/<prompt_id>_r<N>[_t<T>].json`. The harness
is **idempotent**: if the file exists, the call is skipped.

## 7. Arm-order randomization (factoradic Lehmer code)

```python
# run.py:perm_for
import hashlib
def perm_for(prompt_id, run_index, arms):
    if len(arms) <= 1:
        return list(arms)
    seed = "hewn-bench-v1"
    digest = hashlib.sha256(f"{seed}:{prompt_id}:{run_index}".encode()).hexdigest()
    n = int(digest, 16)
    out, remaining = [], list(arms)
    for i in range(len(remaining), 0, -1):
        idx = n % i
        n //= i
        out.append(remaining.pop(idx))
    return out
```

Per `(track, prompt_id, run_index)` we precompute the arm order and
record it in every snapshot under `arm_order_full`/`arm_order_index`.
T0 and T1a do NOT randomize (single-run, sequential). Other tracks
randomize per `(prompt, run)` to spread cache-warming bias across arms.

## 8. Multi-turn (T4) — exact session protocol

For each `(sequence_id, run_index, arm)`:
1. Turn 1: `build_cmd(arm, turn1_user_msg)` (no `--resume`). Capture
   `session_id` from response JSON.
2. Turns 2-5: `build_cmd(arm, turnK_user_msg, resume=session_id)`.
   The system prompt is **re-passed every turn** (smoke 4 confirmed it
   does NOT persist across `--resume` on this CLI version).
3. After all 100 calls done, `measure.py` runs the session-isolation
   check: every `session_id` must be unique to a single
   `(arm, sequence_id, run_index)` tuple. The current run reports OK.

## 9. Smoke tests (run BEFORE any track)

```bash
python3 benchmarks/run.py --smoke
```

Validates:
1. **Model assertion**: `modelUsage["claude-opus-4-7"].outputTokens == usage.output_tokens`. tiktoken installed. Factoradic permutation produces same ordering across two subprocess invocations.
2. **Sentinel content reaches Claude**: arm file contains literal
   `BENCH_SENTINEL_OK`; running `claude -p --system-prompt <content>
   "what is 2 + 2?"` must include the sentinel in the response (proves
   we passed CONTENT, not the file path).
3. **Hewn hook delta**: `hewn_full.cache_creation_input_tokens >
   hewn_prompt_only.cache_creation_input_tokens` on the same prompt.
   Original observed delta: ~215-1500 tokens (varies with cache state).
4. **Multi-turn `--resume` system-prompt persistence**: documented as
   NOT persisted; this is informational. The harness re-passes the
   system prompt on every turn anyway.

If any of 1-3 fails, **do not proceed** with full tracks.

## 10. Track execution order (exact sequence used)

```bash
cd /home/tommaso/dev/playground/SIGIL

# Foreground (small, verify outputs visually):
python3 benchmarks/run.py --track T0       #  40 calls, ~6 min
python3 benchmarks/run.py --track T1a      #  30 calls, ~5 min

# Background sequentially (use the helper script — Claude OAuth dislikes
# parallel processes from the same user, so run them in series):
cat > /tmp/run_all_tracks.sh << 'EOF'
#!/bin/bash
set -e
cd /home/tommaso/dev/playground/SIGIL
echo "=== START $(date -Is) ==="
for track in T1b T2 T3 T5 T4; do
  echo "=== TRACK $track $(date -Is) ==="
  python3 benchmarks/run.py --track "$track" 2>&1
  echo "=== DONE $track $(date -Is) ==="
done
echo "=== ALL TRACKS DONE $(date -Is) ==="
EOF
chmod +x /tmp/run_all_tracks.sh
/tmp/run_all_tracks.sh > /tmp/run_all.log 2>&1 &
# Track progress: tail -F /tmp/run_all.log | grep -E "TRACK|DONE|ERROR"
```

Track durations on the original run:

| Track | Calls | Wall-clock |
|---|---:|---:|
| T0 | 40 | ~6 min |
| T1a | 30 | ~5 min |
| T1b | 180 | ~35 min (started 01:39, done 02:14) |
| T2 | 90 | ~16 min (started 02:14, done 02:30) |
| T3 | 54 | ~22 min (started 02:30, done 02:52) |
| T5 | 24 | ~4 min (started 02:52, done 02:56) |
| T4 | 100 | ~40 min (started 02:56, done 03:36) |
| **Total bench** | **518** | **~2h 8min** |

The harness is idempotent. To resume after an interruption, just rerun
the same `--track <T>` invocation; existing `<prompt>_r<N>.json` files
are skipped.

## 11. Judge pass

```bash
# After ALL bench tracks done (judges also call claude -p; running
# concurrently with bench tracks risks rate-limiting):
cat > /tmp/run_judges.sh << 'EOF'
#!/bin/bash
set -e
cd /home/tommaso/dev/playground/SIGIL
for track in T1b T2 T3 T5; do
  python3 benchmarks/judge.py --track "$track" 2>&1
done
EOF
chmod +x /tmp/run_judges.sh
/tmp/run_judges.sh > /tmp/judges.log 2>&1 &

# T4 judge separately (was started later in the original run):
python3 benchmarks/judge.py --track T4 > /tmp/judge_t4.log 2>&1 &

# T1a judge (the smallest, useful for an early sanity check):
python3 benchmarks/judge.py --track T1a
```

What the judge does per snapshot:
- Reads `result` from the snapshot.
- Loads `rubrics/concepts.json[<prompt_set>][<prompt_id>]` (list of
  required concepts).
- Sends `claude -p --model claude-opus-4-7 --output-format json
  --system-prompt <CONCEPT_JUDGE_SYSTEM> <user_message>` where
  `<user_message>` includes the original prompt + response text +
  concept list.
- Validates strict-JSON `{concept_name: bool}` output. **2 retries** on
  invalid. After 3 failures: marks `concepts: null`,
  `concepts_failure: true`, contributes to `judge_failure_rate`.
- Writes raw judge call (with retry history) to
  `snapshots/raw_judgments/<track>/<arm>/<prompt_id>_r<N>_concepts.json`.
- Appends parsed result to `snapshots/judgments_<track>.json`.
- Also runs deterministic checks: literal preservation (regex
  `<lit> in result`), Hewn IR validity (regex over the 6-line shape),
  Caveman style heuristics (filler-token frequency, sentence-leading
  articles).
- For T2 only: also runs a "non-tech readability" persona judge
  returning 4 booleans (uses_plain_language, actionable,
  starts_helpfully, respects_user_level).

The judge is BLINDED: the prompt to the judge does NOT include the arm
name. Response is labeled "RESPONSE UNDER REVIEW".

## 12. Report + evidence generation

```bash
python3 benchmarks/measure.py            # writes report/REPORT.md
python3 benchmarks/extract_evidence.py   # writes report/evidence/01..08_*.md
```

`measure.py` reads ALL of `snapshots/raw/*` and `snapshots/judgments_*.json`,
writes:
- T1a Caveman-parity table (output tokens via tiktoken, savings vs
  terse, totals)
- T0 append-vs-replace exposure deltas
- T1b: per-prompt × arm output tokens median (Anthropic ground truth);
  Hewn-vs-Caveman/terse `(appended, observed)` pair via T0+T1b cross-
  track join (appended side from T0 single run, observed side from T1b
  median-of-3); Hewn-vs-baseline causal table; per-arm stability
  (stdev of output tokens across runs)
- T2/T3/T5: median-per-prompt-per-arm tables; Hewn-vs-baseline causal;
  wall-clock latency tables
- T4: cumulative-per-sequence tables; hook value
  `(hewn_prompt_only - hewn_full)` cumulative deltas; session_id
  isolation check
- Quality table per track: concepts coverage mean ratio, literals
  preserved mean, Hewn IR validity rate, filler/100w mean, judge
  failure count, T2 readability mean true ratio

`extract_evidence.py` picks 8 representative cases (1-2 per track) and
writes side-by-side full-text examples so any reader can audit the raw
responses.

## 13. Final commit (already done in this branch)

```bash
git add benchmarks/
git -c commit.gpgsign=false commit -m "benchmarks/: add Hewn vs Verbose Claude vs Caveman benchmark suite" \
  -m "$(see commit b141e4e for the full body)"
```

Commit hash on this branch: `b141e4e4bf0288455e1e8389628610541752aa1e`

## 14. Plan iteration files (kept for the audit trail)

The plan went through 8 cross-model review rounds with Codex (LGTM at
v9). Each iteration was saved at the time:

```
/tmp/codex-review/plan-v1.md   # initial
/tmp/codex-review/plan-v2.md   # H1 model pin, H2 T1 split, H3 hewn instrumentation, M4 ultra naming, M5 judge robustness, M6 cache/order
/tmp/codex-review/plan-v3.md   # H1v3 full ID, H2v3 hook overhead via cache_creation, H3v3 explicit session_id, M4v3 T4 5-arm, M5v3 factoradic
/tmp/codex-review/plan-v4.md   # H1 v4 cache_creation overhead, H2v4 env isolation (later removed), M3v4 file content, M4v4 factoradic
/tmp/codex-review/plan-v5.md   # remove env isolation per user choice (option B); document contamination
/tmp/codex-review/plan-v6.md   # H1v6 corrected bias direction; add T0 calibration
/tmp/codex-review/plan-v7.md   # M1v7 T0 renamed (append-vs-replace, not CLAUDE.md-only); M2v7 explicit (appended, observed) pair
/tmp/codex-review/plan-v8.md   # M1v8 adjusted bracket scope T1 only; M2v8 no ordering assumption
/tmp/codex-review/plan-v9.md   # M1v9 cross-track join formal; M2v9 Hewn-vs-baseline T1b-T5
```

These files live under `/tmp/codex-review/` on the original host and
are NOT committed to the repo. If you want to preserve them long-term,
copy them under `benchmarks/codex-review-iterations/` before the next
reboot.

## 15. Reference numbers from the 2026-04-22 run

Use these to sanity-check a re-run. Rerunning end-to-end on the same
CLI version, same model, same prompts, same seed should produce values
in the same ballpark (single runs in T0/T1a will vary at the
~10-20% level due to model-side temperature).

**T1a (strict Caveman parity, 1 run)** — output tokens via tiktoken:

| Arm | Total tokens | Mean savings vs terse |
|---|---:|---:|
| `baseline` | 2377 | — |
| `terse` | 2318 | — |
| `caveman_full` | 943 | **59% median, 60% vs baseline** |

(matches Caveman's published ~60% claim within tolerance)

**T1b (3 runs, median per arm/prompt)** — output tokens (Anthropic):

| Arm | Mean output tokens across 10 prompts |
|---|---:|
| `baseline` | 349 |
| `terse` | 356 |
| `caveman_full` | **167** ← winner on raw token count |
| `caveman_full_plus_ultra_directive` | 140 |
| `hewn_prompt_only` | 352 |
| `hewn_full` | 264 |

Hewn-vs-baseline median savings: **24%** (range −46% to +47%).
Hewn-vs-Caveman observed: Hewn produces ~97 tokens MORE than Caveman
(median). So Caveman wins single-turn Q&A token compression.

**T4 (multi-turn cumulative, median across 2 runs)**:

| Sequence | baseline | terse | caveman_full | hewn_prompt_only | hewn_full |
|---|---:|---:|---:|---:|---:|
| `debug-prod-incident` (5 turns) | 5550 | 2255 | 1612 | 6030 | **1301** |
| `design-feature` (5 turns) | 8841 | 5585 | 6840 | 10902 | **5295** |

Hook value `(hewn_prompt_only − hewn_full)`: +4729 and +5607
cumulative tokens. The hook is doing real work.

**T2 (non-tech readability persona judge)**:

| Arm | Readability mean true ratio |
|---|---:|
| `baseline` | **78%** ← best |
| `hewn_prompt_only` | 60% |
| `terse` | 43% |
| `hewn_full` | 35% |
| `caveman_full_plus_ultra_directive` | 28% |
| `caveman_full` | **20%** ← worst |

**T3 `rate-limit-xff-review` (IR-style task) — concepts coverage**:

| Arm | Concepts (best of 3 runs) | Output tokens |
|---|---:|---:|
| `baseline` | 0/6 | ~146 (asked clarifying question) |
| `terse` | 0/6 | ~100 (same) |
| `caveman_full` | 0/6 | ~72 (same) |
| `caveman_full_plus_ultra_directive` | 0/6 | ~54 (same) |
| `hewn_prompt_only` | 0/6 | ~252 (same) |
| `hewn_full` | **6/6** | ~5180 (full review) |

Hewn understood the IR-shaped prompt; nothing else did.

If your re-run drifts more than ±25% on any of these summary numbers,
investigate before claiming parity. Likely causes: CLI version change,
model snapshot drift, different `~/.claude/CLAUDE.md` content, or
silent rate limit / fallback to a different model (check
`assertion_pass` field in the snapshots).

## 16. Common pitfalls (from this run)

- **Don't run `claude --bare`** to try to isolate the env: `--bare`
  requires `ANTHROPIC_API_KEY`. The whole point is OAuth-only.
- **Don't pass arm file PATHS to `--system-prompt`**: the flag takes
  CONTENT. Smoke 2 verifies this.
- **Don't pin the model with `--model opus`**: alias may resolve to a
  different model later. Use full ID `claude-opus-4-7` and check
  `modelUsage` in the response.
- **Don't measure hook overhead via `usage.input_tokens`**: it does
  NOT change. The hook injects into `cache_creation_input_tokens`.
- **Don't run two tracks (or judge + bench) in parallel against the
  same OAuth**: you may hit rate limits unexpectedly. Use the
  sequential helper scripts above. The harness is idempotent so
  resuming is safe.
- **Don't use bare `--resume` or `-c`**: capture the explicit
  `session_id` from turn 1 and pass it as `--resume <id>` for turns 2+.
- **Don't forget the system prompt on resume turns**: Claude does NOT
  persist `--system-prompt` across `--resume`. Re-pass every turn.
