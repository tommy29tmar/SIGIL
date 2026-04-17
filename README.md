# Flint

**Caveman prompts. Flint delivers.**

On realistic coding workloads — codebases, CLAUDE.md loaded, RAG context — Claude writes answers **3× shorter, 2× faster, covering 23 more concept points** than verbose Claude. And it beats "Caveman prompting" on every metric that matters.

![demo](assets/launch/demo.png)

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/tommy29tmar/flint/main/integrations/claude-code/install.sh | bash
```

Then in Claude Code:

```
/flint <your technical question>     # one-shot
/output-style flint                   # every response, Flint format
```

Turn it off: `/output-style default`.

## Why it works

Most token-saving tricks save tokens by telling Claude to drop words. That works until Claude also drops the concepts you needed.

Flint doesn't compress the words. It compresses the **shape** of the answer into 5 slots:

- **G** — the goal
- **C** — the context and constraints
- **P** — the plan
- **V** — how to verify it
- **A** — the action to take

One operator, `∧`. Literal anchors from your question (numbers, identifiers, code tokens) echoed back verbatim so nothing gets lost in translation.

That's it. Six lines. Same concepts. Fewer tokens. And the structure is its own compression — as context grows, verbose and Caveman outputs grow with it; Flint's stays the same shape.

## Proof

Benchmark on Claude Opus 4.7, 4 realistic coding tasks (debug, architecture, security review, refactor) with ~18k tokens of project-handbook context loaded per call — the shape of a real Claude Code / RAG / agent session with prompt cache active. 2 runs per cell.

| approach                      | output tokens | latency | concepts covered |
|-------------------------------|--------------:|--------:|-----------------:|
| Claude default (verbose)      |           518 |   11.9s |              71% |
| Caveman ("primitive English") |           400 |    9.0s |              69% |
| **Flint**                     |       **168** | **4.9s** |          **94%** |

Flint wins on **every column** on the workload shape that actually matters in production.

- vs verbose Claude: **-68% output tokens, -59% latency, +23pt concept coverage**
- vs Caveman: **-58% output tokens, -46% latency, +25pt concept coverage**

## Flint vs Caveman

"Caveman prompting" tells Claude to drop articles and filler. On short Q&A it saves tokens. But on real work — multi-file diffs, codebase review, long agent loops — Caveman has no ceiling on its output. It keeps rambling in "primitive English" and ends up only 23% shorter than verbose Claude while covering fewer concepts.

Flint replaces the "no articles" discipline with a **structural** one: five slots (Goal, Constraints, Plan, Verify, Action), atoms joined by `∧`. The structure is its own compression. Give Flint more context and it stays 6 lines. Give Caveman more context and it writes more cave.

## When things drift

Claude sometimes drifts off format. Flint ships with a parser, a repair layer, and `flint audit --explain` that shows you exactly what came in, what was repaired, which anchors matched, and a prose rerender — so you can trust the output even on the worst cases.

```bash
flint audit --explain response.flint --anchor 300 --anchor 401
```

## More CLI tools

```bash
# Look up which variant a calibration profile recommends for a task or category
flint routing recommend --profile profiles/<profile>.json --category debugging

# Per-file CLAUDE.md audit — structurally-safe compression preview (read-only)
flint claude-code inventory path/to/CLAUDE.md
flint claude-code diff path/to/CLAUDE.md
```

See [integrations/claude-code/README.md](integrations/claude-code/README.md) for the full list of preserved segment types and caching behavior.

## Reproduce the numbers

```bash
git clone https://github.com/tommy29tmar/flint && cd flint
cp .env.example .env && $EDITOR .env      # ANTHROPIC_API_KEY
./scripts/run_stress_bench.sh              # 2 runs per cell, ~2 min
python3 scripts/stress_table.py
```

Set `RUNS=4` for tighter confidence intervals. Full methodology and cross-model data in [docs/research.md](docs/research.md).

## Honest scope

Flint shines on crisp technical asks: debug this, review this diff, refactor this function, sketch this architecture. It's not for open-ended writing. Use Claude normally for that.

## License

MIT. If you cite Flint in research, see [CITATION.cff](CITATION.cff).
