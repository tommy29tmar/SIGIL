#!/usr/bin/env python3
"""Render assets/launch/demo.png — a clean, viral-friendly before/after.

Left: verbose Claude default (truncated with "...").
Right: Flint 6-line reply.
Bottom: headline numbers.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "launch" / "demo.png"

BG            = (14, 16, 22)
PANEL_BG      = (24, 28, 38)
SIGIL_BG      = (20, 30, 30)
BORDER        = (60, 66, 80)
SIGIL_BORDER  = (80, 200, 160)
TEXT_DIM      = (170, 176, 190)
TEXT_BRIGHT   = (230, 234, 245)
ACCENT        = (120, 220, 180)
ACCENT_WARN   = (240, 200, 110)
HEADLINE      = (255, 255, 255)

W, H = 1600, 900
PAD = 60
GAP = 40
PANEL_Y = 180
PANEL_H = 520
PANEL_W = (W - 2 * PAD - GAP) // 2

VERBOSE_BODY = """finding: X-Forwarded-For trusted without
proxy validation ⇒ spoofable rate-limit key

exploit:
- attacker sends rotating XFF header →
  distinct keys → limiter bypassed
- attacker pins victim IP → exhausts
  victim's bucket → DoS / lockout

mitigation:
- derive client IP from trusted proxy
  chain only (Express trust proxy + req.ip)
- never read raw x-forwarded-for at
  public boundary
- also add INCR + EXPIRE atomically
  (current code leaks keys, no TTL)

verify:
- spoof test: rotating XFF, same socket
  → single bucket increments
  (...continues for 300+ more tokens)"""

SIGIL_BODY = """@flint v0 hybrid
G: fix(rl_spoof)
C: trust_boundary ∧ "X-Forwarded-For" ∧ "Redis"
P: drop("X-Forwarded-For") ∧ bind(req.ip) ∧ expire(key)
V: test(spoof_header) ∧ test(incr_ttl)
A: ! header_spoof ∧ ! key_unbounded ∧ ? proxy_chain"""


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates_bold = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    candidates_regular = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in (candidates_bold if bold else candidates_regular):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def draw_panel(draw, x, y, w, h, bg, border, radius=18):
    draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=bg, outline=border, width=2)


def main() -> None:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Header
    draw.text((PAD, 50),
        "Flint vs default Claude — same question, Opus 4.7",
        fill=HEADLINE, font=_font(40, bold=True))
    draw.text((PAD, 110),
        "Review this rate-limiter diff for a bypass vulnerability (~10k-tok project context loaded).",
        fill=TEXT_DIM, font=_font(22))

    # Left panel — verbose default
    lx, ly = PAD, PANEL_Y
    draw_panel(draw, lx, ly, PANEL_W, PANEL_H, PANEL_BG, BORDER)
    draw.text((lx + 28, ly + 24), "Claude (default)", fill=TEXT_BRIGHT, font=_font(28, bold=True))
    draw.text((lx + 28, ly + 64), "736 output · 15.2s · 74% coverage",
              fill=ACCENT_WARN, font=_font(22, bold=True))
    body_font = _font(18)
    ty = ly + 115
    for line in VERBOSE_BODY.split("\n"):
        if ty > ly + PANEL_H - 40:
            break
        draw.text((lx + 28, ty), line, fill=TEXT_DIM, font=body_font)
        ty += 26

    # Right panel — Flint
    rx, ry = PAD + PANEL_W + GAP, PANEL_Y
    draw_panel(draw, rx, ry, PANEL_W, PANEL_H, SIGIL_BG, SIGIL_BORDER)
    draw.text((rx + 28, ry + 24), "Claude + Flint",
              fill=ACCENT, font=_font(28, bold=True))
    draw.text((rx + 28, ry + 64), "186 output · 5.3s · 76% coverage",
              fill=ACCENT, font=_font(22, bold=True))
    sigil_font = _font(20)
    ty = ry + 125
    for line in SIGIL_BODY.split("\n"):
        draw.text((rx + 28, ty), line, fill=TEXT_BRIGHT, font=sigil_font)
        ty += 32

    # Bottom headline
    banner_y = PANEL_Y + PANEL_H + 40
    draw.text((PAD, banner_y),
        "-75% output   ·   -65% latency   ·   matching-or-better coverage",
        fill=HEADLINE, font=_font(38, bold=True))
    draw.text((PAD, banner_y + 60),
        "40 samples (10 long-context tasks × 4 runs), Opus 4.7 + prompt cache. One /flint install in Claude Code.",
        fill=TEXT_DIM, font=_font(20))

    img.save(OUT, "PNG", optimize=True)
    print(f"wrote {OUT} — {OUT.stat().st_size // 1024} KB, {Image.open(OUT).size}")


if __name__ == "__main__":
    main()
