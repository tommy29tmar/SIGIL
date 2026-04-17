# r/LocalLLaMA post draft

**Subreddit:** https://www.reddit.com/r/LocalLLaMA/

**Rules check:** r/LocalLLaMA tolerates proprietary-model content when the
*technique* is transferable / reproducible and the post is methodology-heavy.
**Lead with methodology, not hype.** This audience smells AI marketing
fluff from three subreddits away. Technical detail, honest caveats,
reproducible numbers.

**Best posting time:** Saturday-Sunday morning UTC (international audience),
or Tuesday-Wednesday 10 AM-12 PM ET.

## Title

> Prompt-level output compression: 4× fewer output tokens on long-context coding (methodology + repro)

*(Notice: no "show", no product-name-first. Methodology framing earns
this audience's engagement.)*

## Body

> I've been benching a prompt-level compression technique and the numbers
> hold up well enough that I want pushback before I over-commit to them.
> Open source, MIT, no vendor lock-in.
>
> **Setup:** 10 long-context coding tasks (debug, security review,
> architecture, refactor) each carrying ~10k tokens of shared project
> handbook context (simulating a real agent/RAG loop). 4 runs per cell,
> 40 samples per cell. 3 cells: verbose baseline, "caveman" (primitive-
> English prompt), and my format ("Flint"). Target model: Claude Opus 4.7
> via Anthropic Messages API, prompt cache active on system + task prefix.
>
> **What Flint is, technically:**
>
> - ~90-token system prompt that instructs the model to emit a 6-line IR:
>   `G: goal / C: constraints / P: plan / V: verify / A: action`, atoms
>   joined with `∧`, optional `[AUDIT]` prose trailer.
> - EBNF grammar (strict); stdlib Python parser; normalizer that repairs
>   common drift (whitespace, casing, unicode→ASCII fallback); verifier
>   that checks slot completeness + literal anchor retention.
> - No fine-tuning. No tool-use. Single system prompt. Works on the raw
>   Messages API — the "skill" layer is just a convenient installer for
>   Claude Code users.
>
> **Results (40 samples/cell, Opus 4.7, Apr 2026):**
>
> | variant | output tok | latency | must_include coverage |
> | --- | ---: | ---: | ---: |
> | verbose baseline | 736 ±28 | 15s ±1 | 86% ±1 |
> | caveman (prim-english) | 423 ±18 | 9s ±0 | 84% ±4 |
> | flint (structural IR) | **186 ±10** | **5s ±0** | **95% ±4** |
>
> **Interpretation:**
>
> 1. Caveman saves tokens by compressing the voice layer. On long context
>    it's not enough: ~40% token savings, but a 2pt coverage drop.
> 2. Flint compresses the structure layer. At this scale, structure is its
>    own completeness checklist — the model can't close the format without
>    filling all five slots, which correlates with must_include retention.
> 3. Concept coverage ↑ despite tokens ↓ is the counterintuitive bit.
>    Verbose Claude spends a large fraction of tokens on transitions
>    ("to fix this, you'll want to consider..."), none of which carry
>    must_include weight. Flint's atoms per token ratio is much higher.
>
> **What I'm NOT claiming:**
>
> - This is not a semantic correctness result. `must_include` is stem-
>   matched literal retention. LLM-judge eval is on the roadmap but I'm
>   not shipping a judged number without the judge being auditable.
> - Cross-provider untested. Anthropic prompt cache semantics don't
>   transfer to OpenAI / Gemini. If the structural compression helps,
>   the *ratio* will change on other providers. Open to PRs.
> - Not a Claude Code trick — the actual artifact is the system prompt.
>   Any Messages-API-compatible endpoint can serve it.
>
> **Known failure modes:** short prompts with no context (the ~90-token
> overhead isn't amortized), open-ended/creative tasks (nothing to
> structure), and non-Opus models (smaller effect, see git history for
> pre-cleanup cross-model data on Sonnet 4, Sonnet 4.6, Opus 4.6).
>
> **Repro (5 min, ~$2 on Opus 4.7):**
>
> ```bash
> git clone https://github.com/tommy29tmar/flint && cd flint
> cp .env.example .env && $EDITOR .env    # ANTHROPIC_API_KEY
> pip install -e .
> RUNS=4 ./scripts/run_stress_bench.sh
> python3 scripts/stress_table.py
> ```
>
> **Repo:** https://github.com/tommy29tmar/flint
> **Full methodology doc:** https://github.com/tommy29tmar/flint/blob/main/docs/methodology.md
> **Failure modes:** https://github.com/tommy29tmar/flint/blob/main/docs/failure_modes.md
> **The prompt itself (~90 tokens):** https://github.com/tommy29tmar/flint/blob/main/integrations/claude-code/flint_system_prompt.txt
>
> Would particularly value pushback on:
> - whether stem-matching for `must_include` is a defensible proxy
> - whether there's a fairer caveman-style baseline I should add
> - whether anyone has replicated this on Qwen 3 / DeepSeek / Llama 4
>   (I'd love to port the bench if someone has credits)

## First comment (self-post immediately)

> One measurement detail worth flagging: concept coverage uses stem
> matching ("idempot" matches both "idempotent" and "idempotency",
> "semver" matches both the word and `semver("1.0.0")`). Without stems,
> any symbolic format loses to prose on the prose's own vocabulary — which
> is a measurement artifact, not a real gap. The stems are committed in
> the task file; disagree and open a PR.
