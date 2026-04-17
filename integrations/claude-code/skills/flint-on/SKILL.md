---
name: flint-on
description: Turn on Flint output mode for the rest of this conversation. From this turn onward every response is a Flint IR document, until the user types /flint-off or asks for prose explicitly.
---

The user has activated **Flint mode** for this conversation.

From this turn onward, answer **every** turn in Flint format:

```
@flint v0 hybrid
G: <goal atom>
C: <context atoms joined with ∧>
P: <plan atoms with ∧>
V: <verification atoms with ∧>
A: <action atoms with ∧>
```

Format rules (must hold for every Flint response in this conversation):

- 5–6 short lines, nothing else.
- Use short `snake_case` atoms.
- Prefer call form `ddl("12 weeks")` over suffix `ddl_"12 weeks"`.
- Echo literal anchors from the user's question verbatim when present
  (numbers, identifiers, code tokens, quoted strings — keep them as-is).
- Connect conjunctions with `∧` only. No commas. No bullets.
- Stop after the `A:` line. No audit block unless explicitly asked.

Mode control:

- The user types `/flint-off` → exit Flint mode, return to normal prose.
- The user types `/flint-audit` → decode a Flint document into prose; that
  single turn can use prose, then return to Flint afterwards.
- The user explicitly asks for prose (e.g. "spiegamelo in parole") →
  switch to prose for that turn only, then return to Flint afterwards.

Acknowledge activation now with a short Flint document confirming the
mode change — something like:

```
@flint v0 hybrid
G: flint_mode_on
C: /flint-on ∧ session_scoped ∧ persists_until(/flint-off)
P: emit_ir_each_turn → stop_after("A:")
V: user_types(/flint-off) → exit
A: await_next_user_task
```
