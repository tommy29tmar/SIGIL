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

## Real Long-Prompt Example

Real Opus 4.7 stress-bench row. Same model, same 16k-token project handbook,
same task.

Prompt excerpt:

```text
Project handbook: Atlas API service
- Public edge must never trust client-supplied identity headers.
- Security-sensitive fixes should prefer narrow patches over broad rewrites.
- Review findings should be short but concrete: finding, exploit path,
  mitigation, verification, and main risks.
- Preserve exact literals such as "X-Forwarded-For", "Redis", "401",
  "next(err)", and "PostgreSQL".

[Task]
[capsule micro review]
anchors: "X-Forwarded-For" | "Redis"
diff: + const key=`rl:${req.headers['x-forwarded-for']||req.ip}`;
        await redis.incr(key);
ctx: public_api_gateway rate limiter
deliver: risk mitigation verify
```

| Mode | Output tokens | Latency |
| --- | ---: | ---: |
| Verbose Claude | 523 | 11.5s |
| Caveman Ultra-style | 512 | 11.2s |
| **Hewn** | **167** | **4.5s** |

Verbose Claude:

```text
finding: `X-Forwarded-For` trusted without proxy validation => spoofable
rate-limit key

exploit:
- attacker sends `X-Forwarded-For: <random>` per request -> distinct keys
  -> limiter bypassed
- attacker pins victim IP -> exhausts victim's bucket -> DoS / lockout

mitigation:
- derive client IP from trusted proxy chain only
- never read raw `x-forwarded-for` at public boundary
- key on validated IP; fall back to `req.socket.remoteAddress`
- also add `INCR` + `EXPIRE` atomically

verify:
- spoof test: 100 req with rotating `X-Forwarded-For`
- victim-pin test: forged XFF=victim.ip
- TTL test: `TTL rl:<ip>` returns >0 after first hit
- proxy-off test: with `trust proxy=false`, XFF ignored entirely

risks:
- misconfigured proxy may still reflect XFF
- IPv6 + CGNAT shared buckets
- Redis key without `EXPIRE` = unbounded memory growth
```

Caveman Ultra-style:

```text
risk: spoof `X-Forwarded-For` -> bypass per-IP limit
risk: multi-hop XFF -> only first/last hop parsed, wrong client
risk: no TTL on key -> counter never resets, permanent lockout
risk: no limit check -> `incr` without threshold compare
risk: missing IP -> key `rl:undefined` -> shared bucket all anon
risk: Redis failure -> no fallback -> limiter fails open or crashes
risk: IPv6 normalization absent -> same client, multiple keys

mitigation: trust XFF only from signed gateway contract; else use `req.ip`
mitigation: parse XFF as left-most untrusted, right-most trusted hop
mitigation: `redis.expire(key, windowSec)` on first `incr`
mitigation: compare count vs limit -> `429` when exceeded
mitigation: reject/normalize when IP absent
mitigation: wrap Redis in try/catch
mitigation: normalize IPv6

verify: spoofed `X-Forwarded-For` from public edge -> limited by real IP
verify: exact-threshold request -> allowed; threshold+1 -> `429`
verify: key TTL present after first hit
verify: missing IP -> rejected or isolated bucket
verify: Redis down -> documented behavior
```

Hewn:

```text
@hewn v0 hybrid
G: fix(rl_spoof)
C: trust_boundary ∧ "X-Forwarded-For" ∧ "Redis"
P: drop("X-Forwarded-For") ∧ bind(req.ip) ∧ expire(key)
V: test(spoof_header) ∧ test(missing_ip) ∧ test(incr_ttl)
A: ! header_spoof ∧ ! key_unbounded ∧ ? proxy_chain
```

Same risk, mitigation, and verification. Hewn compresses the answer and GCs the
context: keep what changes the fix, drop what only burns tokens.

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
