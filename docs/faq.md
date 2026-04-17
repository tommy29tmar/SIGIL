# FAQ

Fast answers to the most common questions about Flint. If you want the full
story, the three companion docs go deeper:
[methodology](methodology.md), [architecture](architecture.md),
[failure modes](failure_modes.md).

---

## Why not just use Caveman prompting?

Caveman tells Claude to drop articles, fillers, and pronouns — you get ~40%
shorter output, and that's real. But Caveman also drops *concepts*: in the
long-context stress bench, Caveman answers cover **84%** of must-have
concepts, vs **95%** for Flint and **86%** for verbose Claude. Caveman is a
voice trick. Flint is a structural one. The structure is its own
compression and its own checklist.

## 10 tasks isn't much. How confident should I be?

Fair. It's **40 samples per cell** (10 tasks × 4 runs), not 10. Stdev
columns are published. The effect sizes (4× fewer tokens, 3× less latency,
+9pt coverage) are large enough that run-to-run noise doesn't flip the
ranking. Reproduction takes 5 minutes and ~$2 of Opus 4.7 credits; PRs with
extended corpora welcome.

## Isn't `must_include` a weak quality proxy?

Yes. It's a *literal-retention proxy*, not a semantic-correctness grade.
It's honest about what it measures: whether the answer mentioned the right
concepts. A semantic LLM-judge eval is on the roadmap but every judged eval
is itself unverifiable, so we shipped the deterministic version first.
Every run writes raw `.jsonl` — eyeball it yourself.

## Claude Code already has skills. Why should I care?

The skill is just the installer. The actual artifact is a ~90-token system
prompt (`integrations/claude-code/flint_system_prompt.txt`) that works via
any Anthropic-compatible Messages API. You can use it without Claude Code —
the skill is one convenient delivery mechanism.

## Does it work on Sonnet? Haiku? GPT? Gemini?

The shipped prompt is tuned for Opus 4.7. Earlier cross-model data showed
Flint winning on Sonnet 4.6 (-24% tokens, -52% latency, +8pt coverage) and
Opus 4.6 (-47% tokens, -68% latency, -6pt coverage). Sonnet 4 showed modest
token savings (-3%) but large latency gains (-44%) and a big coverage
improvement.

Non-Anthropic providers: the prompt is provider-agnostic in principle, but
cache semantics differ across OpenAI/Google, and only Anthropic has been
validated. Treat cross-provider claims as untested until you run the bench.

## Does this work with tool use?

Tool use is orthogonal. Flint compresses the response layer; tool_use
compresses nothing (it *adds* a ~1.4k-token tool schema). Earlier
experiments (`local/flint5-tool/`, preserved in git history) showed
tool_use worked only in long-context cached scenarios and was unreachable
from skills. If you want the cleanest story today: use Flint for response,
keep tool_use for its own orthogonal purposes.

## Will Flint hurt creative or open-ended writing?

Yes. That's why it's opt-in per-turn (`/flint <q>`) or per-session
(`/output-style flint`), and explicitly off by default. Flint is for crisp
technical questions with a verifiable endpoint. Use Claude normally for
essays, brainstorming, back-and-forth chat. See
[failure_modes.md](failure_modes.md) for the full list.

## How is this different from JSON mode / structured output?

JSON mode forces the *wrapper* to be structured but doesn't reduce output
tokens — in practice it often *inflates* them, because JSON's punctuation
and repeated keys add bytes. Flint compresses the content: atoms plus one
operator, no field names repeated, no quotes except on literals. Also,
Flint keeps an optional `[AUDIT]` trailer that's plain prose — JSON mode
kills the prose path entirely.

## Why `∧` and not `&` or just commas?

`∧` is a single visually-distinct character that can't be confused with
code. The Unicode salience tells the model "this is the IR, not prose".
For models that mangle Unicode we ship an ASCII fallback
(`&`, `=>`, `->`) documented in
[`grammar/flint_ascii.md`](../grammar/flint_ascii.md) — the normalizer
swaps them silently. Not religious about the operator; religious about one
operator.

## Isn't this just Markdown with extra steps?

Markdown has no grammar, no parser, no verifier, and no repair layer. Flint
has all four — EBNF at [`FLINT_GRAMMAR.ebnf`](../FLINT_GRAMMAR.ebnf),
stdlib-only parser at `src/flint/parser.py`, verifier at
`src/flint/verification.py`, normalizer at `src/flint/normalize.py`. The
difference is whether you can mechanically *check* that the model produced
a well-formed, concept-covering answer. With Markdown, you can't.

## Does it save input tokens too, or only output?

Only output. The system prompt is ~90 tokens extra on every call (amortized
by prompt cache after call 1). The user message is unchanged. The wins all
come from output-side compression. That's fine: output tokens are where
the money and latency hide — Anthropic's Opus 4.7 pricing makes output
5× more expensive than input, and output is what streams sequentially.

## Is this safe to use on production / client workloads?

The *format* is safe — it's a deterministic text transformation with no
network side effects. The *content* comes from Claude, same as any other
prompt. Read [failure_modes.md](failure_modes.md) before using it on
anything high-stakes. For code review / debugging / architecture sketches
it's been validated on the committed bench. For legal, medical, or
financial content: use plain prose and a human reviewer — Flint isn't
what you want.

## What happens if the model drifts off format?

The repair layer catches the common cases (whitespace, case, unicode,
preamble strips). Rare schema failures (< 2% on Opus 4.7 in the stress
bench) fall through to the verifier, which tells you exactly what broke.
See [failure_modes.md#drift-patterns](failure_modes.md#drift-patterns) for
the full taxonomy.

## What's on the roadmap?

- Semantic (LLM-judge) quality eval alongside `must_include`.
- Cross-provider replication harness (OpenAI Responses API, Google Gemini).
- Agent-loop integration where the IR carries state across turns.

No promised dates. If you want to move any of these forward, open an issue
or a PR.

## License?

MIT. If you cite Flint in research, see [CITATION.cff](../CITATION.cff).
