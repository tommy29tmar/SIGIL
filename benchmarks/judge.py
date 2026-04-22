#!/usr/bin/env python3
"""Hewn benchmark judge — concepts coverage + readability scoring.

Reads snapshots/raw/<track>/<arm>/<prompt>_r<N>.json (and per-turn for T4),
invokes claude -p --model claude-opus-4-7 --output-format json with a
strict-JSON-output system prompt, validates the response against
rubrics/concepts.json, retries on invalid JSON (max 2), persists raw
judge output to snapshots/raw_judgments/, tracks judge_failure_rate.

Blinded: judge sees the response text only, not the arm name.
Deterministic: binary present/absent per concept; no free-form score.

Usage:
  uv run benchmarks/judge.py --track T1a
  uv run benchmarks/judge.py --track all
  uv run benchmarks/judge.py --resume   # skip already-judged
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BENCH = Path(__file__).resolve().parent
RUBRICS = BENCH / "rubrics" / "concepts.json"
LITERALS = BENCH / "rubrics" / "literals.json"
RAW = BENCH / "snapshots" / "raw"
RAW_J = BENCH / "snapshots" / "raw_judgments"
MODEL = "claude-opus-4-7"

# Tracks to judge — multi-turn (T4) judged per turn separately
SINGLE_TURN_TRACKS = ["T1a", "T1b", "T2", "T3", "T5"]
MULTITURN_TRACKS = ["T4"]


# ──────────────────────────────────────────────────────────────────────────────
# judge prompt construction
# ──────────────────────────────────────────────────────────────────────────────

CONCEPT_JUDGE_SYSTEM = """You are a strict, blinded grader. You receive:
1. The original user prompt that was asked.
2. A response under review (the source of the response is hidden — do NOT speculate).
3. A list of concepts the response should cover.

For each concept, return a single boolean: true if the concept is meaningfully
present in the response (the substance is conveyed, not just a keyword match),
false otherwise. Be strict: shallow keyword mention without explanation = false.
Substantive coverage even with different wording = true.

Output ONLY a single JSON object with each concept name as a key and a boolean
as the value. No prose, no explanation, no markdown fences. Just the JSON."""


READABILITY_JUDGE_SYSTEM = """You are evaluating whether a response is
understandable to a NON-TECHNICAL user (someone who doesn't know what a
'cache', 'pool', or 'middleware' is). The user's original request was casual
and non-technical.

