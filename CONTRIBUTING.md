# Contributing to Flint

Flint is trying to answer one concrete question:

> Can we compile LLM work into tighter contracts that reduce token use without
> sacrificing quality?

The best contributions are the ones that make that question easier to answer.

## High-value contribution areas

- new benchmark corpora with realistic, self-contained tasks
- provider- or model-specific transport contracts
- runtime repair and canonicalization improvements
- better benchmark methodology and reporting
- context compilation and cache-aware serving experiments
- integrations with real agent workflows

## Development workflow

1. Install the package:

```bash
python -m pip install -e .
```

2. Run the test suite:

```bash
python -m unittest discover -s tests -q
```

3. If your change affects benchmarks, include:

- the task set used
- provider and model
- exact commands
- the resulting `.jsonl` artifacts when they support a published claim

## Benchmark hygiene

- do not overwrite published benchmark rows casually
- prefer new named directories under `evals/runs/` for publishable results
- keep scratch runs out of the repo; `tmp_*.jsonl` and `*smoke*.jsonl` are ignored

## Pull requests

Good PRs are narrow and falsifiable. They should explain:

- what changed
- why it changed
- what evidence supports it
- what tradeoff worsened, if any

If a change improves one provider but hurts another, say it explicitly.
