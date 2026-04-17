# Methodology

How the benchmark behind the README numbers works — what it measures, what it
doesn't, and why the numbers shake out the way they do.

## The claim

On Claude Opus 4.7, with ~10k tokens of project-handbook context loaded per
call, Flint produces answers that are:

- **4× shorter** than verbose Claude (186 vs 736 output tokens)
- **3× faster** than verbose Claude (5s vs 15s wall-clock)
- **+9 concept points vs verbose** and **+11 vs Caveman** (95% vs 86% / 84%)

That's three wins in three columns against two baselines, on 40 samples per
cell.

## The bench shape

**Corpus:** `evals/tasks_stress_coding.jsonl` — 10 long-context coding tasks
across four categories:

- debugging (3): `debug-auth-expiry`, `debug-memory-leak-node`, `debug-query-n-plus-one`
- architecture (3): `arch-small-team`, `arch-audit-log-schema`, `arch-idempotent-webhook`
- code review (2): `security-review-header-auth`, `review-rate-limit-bypass`
- refactoring (2): `refactor-callback`, `refactor-extract-shared-lib`

Each task carries:

- a ~10k-token **project handbook prefix** (Atlas API backend conventions,
  trust boundaries, style rules) — this is the shared cache_prefix that
  simulates a real Claude Code / RAG / agent loop
- a specific question
- a `must_include` list of 3–4 technical concepts that any correct answer
  should touch

**Prompt caching is on**, so the handbook is charged at the cached rate
(~10% of input cost) after the first call per cell. This is the shape of
production usage: the same system/context is seen repeatedly, and only the
task tail changes.

**Three cells per model:**

| cell | system prompt | what it tests |
| --- | --- | --- |
| verbose | `prompts/verbose_baseline.txt` ("helpful AI coding assistant") | Claude's default verbosity |
| caveman | `prompts/primitive_english.txt` | the popular "drop articles, no filler" trick |
| flint   | `integrations/claude-code/flint_system_prompt.txt` | the actual artifact the installer ships |

**Runs:** 4 runs per cell × 10 tasks = **40 samples per cell**, 120 total.

**Model:** `claude-opus-4-7`, Anthropic Messages API.

Reproduction:

```bash
RUNS=4 ./scripts/run_stress_bench.sh
python3 scripts/stress_table.py
```

## What we measure

### 1. Output tokens

Raw `usage.output_tokens` from the Anthropic response. This is what you pay
for per answer. Mean across 40 samples, ± population stdev across runs.

### 2. Wall-clock latency

Time from request send to final chunk received. Includes network RTT and
streaming. Reported as seconds to the nearest integer because second-scale
differences are what a human actually feels.

### 3. Concept coverage (must_include)

For each task, we define 3–4 `must_include` literals — short technical
concept stems (e.g. `idempot`, `semver`, `trust_boundary`, `rate_limit`) —
and count the fraction of stems that appear as substrings in the answer.

**Stemming is deliberate.** Flint writes `idempotent_key` as a snake_case
atom; verbose Claude writes "the key should be idempotent". Matching
`idempotent` exactly would require Flint to mimic prose; stemming on
`idempot` lets any well-formed answer — prose, cave, or symbolic — count if
the concept is actually there. Without stemming, any structural format looks
worse than prose on its own surface vocabulary, which is a measurement
artifact, not a real gap.

See `src/flint/verification.py` for the exact matcher. The stems are
committed in `tasks_stress_coding.jsonl` — you can read them, disagree with
them, and open a PR.

## What we do *not* measure

- **Semantic correctness.** `must_include` is a *literal-retention proxy*.
  It tells us "the model mentioned the right concepts"; it doesn't tell us
  "the suggested fix actually works." A semantic LLM-judge eval is on the
  roadmap, but every judged eval is itself unverifiable, so we shipped the
  measurable version first.
- **End-to-end Claude Code cost.** Claude Code adds its own system prompts
  and tool loops we don't control. This bench measures the Flint system
  prompt on the raw Messages API, which is what the skill injects.
- **Open-ended or creative tasks.** Flint is explicitly for crisp technical
  questions. We don't benchmark it on "write me an essay about X" because
  it's not the right tool for that. Use Claude normally for open prose.

## Why Flint wins on concept coverage

Intuitively this sounds wrong: a shorter answer should cover fewer concepts.
In practice the opposite happens for two reasons:

1. **Verbose Claude buries concepts in transition text.** In a 736-token
   answer, a lot of tokens go to "To fix this, you'll want to consider
   several factors…" — none of which are must_include keywords. Flint's
   slot structure forces every atom to be a concept, so atoms per token is
   much higher.
2. **Caveman drops structure alongside articles.** Telling Claude to drop
   "the", "a", "is" doesn't improve information density — it just compresses
   the prose layer. On long tasks Caveman's output rambles the same
   concepts in fewer words, and sometimes skips a concept to end quickly
   ("minimal diff", one of the must_include stems on the debug tasks, is
   the most frequent Caveman miss).

Flint's 5 slots (G/C/P/V/A) are a checklist in disguise: the format won't
close cleanly if you forget to state a goal, a constraint, a plan, a
verification, or an action. Structure is compression *and* completeness in
one move.

## Why Opus 4.7 not Opus 4.6

Opus 4.6 posts a bigger token delta (it's wordier by default), but 4.7 is
the launch context. 4.7's baseline is already tighter, so the *ratio* is
smaller — and that's exactly why the win matters: Flint wins even against a
model that's already optimized for concise output.

Cross-model data (Sonnet 4, Sonnet 4.6, Opus 4.6, Opus 4.7) is in the git
history before commit `7a236d0`. It was pruned from the tracked tree during
the cleanup so this repo can ship one corpus, one story, one number — but
the raw jsonl rows are recoverable from prior commits if you need them.

## Reproducing the exact numbers

```bash
git clone https://github.com/tommy29tmar/flint && cd flint
cp .env.example .env && $EDITOR .env    # add ANTHROPIC_API_KEY
pip install -e .
RUNS=4 ./scripts/run_stress_bench.sh     # ~5 min, ~$2 on Opus 4.7
python3 scripts/stress_table.py
```

Expected table, numbers within ±10 tokens due to model sampling variance:

| variant       | output   | latency | must_include |
| ------------- | -------: | ------: | -----------: |
| verbose       | 736 ±28  | 15s ±1  | 86% ±1       |
| caveman       | 423 ±18  |  9s ±0  | 84% ±4       |
| flint         | 186 ±10  |  5s ±0  | 95% ±4       |

`RUNS=2` gives the same means with wider error bars and cuts cost roughly
in half.

## Statistical disclaimers

- 40 samples per cell is **enough to see a large effect, not enough for a
  formal significance test.** The stdev columns give you the spread; the
  effect sizes here (4× tokens, 3× latency, +9pt coverage) are large enough
  that noise doesn't flip the ranking.
- One corpus, one model, one provider. The claim is bounded to what was
  actually measured. Cross-model and cross-provider replications are
  welcomed — see [CONTRIBUTING.md](../CONTRIBUTING.md) for how to publish
  benchmark additions.
- No LLM judge. Concept coverage uses deterministic substring matching
  against a committed stem list. It's the honest version of what can be
  measured without an unaccountable grader.

If any of these bother you, the corpus is 10 tasks, the bench runs in 5
minutes, and every run writes raw `.jsonl` that you can eyeball.
