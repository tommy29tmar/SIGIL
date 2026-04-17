# Canned replies — top-10 predicted objections

Paste these into HN / X / Reddit / Discord when the predictable objection
arrives. Each is short (2-4 sentences), concrete, with a file/line
reference or a reproducible command.

Style rules:

- Answer the question, then link.
- Don't argue. If they're right, say "fair, here's what I'd change".
- No "great question!". No emojis unless the channel culture is emoji-heavy.
- Short. Four lines max per reply.

---

## 1. "Why not just use Caveman prompting?"

> Caveman compresses the voice layer — ~40% fewer tokens — but on long
> context it drops ~2pt of concept coverage vs verbose Claude. Flint
> compresses the structure layer (5 slots + `∧`) which is its own
> completeness checklist and gains 9pt of coverage while cutting another
> 56% of tokens. Table in README, full comparison in
> [docs/faq.md](https://github.com/tommy29tmar/flint/blob/main/docs/faq.md#why-not-just-use-caveman-prompting).

---

## 2. "10 tasks isn't enough."

> It's 40 samples per cell (10 tasks × 4 runs). Stdev columns are
> published. Effect sizes (4× tokens, 3× latency, +9pt coverage) are much
> larger than run-to-run noise. Repro is `RUNS=4 ./scripts/run_stress_bench.sh`
> — 5 minutes and ~$2 of Opus 4.7. PRs with extended corpora welcome.

---

## 3. "must_include isn't a real quality measure."

> Correct — it's a literal-retention proxy, called out explicitly in
> [docs/methodology.md#what-we-do-not-measure](https://github.com/tommy29tmar/flint/blob/main/docs/methodology.md#what-we-do-not-measure).
> Semantic LLM-judge eval is on the roadmap. I chose deterministic
> substring matching because every judged eval is itself unverifiable; I'd
> rather ship the honest partial measurement than a confident-sounding one
> nobody can reproduce.

---

## 4. "Why should I care? Claude Code already has skills."

> The skill is just the delivery mechanism. The artifact is a ~90-token
> system prompt (`integrations/claude-code/flint_system_prompt.txt`) that
> works via any Anthropic Messages API call. You can use it without
> Claude Code entirely — it's provider-agnostic by design.

---

## 5. "Does it work on Sonnet / GPT / Gemini / open models?"

> Shipped prompt is tuned for Opus 4.7. Pre-cleanup bench data (recoverable
> from git history at commit 7a236d0) showed Flint winning on Sonnet 4.6
> (-24% tokens, +8pt coverage) and Opus 4.6 (-47% tokens, -6pt coverage).
> Cross-provider is untested — prompt cache semantics differ. PR with a new
> provider's numbers is the best way to expand the claim.

---

## 6. "Isn't this just Markdown with extra steps?"

> Markdown has no grammar, no parser, no verifier, no repair layer. Flint
> has all four: [EBNF](https://github.com/tommy29tmar/flint/blob/main/FLINT_GRAMMAR.ebnf),
> stdlib parser at `src/flint/parser.py`, verifier at
> `src/flint/verification.py`, normalizer at `src/flint/normalize.py`. The
> difference is whether you can mechanically *check* that the model's
> answer is well-formed and concept-complete.

---

## 7. "JSON mode / structured output already does this."

> JSON mode structures the wrapper but doesn't reduce tokens — in practice
> it inflates them because keys repeat. Flint compresses content: atoms +
> one operator, no field names, no quotes except on literals. Flint also
> keeps an optional `[AUDIT]` prose trailer that JSON mode kills entirely.

---

## 8. "Why the Unicode `∧`? Use `&` and stop being fancy."

> Fair taste call. The reason for `∧`: visually distinct from code, so the
> model treats it as IR, not prose. For models that mangle Unicode we ship
> an ASCII fallback (`&`, `=>`, `->`) documented in
> [`grammar/flint_ascii.md`](https://github.com/tommy29tmar/flint/blob/main/grammar/flint_ascii.md).
> The normalizer swaps them silently. Pick one, either works.

---

## 9. "Won't this kill Claude's reasoning / CoT?"

> It bounds reasoning to a 5-slot shape instead of free-form prose. On
> technical tasks with a clear goal, that's an improvement — the structure
> is the reasoning scaffold. On open-ended / creative tasks it *would*
> hurt, which is why Flint is opt-in (`/flint` per-turn or
> `/output-style flint` per-session) and explicitly off by default. Full
> scope in [docs/failure_modes.md](https://github.com/tommy29tmar/flint/blob/main/docs/failure_modes.md).

---

## 10. "What about tool use / agent loops?"

> Tool use is orthogonal — Flint compresses the response; tool_use adds a
> ~1.4k-token tool schema. I ran a tool_use variant earlier (preserved at
> `local/flint5-tool/` in my working tree, research notes in git history);
> it only wins at long-context-cached scale and is unreachable from Claude
> Code skills. Flint's text path is the simpler, more portable story.

---

## Bonus: if somebody accuses you of astroturfing

> I'm solo on this, no team, no VC, no marketing. I posted because I built
> it and I want feedback. Happy to answer anything — including on whether
> I'm right that this is worth releasing.

---

## Bonus: if a pricing question comes up

> MIT licensed, free, no account, no proxy, no telemetry. The only cost is
> your own Anthropic API bill, which this is designed to *reduce*.

---

## When NOT to reply

- Low-effort dunk comments ("this is stupid", "hype"). Silence is louder.
- People telling you the readme could be clearer — just fix the readme.
- Threads that have drifted to an argument between two other people.
  Don't enter someone else's fight.
- Comments posted 48+ hours after the launch. The moment has passed;
  responding late looks needy.
