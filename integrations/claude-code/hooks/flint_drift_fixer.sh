#!/usr/bin/env bash
# flint_drift_fixer — UserPromptSubmit hook
#
# Per-turn classifier that reasserts Flint rules as additionalContext.
# Fixes the multi-turn drift observed in cccflint and cccflint-mcp: IR
# fires at T1 but the model defaults to prose on T2-T4 as system-prompt
# attention wanes against accumulated conversation.
#
# By emitting a fresh per-turn directive adjacent to the user's message,
# attention weight is pinned to the Flint rules again for that turn.
#
# Input: JSON event object on stdin with a "prompt" field.
# Output: JSON hookSpecificOutput with additionalContext string.
#
# Classification is regex-based (no LLM call, no latency).

set -euo pipefail

input="$(cat)"
# Extract the prompt text (jq fallback for systems without jq)
if command -v jq >/dev/null 2>&1; then
    prompt="$(printf '%s' "$input" | jq -r '.prompt // ""')"
else
    prompt="$(printf '%s' "$input" | sed -n 's/.*"prompt":[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)"
fi

# Default: IR-shape off
ir_shape=0

# IR indicators: code structure cues OR task-shape verbs
# Code structure cues
has_code=0
if printf '%s' "$prompt" | grep -qE '```|\bdef \b|\bclass \b|diff --git|^[+-] '; then
    has_code=1
fi
# Task-shape IR verbs
if printf '%s' "$prompt" | grep -iqE 'debug|review.*(code|diff|patch|pr|commit)|fix.*(bug|code|race|issue)|refactor|check.*(code|security)|audit.*(code|security)|spieg.*perch|concurrency.*issue|security.*issue|vulnerability|bypass.*(auth|security)|race.*condition|test.*fail'; then
    ir_shape=1
fi
# Code + any review verb
if [ "$has_code" = "1" ] && printf '%s' "$prompt" | grep -iqE 'review|audit|check|find|describe.*(issue|bug|problem)|what.*(wrong|bug|issue)'; then
    ir_shape=1
fi

# Standalone IR triggers (no code block needed)
if printf '%s' "$prompt" | grep -iqE 'what.*(issues|bugs|risks|errors)|verify|regression test|repro test|what.*monitor|cosa.*monit|monitor.*prod|canary|alert|trace.*(bug|error)|repro|propose.*fix|describe.*fix|describe.*test'; then
    ir_shape=1
fi

# Prose overrides — user explicitly wants narrative/essay
if printf '%s' "$prompt" | grep -iqE 'explain.*junior|explain how.*works|tutorial|rfc|essay|brainstorm|post.mortem|memo|narrative|readable|stakeholders|non.technical|senior.*dev'; then
    ir_shape=0
fi

# Task-shape negations — user disavows crisp endpoint
if printf '%s' "$prompt" | grep -iqE 'non cerco|non voglio.*fix|non.*decisione|filosof|discussione|ragioni sul tradeoff'; then
    ir_shape=0
fi

if [ "$ir_shape" = "1" ]; then
    directive="[TURN CLASSIFICATION: IR-shape] This turn has a crisp technical goal and verifiable endpoint. Respond in Flint IR: emit '@flint v0 hybrid' + G/C/P/V/A clauses (or call the submit_flint_ir MCP tool if available). Do NOT respond in prose for this turn. Keep atoms in lowercase_snake_case or call form f(\"x\") or quoted literals."
else
    directive="[TURN CLASSIFICATION: prose-shape] This turn asks for writing, explanation, brainstorming, summary, or conversation. Respond in Caveman-compressed prose. No markdown headers (# or ##). No bold. Drop articles (the/a/an/is/are). No filler intros or summaries. One idea per line. Do NOT emit Flint IR or call submit_flint_ir for this turn."
fi

# Emit hook output JSON (escape quotes and newlines in directive)
escaped="$(printf '%s' "$directive" | sed 's/\\/\\\\/g; s/"/\\"/g')"
printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"%s"}}\n' "$escaped"
