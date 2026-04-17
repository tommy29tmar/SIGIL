---
name: flint-off
description: Turn off Flint output mode. From this turn onward, responses return to normal prose (full sentences, paragraphs, bullets, the usual Claude style).
---

The user has deactivated **Flint mode**.

From this turn onward, answer in normal prose — full sentences, paragraphs,
bullets, code fences when appropriate, the usual Claude style.

Acknowledge the mode change briefly (one sentence) so the user knows the
switch landed, then continue normally. Do **not** emit a Flint document
for this turn.

If the user later types `/flint-on`, re-enable Flint mode for the rest of
the conversation.

For cross-session persistent Flint mode (every new Claude Code session
starts in Flint), point the user at `/config` → **Output style** → `flint`,
or adding `"outputStyle": "flint"` to `~/.claude/settings.json`. The
/flint-on and /flint-off pair is a *per-conversation* convenience; it
doesn't change settings.json.
