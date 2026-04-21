#!/usr/bin/env bash
# Hewn — Claude Code installer (with legacy Flint aliases retained).
# One-line install:
#   curl -fsSL https://raw.githubusercontent.com/tommy29tmar/flint/main/integrations/claude-code/install.sh | bash
#
# What this does:
#   1. Installs four Claude Code skills: /flint, /flint-on, /flint-off, /flint-audit.
#   2. Installs both Hewn and Flint output-style names (`hewn`, `hewn-thinking`,
#      `flint`, `flint-thinking`).
#   3. Installs the `hewn` CLI wrapper (recommended default) plus the legacy
#      `flint` alias. Both invoke `claude` with Hewn/Flint thinking-mode at
#      system-prompt level + per-turn drift-fix hook. Does NOT interfere with the
#      default `claude` binary.
#   4. Optionally installs `hewn-mcp` plus the legacy `flint-mcp`: same as `hewn`
#      plus an MCP server exposing
#      `submit_flint_ir` for schema-validated IR (downstream pipeline use-case).
#   5. Installs the Python package (provides both `hewn-ir` and `flint-ir` CLI aliases
#      for parse/rerender).
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

echo "==> Installing Hewn / Flint output-styles"
mkdir -p "$CLAUDE_DIR/output-styles"
fetch "output-styles/hewn.md" "$CLAUDE_DIR/output-styles/hewn.md" || \
  echo "   (hewn output-style install failed — legacy flint styles remain available)"
fetch "output-styles/hewn-thinking.md" "$CLAUDE_DIR/output-styles/hewn-thinking.md" || \
  echo "   (hewn-thinking output-style install failed — not fatal)"
fetch "output-styles/flint.md" "$CLAUDE_DIR/output-styles/flint.md" || \
  echo "   (flint output-style install failed — skills alone are sufficient)"
fetch "output-styles/flint-thinking.md" "$CLAUDE_DIR/output-styles/flint-thinking.md" || \
  echo "   (flint-thinking output-style install failed — not fatal)"

echo "==> Installing Hewn / Flint CLI wrappers + thinking-mode prompts + drift-fix hook"
BIN_DIR="${HOME}/.local/bin"
mkdir -p "$BIN_DIR"
mkdir -p "$CLAUDE_DIR/hooks"
fetch "bin/hewn" "$BIN_DIR/hewn" || echo "   (hewn install failed — not fatal)"
chmod +x "$BIN_DIR/hewn" 2>/dev/null || true
fetch "bin/flint" "$BIN_DIR/flint" || echo "   (flint install failed — not fatal)"
chmod +x "$BIN_DIR/flint" 2>/dev/null || true
fetch "bin/hewn-mcp" "$BIN_DIR/hewn-mcp" || echo "   (hewn-mcp install failed — not fatal)"
chmod +x "$BIN_DIR/hewn-mcp" 2>/dev/null || true
fetch "bin/flint-mcp" "$BIN_DIR/flint-mcp" || echo "   (flint-mcp install failed — not fatal)"
chmod +x "$BIN_DIR/flint-mcp" 2>/dev/null || true
fetch "flint_thinking_system_prompt.txt" "$CLAUDE_DIR/flint_thinking_system_prompt.txt" || \
  echo "   (thinking-mode prompt install failed — flint will not work until installed)"
fetch "flint_thinking_mcp_system_prompt.txt" "$CLAUDE_DIR/flint_thinking_mcp_system_prompt.txt" || \
  echo "   (thinking-mode-MCP prompt install failed — flint-mcp will not work until installed)"
fetch "mcp-config.json" "$CLAUDE_DIR/flint-mcp-config.json" || \
  echo "   (mcp-config install failed — flint-mcp requires it)"
fetch "hooks/flint_drift_fixer.py" "$CLAUDE_DIR/hooks/flint_drift_fixer.py" || \
  echo "   (drift-fix hook install failed — flint will fall back to system-prompt-only mode)"
chmod +x "$CLAUDE_DIR/hooks/flint_drift_fixer.py" 2>/dev/null || true
fetch "flint-drift-fix-settings.json" "$CLAUDE_DIR/flint-drift-fix-settings.json" || \
  echo "   (drift-fix settings install failed — flint will not register the hook)"

if ! echo ":$PATH:" | grep -q ":$BIN_DIR:"; then
  echo ""
  echo "   ⚠  $BIN_DIR is not in your \$PATH."
  echo "      Add this line to your ~/.bashrc or ~/.zshrc:"
  echo "        export PATH=\"\$HOME/.local/bin:\$PATH\""
  echo ""
fi

echo "==> Installing Hewn / Flint Python CLI package (optional)"
if command -v pipx >/dev/null 2>&1; then
  pipx install "git+${REPO_URL}" || pipx install --force "git+${REPO_URL}" || true
elif command -v pip >/dev/null 2>&1; then
  pip install --user "git+${REPO_URL}" || true
else
  echo "   (skipping — install pipx or pip to get the \`hewn-ir\` / \`flint-ir\` CLI)"
fi

echo ""
echo "✓ Hewn installed."
echo ""
echo "Slash commands (legacy names retained for now):"
echo "  /flint <question>          one-shot: answer in strict Flint IR"
echo "  /flint-on                   turn on strict Flint for this conversation"
echo "  /flint-off                  turn off Flint mode"
echo "  /flint-audit <file|text>   decode a Flint document into readable prose"
echo ""
echo "Output-styles (opt-in, per session, set via /config):"
echo "  hewn            strict IR always"
echo "  hewn-thinking   dual-mode: Caveman prose + IR by task shape"
echo "  flint           strict IR always (best for API, parser-strict tooling)"
echo "  flint-thinking  dual-mode: Caveman prose + IR by task shape (Claude Code soft layer)"
echo ""
echo "Always-on for Claude Code Max users (recommended):"
echo "  hewn                        starts Claude Code with Hewn thinking-mode (Caveman prose +"
echo "                              IR on IR-shape tasks) + per-turn drift-fix hook. Does NOT"
echo "                              affect the default 'claude' command."
echo "  hewn -p \"your prompt\"      non-interactive mode"
echo "  flint                       legacy alias for hewn"
echo ""
echo "Optional — schema-validated IR via MCP (opt-in, downstream-pipeline use-case):"
echo "  hewn-mcp                    hewn + Flint MCP server (submit_flint_ir tool)"
echo "  hewn-mcp -p \"prompt\"       non-interactive mode"
echo "  flint-mcp                   legacy alias for hewn-mcp"
echo ""
echo "Requires Python 'mcp' package:  pip install --user mcp"
echo ""
echo "CLI parser / audit aliases:"
echo "  hewn-ir                     primary parser / audit command"
echo "  flint-ir                    legacy alias"
echo ""
echo "The default 'claude' command remains untouched — hewn / hewn-mcp and their"
echo "legacy flint aliases are separate binaries. Opt into the level of enforcement"
echo "you need."
