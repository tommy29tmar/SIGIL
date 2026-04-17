#!/usr/bin/env bash
# Head-to-head SIGIL vs Caveman (primitive-english) vs verbose Claude baseline.
# Same frame Caveman uses to report "~60% savings".
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MODEL="claude-opus-4-7"
TASKS="evals/tasks_top_tier_holdout.jsonl"
OUT_DIR="evals/runs/caveman"
mkdir -p "$OUT_DIR"

run_cell() {
  local name="$1" transport="$2" ppath="$3"
  local out="$OUT_DIR/opus47_${name}.jsonl"
  rm -f "$out"
  echo "[$name] start" >&2
  python3 evals/run_anthropic.py \
    --tasks "$TASKS" \
    --model "$MODEL" \
    --out "$out" \
    --variant "${name}@${transport}=${ppath}" \
    --max-output-tokens 1024 \
    --max-retries 3 \
    > "$OUT_DIR/opus47_${name}.log" 2>&1
  echo "[$name] done" >&2
}

run_cell "verbose"    "plain"  "prompts/verbose_baseline.txt" &
run_cell "primitive"  "plain"  "prompts/primitive_english.txt" &
run_cell "sigil"      "sigil"  "integrations/claude-code/sigil_system_prompt.txt" &
wait
echo "all cells done"