Return ONLY a single JSON object with these exact keys, all booleans:
{
  "uses_plain_language": true/false (avoids unexplained jargon),
  "actionable": true/false (gives the user something concrete to try or check),
  "starts_helpfully": true/false (doesn't open with a wall of code or a lecture),
  "respects_user_level": true/false (treats them as a non-expert without condescension)
}
No prose. No markdown. Just the JSON."""


def build_concept_judge_user(prompt: str, response: str,
                             concepts: list[str]) -> str:
    return (
        "ORIGINAL USER PROMPT:\n"
        f"{prompt}\n\n"
        "RESPONSE UNDER REVIEW:\n"
        f"{response}\n\n"
        "CONCEPTS TO CHECK (output a JSON object with these exact keys, "
        "boolean values only):\n"
        + json.dumps(concepts, indent=2)
    )


def build_readability_judge_user(prompt: str, response: str) -> str:
    return (
        "ORIGINAL USER PROMPT (the user is non-technical):\n"
        f"{prompt}\n\n"
        "RESPONSE UNDER REVIEW:\n"
        f"{response}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# subprocess + validation
# ──────────────────────────────────────────────────────────────────────────────

def call_judge(system: str, user: str) -> str:
    cmd = ["claude", "-p", "--model", MODEL, "--output-format", "json",
           "--system-prompt", system, user]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    payload = json.loads(proc.stdout)
    return payload.get("result", "") or ""


def extract_json(text: str) -> dict | None:
    """Extract a JSON object from possibly noisy text (judge sometimes wraps)."""
    text = text.strip()
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try fenced block
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    # Try first {...} balanced block
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i, ch in enumerate(text[start:], start=start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i+1])
                except json.JSONDecodeError:
                    return None
    return None


def validate_concept_judgment(obj: Any, expected_keys: list[str]) -> bool:
    if not isinstance(obj, dict):
        return False
    for k in expected_keys:
        if k not in obj or not isinstance(obj[k], bool):
            return False
    return True


def validate_readability_judgment(obj: Any) -> bool:
    if not isinstance(obj, dict):
        return False
    for k in ("uses_plain_language", "actionable", "starts_helpfully",
              "respects_user_level"):
        if k not in obj or not isinstance(obj[k], bool):
            return False
    return True


def judge_with_retry(system: str, user: str, validator,
                     raw_path: Path, max_retries: int = 2) -> dict | None:
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    history = []
    for attempt in range(max_retries + 1):
        try:
            text = call_judge(system, user)
        except Exception as e:
            history.append({"attempt": attempt, "error": str(e)})
            continue
        history.append({"attempt": attempt, "raw": text})
        obj = extract_json(text)
        if obj is not None and validator(obj):
            raw_path.write_text(json.dumps({"final": obj, "history": history,
                                            "ts": _now()},
                                           indent=2, ensure_ascii=False))
            return obj
    raw_path.write_text(json.dumps({"final": None, "history": history,
                                    "ts": _now(), "status": "FAILED"},
                                   indent=2, ensure_ascii=False))
    return None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ──────────────────────────────────────────────────────────────────────────────
# literal preservation (deterministic, no judge)
# ──────────────────────────────────────────────────────────────────────────────

def check_literals(response: str, literals: list[str]) -> dict[str, bool]:
    return {lit: lit in response for lit in literals}


# ──────────────────────────────────────────────────────────────────────────────
# format compliance
# ──────────────────────────────────────────────────────────────────────────────

HEWN_IR_HEADER = "@hewn v0 hybrid"
HEWN_IR_LINES_RE = re.compile(
    r"^@hewn v0 hybrid\s*\nG:.*\nC:.*\nP:.*\nV:.*\nA:.*$",
    re.MULTILINE,
)

CAVEMAN_FILLER_RE = re.compile(
    r"\b(sure|certainly|of course|happy to|just|really|basically|"
    r"actually|simply)\b",
    re.IGNORECASE,
)
LEADING_ARTICLE_RE = re.compile(r"^\s*(the|a|an)\s+", re.IGNORECASE | re.MULTILINE)


def hewn_ir_valid(response: str) -> bool:
    text = response.strip()
    if not text.startswith(HEWN_IR_HEADER):
        return False
    return bool(HEWN_IR_LINES_RE.search(text))


def caveman_style_score(response: str) -> dict[str, Any]:
    """Heuristic: low filler frequency + few sentence-leading articles."""
    fillers = len(CAVEMAN_FILLER_RE.findall(response))
    leading_articles = len(LEADING_ARTICLE_RE.findall(response))
    words = max(1, len(response.split()))
    return {
        "filler_count": fillers,
        "leading_article_count": leading_articles,
        "words": words,
        "filler_per_100w": round(fillers * 100 / words, 2),
        "leading_article_per_100w": round(leading_articles * 100 / words, 2),
    }


# ──────────────────────────────────────────────────────────────────────────────
# main per-track loop
# ──────────────────────────────────────────────────────────────────────────────

def judge_single_turn_track(track: str, concepts_db: dict,
                            literals_db: dict) -> None:
    track_dir = RAW / track
    if not track_dir.exists():
        print(f"[{track}] no snapshots; skipping")
        return
    out_path = BENCH / "snapshots" / f"judgments_{track}.json"
    if out_path.exists():
        existing = json.loads(out_path.read_text())
    else:
        existing = {}
    judged_count = 0
    failed_count = 0
    total = 0

    # determine which prompt-set rubric applies
    prompt_set = {
        "T1a": "short_en", "T1b": "short_en", "T2": "vibe_en",
        "T3": "long_en", "T5": "expansive_en",
    }[track]
    concepts_for_set = concepts_db.get(prompt_set, {})
    literals_for_set = literals_db.get(prompt_set, {})

    do_readability = (track == "T2")

    for arm_dir in sorted(track_dir.iterdir()):
        if not arm_dir.is_dir():
            continue
        arm = arm_dir.name
        for snap_path in sorted(arm_dir.glob("*.json")):
            stem = snap_path.stem  # e.g. "react-rerender-parent_r1"
            m = re.match(r"^(.+)_r(\d+)$", stem)
            if not m:
                continue
            prompt_id, run_idx = m.group(1), int(m.group(2))
            key = f"{arm}/{prompt_id}_r{run_idx}"
            total += 1
            if key in existing:
                continue

            snap = json.loads(snap_path.read_text())
            response = snap.get("result", "") or ""
            if not response:
                existing[key] = {"skipped": "empty_response"}
                continue

            # Reconstruct original user prompt for the judge
            original_prompt = _lookup_original_prompt(prompt_set, prompt_id)

            concepts = concepts_for_set.get(prompt_id, [])
            literals = literals_for_set.get(prompt_id, [])

            entry: dict[str, Any] = {
                "arm": arm, "prompt_id": prompt_id, "run_index": run_idx,
                "literals_present": check_literals(response, literals)
                if literals else {},
                "format": {
                    "hewn_ir_valid": hewn_ir_valid(response),
                    "caveman_style": caveman_style_score(response),
                },
            }

            if concepts:
                raw_path = RAW_J / track / arm / f"{prompt_id}_r{run_idx}_concepts.json"
                user_msg = build_concept_judge_user(
                    original_prompt, response, concepts)
                obj = judge_with_retry(
                    CONCEPT_JUDGE_SYSTEM, user_msg,
                    lambda o: validate_concept_judgment(o, concepts),
                    raw_path)
                if obj is None:
                    entry["concepts"] = None
                    entry["concepts_failure"] = True
                    failed_count += 1
                else:
                    entry["concepts"] = obj
                    entry["concepts_count_present"] = sum(1 for v in obj.values() if v)
                    entry["concepts_count_total"] = len(obj)
                judged_count += 1

            if do_readability:
                raw_path = RAW_J / track / arm / f"{prompt_id}_r{run_idx}_readability.json"
                user_msg = build_readability_judge_user(original_prompt, response)
                obj = judge_with_retry(
                    READABILITY_JUDGE_SYSTEM, user_msg,
                    validate_readability_judgment, raw_path)
                if obj is None:
                    entry["readability"] = None
                    entry["readability_failure"] = True
                else:
                    entry["readability"] = obj
                    entry["readability_count_true"] = sum(
                        1 for v in obj.values() if v)
                judged_count += 1

            existing[key] = entry
            print(f"  [{track}] {key}", flush=True)

            # Persist incrementally so a crash doesn't lose work
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(existing, indent=2,
                                           ensure_ascii=False))

    print(f"[{track}] judged {judged_count} entries, "
          f"{failed_count} failures, {total} total snapshots")


def judge_multiturn_track(concepts_db: dict) -> None:
    track = "T4"
    track_dir = RAW / track
    if not track_dir.exists():
        print(f"[{track}] no snapshots; skipping")
        return
    out_path = BENCH / "snapshots" / f"judgments_{track}.json"
    if out_path.exists():
        existing = json.loads(out_path.read_text())
    else:
        existing = {}

    seq_data = json.loads(
        (BENCH / "prompts" / "multiturn_en.json").read_text())["sequences"]
    seq_map = {s["id"]: s for s in seq_data}
    rubric_per_turn = concepts_db.get("multiturn_en", {})

    for arm_dir in sorted(track_dir.iterdir()):
        if not arm_dir.is_dir():
            continue
        arm = arm_dir.name
        for snap_path in sorted(arm_dir.glob("*_t*.json")):
            stem = snap_path.stem  # "debug-prod-incident_r1_t3"
            m = re.match(r"^(.+)_r(\d+)_t(\d+)$", stem)
            if not m:
                continue
            seq_id, run_idx, turn = m.group(1), int(m.group(2)), int(m.group(3))
            key = f"{arm}/{seq_id}_r{run_idx}_t{turn}"
            if key in existing:
                continue
            snap = json.loads(snap_path.read_text())
            response = snap.get("result", "") or ""
            if not response:
                existing[key] = {"skipped": "empty_response"}
                continue
            user_msg_for_judge = seq_map[seq_id]["turns"][turn-1]
            concepts = rubric_per_turn.get(seq_id, {}).get(f"turn_{turn}", [])
            entry: dict[str, Any] = {
                "arm": arm, "sequence_id": seq_id, "run_index": run_idx,
                "turn": turn,
                "format": {
                    "hewn_ir_valid": hewn_ir_valid(response),
                    "caveman_style": caveman_style_score(response),
                },
            }
            if concepts:
                raw_path = RAW_J / track / arm / f"{seq_id}_r{run_idx}_t{turn}_concepts.json"
                user_msg = build_concept_judge_user(
                    user_msg_for_judge, response, concepts)
                obj = judge_with_retry(
                    CONCEPT_JUDGE_SYSTEM, user_msg,
                    lambda o: validate_concept_judgment(o, concepts),
                    raw_path)
                if obj is None:
                    entry["concepts"] = None
                    entry["concepts_failure"] = True
                else:
                    entry["concepts"] = obj
                    entry["concepts_count_present"] = sum(
                        1 for v in obj.values() if v)
                    entry["concepts_count_total"] = len(obj)
            existing[key] = entry
            print(f"  [T4] {key}", flush=True)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(existing, indent=2,
                                           ensure_ascii=False))


TRANSCRIPT_JUDGE_SYSTEM = """You are a strict, blinded grader of a multi-turn conversation.

You see the FULL conversation between a user and an assistant across N
turns. Evaluate whether the assistant's RESPONSES TAKEN TOGETHER
cover each required concept. Rules:

- A concept counts as covered if the assistant established it at any
  point in the conversation, even if a later turn builds on it without
  re-stating.
- A concept counts as NOT covered only if the assistant never introduced
  or acknowledged the idea anywhere across all turns.
- Do not penalize the assistant for NOT repeating a concept that was
  already established earlier. Conversation continuity is expected.
- Be strict: shallow keyword match without substance = not covered.
  Substantive coverage even with different wording = covered.

Output ONLY a single JSON object mapping each concept name to a
boolean. No prose, no markdown fences. Just the JSON.
"""


def build_transcript_judge_user(seq_id: str, user_turns: list[str],
                                assistant_turns: list[str],
                                concepts: list[str]) -> str:
    transcript_lines = [f"CONVERSATION (sequence: {seq_id}, {len(user_turns)} turns)", ""]
    for i, (u, a) in enumerate(zip(user_turns, assistant_turns), start=1):
        transcript_lines.append(f"--- USER TURN {i} ---")
        transcript_lines.append(u.strip())
        transcript_lines.append("")
        transcript_lines.append(f"--- ASSISTANT TURN {i} ---")
        transcript_lines.append(a.strip())
        transcript_lines.append("")
    transcript = "\n".join(transcript_lines)
    return (
        transcript
        + "\n\nCONCEPTS TO CHECK (return a JSON object with these exact keys, "
        + "boolean values only; a concept counts as covered if the assistant "
        + "established it at any point, even if later turns built on it "
        + "without restating):\n"
        + json.dumps(concepts, indent=2)
    )


def judge_multiturn_transcript(concepts_db: dict) -> None:
    """Conversation-level T4 judge: evaluates the full transcript, not per turn.

    Writes to `snapshots/judgments_T4_transcript.json` (separate from the
    per-turn `judgments_T4.json` so both views are preserved).
    """
    track = "T4"
    track_dir = RAW / track
    if not track_dir.exists():
        print(f"[{track}-transcript] no snapshots; skipping")
        return
    out_path = BENCH / "snapshots" / f"judgments_{track}_transcript.json"
    existing = json.loads(out_path.read_text()) if out_path.exists() else {}

    seq_data = json.loads(
        (BENCH / "prompts" / "multiturn_en.json").read_text())["sequences"]
    seq_map = {s["id"]: s for s in seq_data}
    rubric_per_turn = concepts_db.get("multiturn_en", {})

    # Discover (arm, seq_id, run_idx) tuples from the snapshot filesystem.
    tuples: set[tuple[str, str, int]] = set()
    for arm_dir in sorted(track_dir.iterdir()):
        if not arm_dir.is_dir():
            continue
        arm = arm_dir.name
        for p in arm_dir.glob("*_t*.json"):
            m = re.match(r"^(.+)_r(\d+)_t(\d+)$", p.stem)
            if m:
                tuples.add((arm, m.group(1), int(m.group(2))))

    for (arm, seq_id, run_idx) in sorted(tuples):
        key = f"{arm}/{seq_id}_r{run_idx}"
        if key in existing:
            continue
        seq = seq_map.get(seq_id)
        if seq is None:
            continue
        user_turns = seq["turns"]
        n = len(user_turns)
        # Gather assistant responses in turn order.
        assistant_turns: list[str] = []
        for t in range(1, n + 1):
            p = track_dir / arm / f"{seq_id}_r{run_idx}_t{t}.json"
            if not p.exists():
                assistant_turns.append("")
                continue
            d = json.loads(p.read_text())
            assistant_turns.append(d.get("result", "") or "")
        if not any(assistant_turns):
            existing[key] = {"skipped": "empty_responses"}
            continue
        # Flatten concepts across all turns for this sequence.
        per_turn = rubric_per_turn.get(seq_id, {})
        all_concepts: list[str] = []
        per_turn_map: dict[str, int] = {}
        for t in range(1, n + 1):
            for c in per_turn.get(f"turn_{t}", []):
                if c not in per_turn_map:
                    per_turn_map[c] = t
                    all_concepts.append(c)
        if not all_concepts:
            continue
        raw_path = RAW_J / track / arm / f"{seq_id}_r{run_idx}_transcript.json"
        user_msg = build_transcript_judge_user(
            seq_id, user_turns, assistant_turns, all_concepts)
        obj = judge_with_retry(
            TRANSCRIPT_JUDGE_SYSTEM, user_msg,
            lambda o: validate_concept_judgment(o, all_concepts),
            raw_path)
        entry: dict[str, Any] = {
            "arm": arm, "sequence_id": seq_id, "run_index": run_idx,
            "n_turns": n,
            "concepts_flat": all_concepts,
        }
        if obj is None:
            entry["concepts"] = None
            entry["concepts_failure"] = True
        else:
            entry["concepts"] = obj
            entry["concepts_count_present"] = sum(1 for v in obj.values() if v)
            entry["concepts_count_total"] = len(obj)
        existing[key] = entry
        print(f"  [T4-transcript] {key}", flush=True)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False))


def _lookup_original_prompt(prompt_set: str, prompt_id: str) -> str:
    """Pull the user-visible prompt text for the given id (so judge sees it)."""
    if prompt_set == "short_en":
        from run import load_short_en
        return dict(load_short_en())[prompt_id]
    if prompt_set == "vibe_en":
        from run import load_vibe_en
        return dict(load_vibe_en())[prompt_id]
    if prompt_set == "long_en":
        from run import load_long_en
        return dict(load_long_en())[prompt_id]
    if prompt_set == "expansive_en":
        from run import load_expansive_en
        return dict(load_expansive_en())[prompt_id]
    return ""


# ──────────────────────────────────────────────────────────────────────────────
# main
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--track", default="all")
    parser.add_argument("--mode", choices=["per_turn", "transcript", "both"],
                        default="per_turn",
                        help="For T4 only: 'per_turn' (default, existing "
                        "judge), 'transcript' (conversation-level judge), "
                        "or 'both'.")
    args = parser.parse_args()

    sys.path.insert(0, str(BENCH))  # so we can `from run import ...`

    concepts_db = json.loads(RUBRICS.read_text())
    literals_db = json.loads(LITERALS.read_text())

    if args.track == "all":
        for t in SINGLE_TURN_TRACKS:
            judge_single_turn_track(t, concepts_db, literals_db)
        if args.mode in ("per_turn", "both"):
            judge_multiturn_track(concepts_db)
        if args.mode in ("transcript", "both"):
            judge_multiturn_transcript(concepts_db)
    elif args.track in SINGLE_TURN_TRACKS:
        judge_single_turn_track(args.track, concepts_db, literals_db)
    elif args.track == "T4":
        if args.mode in ("per_turn", "both"):
            judge_multiturn_track(concepts_db)
        if args.mode in ("transcript", "both"):
            judge_multiturn_transcript(concepts_db)
    else:
        print(f"unknown track: {args.track}")
        sys.exit(1)


if __name__ == "__main__":
    main()
