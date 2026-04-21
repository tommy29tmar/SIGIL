# Hewn

| Mode | Output tokens | Latency | Concepts covered |
| --- | ---: | ---: | ---: |
| Verbose Claude | 736 | 15s | 86% |
| Caveman | 423 | 9s | 84% |
| **Hewn** | **186** | **5s** | **95%** |

why burn many token when few do job

**Claude talks too much. Hewn makes it get to the point.**

Same useful answer. Less token burn. More context kept.

No proxy. No telemetry. Default `claude` untouched.

Launch bench: 10 long-context tasks x 4 runs, prompt cache on. "Concepts
covered" means required points from the prompt were still present in the
answer.

## Before / After

Normal Claude:

> The issue is likely caused by the authentication middleware not correctly
> validating token expiry. You should check whether the comparison allows an
> already-expired token through, then add a regression test around the boundary
> condition to make sure this does not happen again.

Hewn:

> Auth expiry check likely off by one. Fix boundary compare. Add regression
> test for expired token.

**Same point. Fewer words. Brain still on.**

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/tommy29tmar/hewn/main/integrations/claude-code/install.sh | bash
```

## Use

```bash
hewn
hewn -p "your prompt"
```

Want normal Claude again?

```bash
claude
```

Hewn is a separate command. It never replaces `claude`.

## What It Does

- Cuts filler.
- Keeps answers tight.
- Uses compact structure when structure saves more.
- Keeps polished prose when you ask for polished prose.
- Works inside Claude Code with one wrapper command.

## Why Not Just Caveman?

Caveman makes Claude talk shorter.

Hewn makes Claude waste less while keeping more context.

The launch bench above is the short version: Caveman reduces output. Hewn
reduces output further while covering more of what the prompt asked for.

Caveman compresses voice. Hewn compresses the answer: fewer tokens, more of
the required context preserved.

## Best For

- Claude Code sessions
- Opus 4.7 token burn
- Long prompts
- Debugging
- Reviews
- Planning
- Anything where Claude starts writing a wall of text

If you want expansive creative writing, use normal `claude`.

## What Gets Installed

- `~/.local/bin/hewn`
- `~/.claude/hewn_thinking_system_prompt.txt`
- `~/.claude/hooks/hewn_drift_fixer.py`

That is it.

## Under The Hood

Hewn wraps:

```bash
claude --append-system-prompt <hewn prompt> --settings <temp hook config>
```

The prompt keeps Claude terse. The hook re-injects the right answer shape every
turn so long sessions do not drift back into bloated prose.

Technical tasks may route into a tiny IR:

```text
@hewn v0 hybrid
G: goal
C: constraints
P: plan
V: verify
A: action
```

Most users do not need to care. Run `hewn`; Claude gets shorter.

## Uninstall

```bash
rm -f ~/.local/bin/hewn \
      ~/.claude/hewn_thinking_system_prompt.txt \
      ~/.claude/hooks/hewn_drift_fixer.py
```

## License

MIT. See [LICENSE](LICENSE).
