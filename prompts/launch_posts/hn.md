# Show HN draft

## Title (HN guideline: "Show HN: X – Y", < 80 chars)

Preferred:

> Show HN: Flint – a 90-token prompt that makes Claude 4× shorter and more accurate

Backups (pick if the one above gets pushback for "sounds too marketing-y"):

> Show HN: Flint – cut Claude Opus 4.7 output tokens 75% on long-context tasks
> Show HN: Flint – a compact IR for Claude, wins on tokens, latency, and concept coverage

## URL

https://github.com/tommy29tmar/flint

## First comment (post immediately after submitting — HN convention)

> Hi HN. Author here. Flint is one file — a ~90-token system prompt — that
> makes Claude Opus 4.7 answer technical questions in a compact symbolic IR
> (`G: goal / C: constraints / P: plan / V: verify / A: action`, atoms
> joined by `∧`).
>
> Why I built it: "Caveman prompting" (tell Claude to drop articles) saves
> tokens by compressing the *voice*, but on long-context workloads it also
> drops concepts — our bench shows it loses 2 points of concept coverage
> vs verbose Claude. I wanted to see if you could compress the *structure*
> instead, and end up with something that wins on every column.
>
> The stress bench: 10 long-context coding tasks (debug, security review,
> architecture, refactor) × 4 runs × 3 variants (verbose / Caveman / Flint)
> on Opus 4.7 with prompt cache active. Numbers:
>
> - Verbose: 736 output tokens, 15s, 86% concept coverage
> - Caveman: 423 output tokens, 9s, 84% concept coverage
> - Flint:   186 output tokens, 5s, 95% concept coverage
>
> Flint wins all three columns, vs both baselines, on the workload shape
> that matches production Claude Code / RAG / agent loops.
>
> Concept coverage is stem-matching against committed must_include lists;
> it's a literal-retention proxy, not a semantic judge, and I'm explicit
> about that in docs/methodology.md. Every run writes raw jsonl you can
> eyeball; reproduction is `RUNS=4 ./scripts/run_stress_bench.sh` + a table
> script, ~5 min and ~$2 on Opus 4.7.
>
> Install is `curl | bash` into `~/.claude`; turns on via `/output-style
> flint` in Claude Code, or you can use the ~90-token prompt directly via
> any Anthropic Messages API call.
>
> Happy to answer anything — particularly keen on methodology pushback.

## Notes for posting

- HN has no "tags" — quality of title + early comment dominates.
- Post between **8-10 AM PT on a Tuesday/Wednesday/Thursday**. Avoid weekends.
- Post the repo URL as the main link, not a blog post. HN prefers direct.
- Check the first 3 comments within 10 minutes. Answer, don't argue.
- If a comment corrects something, edit the post/comment promptly and say so.
- Do **not** ask friends for upvotes. HN's anti-ring detection will kill it.
- If it lands on the front page, expect 4-8 hours of heavy comments. Stay.

## Things to have ready in the repo before posting

- [x] README hero image (conceptA) wired
- [x] docs/methodology.md, architecture.md, failure_modes.md, faq.md live
- [x] Installer passes (tested via HOME override)
- [x] Tests green (73/73)
- [ ] Canned replies file open in another tab (canned_replies.md)
- [ ] GitHub social preview image set in repo settings (use hero.jpg)
