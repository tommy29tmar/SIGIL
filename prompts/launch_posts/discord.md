# Discord share draft

For Claude Code Discord (#share-your-work or equivalent) and any Anthropic
developer community servers. Keep it short — Discord rewards brevity +
link.

## Short version (default)

> Shipped **Flint** — a one-line Claude Code install that compresses Opus
> 4.7's output into a compact symbolic IR. On long-context coding tasks
> (40 samples, prompt cache on):
>
> **186 tokens vs 736 verbose vs 423 caveman. 5s vs 15s vs 9s. +9pt concept coverage.**
>
> Install:
> ```
> curl -fsSL https://raw.githubusercontent.com/tommy29tmar/flint/main/integrations/claude-code/install.sh | bash
> ```
> Then `/output-style flint` in any session. MIT, no account, no proxy.
>
> Repo: <https://github.com/tommy29tmar/flint>
> Methodology: <https://github.com/tommy29tmar/flint/blob/main/docs/methodology.md>

*(attach: `assets/launch/demo.png` — the before/after comparison is the
hook here)*

## Longer variant (if the channel allows full posts)

> **Flint** — compact symbolic IR for Claude's output. One install, MIT.
>
> The one-liner:
> - Caveman prompting (drop articles) saves ~40% tokens but drops 2pt of
>   concept coverage.
> - Flint saves ~75% tokens and *gains* 9pt of coverage, because the
>   5-slot format (Goal / Constraints / Plan / Verify / Action) is its
>   own completeness checklist.
>
> Bench: 10 long-context coding tasks × 4 runs on Opus 4.7 with prompt
> cache active. Raw jsonl in the repo.
>
> Install:
> ```
> curl -fsSL https://raw.githubusercontent.com/tommy29tmar/flint/main/integrations/claude-code/install.sh | bash
> ```
>
> Use:
> - `/flint <your question>` — one-shot
> - `/output-style flint` — every response, Flint format
> - `/output-style default` — off
>
> Not for creative writing / open chat / summarization — use Claude
> normally for those.
>
> Repo: <https://github.com/tommy29tmar/flint>
> Methodology & failure modes docs live under `docs/`.
>
> Pinging if you try it and hit anything weird.

## Reply-ready one-liners for thread answers

If someone asks "is this just caveman?":

> No. Caveman saves tokens by dropping articles — voice compression. On
> long-context tasks it also drops ~2pt of concept coverage. Flint
> compresses structure (5-slot format), which is its own completeness
> checklist, and gains 9pt of coverage. Table in the repo.

If someone asks "Claude Code already has skills, what's new?":

> Skill is just the installer. The actual artifact is a ~90-token system
> prompt you can paste into any Messages API call. The skill is one
> convenient delivery mechanism.

If someone asks "does it help agent loops?":

> That's its best case. The stress bench uses ~10k-token context with
> prompt cache active — which is agent-loop shape. Verbose Claude grows
> with context; Flint stays 6 lines.

## Don't

- Don't cross-post the full HN body. Discord readers are lower-attention.
- Don't link more than 3 URLs — Discord auto-collapses.
- Don't tag @Anthropic staff asking for a retweet. Zero upside, real risk.
