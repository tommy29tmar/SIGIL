# r/ClaudeAI post draft

**Subreddit:** https://www.reddit.com/r/ClaudeAI/

**Rules check:** r/ClaudeAI allows self-promo for free & open-source tools
with concrete Claude relevance. Keep the Claude focus explicit, include
install + usage, include a screenshot, answer questions.

**Best posting time:** Tuesday-Thursday, 9-11 AM ET or 6-9 PM ET.

## Title

> Flint: a one-line Claude Code install that cuts Opus 4.7 output tokens 4× on long-context tasks (open source, MIT)

## Flair

"Use: Claude Code" (or "Showcase" if that flair is allowed)

## Body

> I've been tuning a compact symbolic format for Claude's output that gives
> 4× fewer output tokens, 3× lower latency, and — this is the weird part —
> +9 points of concept coverage on a committed benchmark. It's called
> Flint. One-line install into Claude Code, MIT licensed, no account, no
> proxy.
>
> **The install:**
>
> ```
> curl -fsSL https://raw.githubusercontent.com/tommy29tmar/flint/main/integrations/claude-code/install.sh | bash
> ```
>
> Then in Claude Code:
>
> ```
> /flint <technical question>        # one-shot
> /output-style flint                 # every response, Flint format
> ```
>
> Turn it off anytime with `/output-style default`.
>
> **Why it's not "caveman prompting":**
>
> Caveman ("drop articles and filler") saves tokens by compressing the
> voice. On my long-context stress bench (10 coding tasks × 4 runs on Opus
> 4.7 with prompt cache), Caveman drops 2 points of concept coverage vs
> verbose Claude. It's trading quality for savings.
>
> Flint compresses the *structure* instead — five slots (Goal / Constraints
> / Plan / Verify / Action), atoms joined with `∧`. The structure is its
> own compression and its own completeness checklist.
>
> **Numbers (Opus 4.7, 40 samples per cell, prompt cache on):**
>
> | variant | output tokens | latency | concept coverage |
> | --- | ---: | ---: | ---: |
> | verbose | 736 | 15s | 86% |
> | caveman | 423 | 9s | 84% |
> | **flint** | **186** | **5s** | **95%** |
>
> vs verbose: **-75% output tokens, -65% latency, +9pt coverage.**
> vs caveman: **-56% output tokens, -44% latency, +11pt coverage.**
>
> **What it's NOT for:**
>
> Creative writing, open-ended chat, summarization. Flint wants a crisp
> technical goal. Use Claude normally for prose work.
>
> **Proof / repro:**
>
> ```
> git clone https://github.com/tommy29tmar/flint && cd flint
> cp .env.example .env && $EDITOR .env
> RUNS=4 ./scripts/run_stress_bench.sh
> python3 scripts/stress_table.py
> ```
>
> ~5 minutes, ~$2 of Opus 4.7 credits. Raw jsonl in `evals/runs/stress/`.
>
> **Repo:** https://github.com/tommy29tmar/flint
> **Methodology (honest about what it measures):** https://github.com/tommy29tmar/flint/blob/main/docs/methodology.md
> **Failure modes (where it breaks):** https://github.com/tommy29tmar/flint/blob/main/docs/failure_modes.md
>
> Happy to answer questions or take feedback. If you install it and it
> breaks on a real task, please open an issue with the `failure-mode` tag.

## Image

Include the before/after comparison image (`assets/launch/demo.png`) as
the post's image attachment. Reddit auto-thumbnails it.

## First comment (self-post immediately)

> One thing I'd love pushback on: `must_include` is a literal-retention
> proxy, not a semantic judge. The stem-matcher lets "idempot" count for
> both `idempotent` and `idempotency`, which is deliberate (see
> docs/methodology.md) but it means I can't claim "Flint is more correct" —
> only "Flint retains more listed concepts." Happy to discuss where that
> proxy breaks.
