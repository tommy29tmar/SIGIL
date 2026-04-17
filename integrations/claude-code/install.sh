#!/usr/bin/env bash
# Flint — Claude Code skill installer.
# One-line install:
#   curl -fsSL https://raw.githubusercontent.com/tommy29tmar/flint/main/integrations/claude-code/install.sh | bash
#
# What this does:
#   1. Installs four Claude Code skills: /flint, /flint-on, /flint-off, /flint-audit.
#   2. Installs the Flint output-style (for /config → Output style → flint).
#   3. Installs the flint-ir Python package (provides the `flint` CLI for local parse/rerender).
#
# Refuses to run if ~/.claude is not present (i.e. Claude Code not installed).

set -euo pipefail

CLAUDE_DIR="${HOME}/.claude"
REPO_URL="https://github.com/tommy29tmar/flint.git"
RAW_URL="https://raw.githubusercontent.com/tommy29tmar/flint/main"

SKILLS=(flint flint-on flint-off flint-audit)

if [ ! -d "$CLAUDE_DIR" ]; then
  echo "error: ~/.claude not found. Install Claude Code first."
  exit 1
fi

# Detect if running from a repo checkout (for local testing). Otherwise curl down.
# When piped via `curl | bash`, BASH_SOURCE is empty and SCRIPT_DIR stays empty.
SCRIPT_DIR=""
if [ -n "${BASH_SOURCE[0]:-}" ]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || echo "")"
fi
IS_LOCAL=0
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/skills/flint/SKILL.md" ]; then
  IS_LOCAL=1
fi

fetch() {
  local rel="$1"
  local dest="$2"
  if [ "$IS_LOCAL" = "1" ]; then
    cp "$SCRIPT_DIR/$rel" "$dest"
  else
    curl -fsSL "$RAW_URL/integrations/claude-code/$rel" -o "$dest"
  fi
}

for skill in "${SKILLS[@]}"; do
  echo "==> Installing /$skill skill"
  mkdir -p "$CLAUDE_DIR/skills/$skill"
  fetch "skills/$skill/SKILL.md" "$CLAUDE_DIR/skills/$skill/SKILL.md"
done

echo "==> Installing Flint output-style"
mkdir -p "$CLAUDE_DIR/output-styles"
fetch "output-styles/flint.md" "$CLAUDE_DIR/output-styles/flint.md" || \
  echo "   (output-style install failed — skills alone are sufficient)"

echo "==> Installing flint-ir Python package (optional)"
if command -v pipx >/dev/null 2>&1; then
  pipx install "git+${REPO_URL}" || pipx install --force "git+${REPO_URL}" || true
elif command -v pip >/dev/null 2>&1; then
  pip install --user "git+${REPO_URL}" || true
else
  echo "   (skipping — install pipx or pip to get the \`flint\` CLI)"
fi

echo ""
echo "✓ Flint installed."
echo ""
echo "Slash commands:"
echo "  /flint <question>          one-shot: answer this question in Flint"
echo "  /flint-on                   turn on Flint mode for this conversation"
echo "  /flint-off                  turn off Flint mode"
echo "  /flint-audit <file|text>   decode a Flint document into readable prose"
echo ""
echo "For cross-session persistence (every new Claude Code session in Flint):"
echo "  /config → Output style → flint"
echo "  or add \"outputStyle\": \"flint\" to ~/.claude/settings.json."
