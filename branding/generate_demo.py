#!/usr/bin/env python3
"""Render the XIR demo as an animated GIF.

    python branding/generate_demo.py

The point of the demo is one thing: a behavioural question answered by traversal
rather than by reading code. So the script drives a real sequence of `xir` commands
against the real example model, frames the terminal output as it appears, and writes
a typewriter-effect GIF.

No fake output. Every line on screen came out of the tool.
"""
from __future__ import annotations
import os
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "assets" / "demo.gif"
MODEL = "examples/project-manager/app.xir"

W, H = 940, 540
PAD = 28
FONT_PX = 15
LEADING = 22
TITLEBAR = 36
WINDOW = 19        # visible lines; older lines scroll off
VISIBLE = 19       # how many lines actually fit on the canvas

BG = (11, 15, 25)
BAR = (17, 24, 39)
FG = (229, 231, 235)
MUTED = (148, 163, 184)
CYAN = (34, 211, 238)
VIOLET = (167, 139, 250)
PINK = (244, 114, 182)
GREEN = (74, 222, 128)
AMBER = (251, 191, 36)
PROMPT = (244, 114, 182)

# The demo has one job: show a behavioural question answered by traversal.
# Every step is a real command; output is trimmed to what fits on screen.
STEPS = [
    ("$ xir validate " + MODEL, CYAN, 0.6, 2),
    ("$ xir trace " + MODEL + " archiveProject", CYAN, 1.5, 13),
    ("$ xir query " + MODEL + " \"who can archiveProject\"", CYAN, 0.9, 3),
    ("$ xir query " + MODEL + " \"affected field.project.status\"", CYAN, 0.9, 3),
    ("$ xir compile " + MODEL + " --target react", CYAN, 0.7, 3),
    ("$ xir patch " + MODEL + " \"patch { remove capability.archiveProject }\"", CYAN, 1.4, 2),
]

def font(kind: str, size: int = FONT_PX):
    import glob
    import matplotlib
    d = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
    name = "DejaVuSansMono.ttf" if kind == "mono" else "DejaVuSans.ttf"
    hit = glob.glob(os.path.join(d, name)) or glob.glob(os.path.join(d, "DejaVuSans.ttf"))
    return ImageFont.truetype(hit[0], size)


F_MONO = font("mono")
F_TITLE = font("sans", 14)


def run(cmd: str) -> list[str]:
    """Execute a real xir command and return its real output."""
    from click.testing import CliRunner
    import shlex
    from xir.cli.main import main as cli
    args = shlex.split(cmd[2:])            # strip the leading "$ "
    if args and args[0] == "xir":
        args = args[1:]                    # strip the program name
    r = CliRunner().invoke(cli, args)
    out = (r.output or "").rstrip("\n")
    if not out:
        out = f"(exit {r.exit_code})"
    return out.splitlines() or [""]


def line_colour(line: str, in_output: bool) -> tuple:
    if not in_output:
        return PROMPT
    s = line.strip()
    if not s:
        return FG
    if s.startswith(("CAPABILITY", "SURFACE", "COMPONENT", "FLOW", "STATE", "EVENT",
                     "FIELD", "ACTOR", "MACHINE", "INTERACTION", "GOAL", "PERMISSION")):
        return CYAN
    for key in ("REQUIRES", "MUTATES", "EMITS", "CONSUMES", "PRODUCES", "OUTPUT", "INPUT",
                "EXPOSED BY", "CONFIRMATION", "AUDIT", "MUTATED BY", "MUTATES:"):
        if s.startswith(key):
            return PINK
    for key in ("CONTAINS", "PRESENTS", "ID", "AFFECTED", "STATE:", "FLOW:", "valid:",
                "PROJECT", "surface", "capability", "flow", "interaction"):
        if s.startswith(key):
            return VIOLET
    if s.startswith(("PATCH", "REMOVED", "rolled back", "cannot remove", "  ")):
        return AMBER if "cannot remove" in s or "REJECT" in s else MUTED
    if s.startswith(("react:", "playwright:", "round-trip", "//", "export", "import")):
        return MUTED
    return FG


def draw(lines: list[tuple[str, tuple]], cursor: bool) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # title bar with traffic lights
    d.rectangle([0, 0, W, TITLEBAR], fill=BAR)
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([PAD + i * 22 - 6, TITLEBAR // 2 - 6, PAD + i * 22 + 6, TITLEBAR // 2 + 6], fill=c)
    d.text((W // 2, TITLEBAR // 2), "xir — semantic model of ProjectManager",
           font=F_TITLE, fill=MUTED, anchor="mm")

    d.line([(0, TITLEBAR), (W, TITLEBAR)], fill=(30, 41, 59))
    y = TITLEBAR + PAD
    for text, colour in lines:
        if y > H - 18:
            break
        d.text((PAD, y), text, font=F_MONO, fill=colour)
        y += LEADING
    if cursor and y <= H - 18:
        d.rectangle([PAD, y + 3, PAD + 11, y + LEADING - 6], fill=CYAN)
    return img


def main() -> int:
    if not (ROOT / MODEL).exists():
        print(f"missing {MODEL}", file=sys.stderr)
        return 1
    OUT.parent.mkdir(parents=True, exist_ok=True)

    frames: list[Image.Image] = []
    durations: list[int] = []

    def emit(lines, cursor, hold_ms):
        """Append a frame, with an explicit dwell time."""
        frames.append(draw(lines, cursor))
        durations.append(hold_ms)

    script = []
    for cmd, colour, pause, cap in STEPS:
        lines = run(cmd)
        if len(lines) > cap:
            # keep the informative head; a truncated real output is still real
            lines = lines[:cap]
        script.append((cmd, lines, colour, pause))

    def chunked(s, step):
        """Reveal text in `step`-sized pieces so we type fast but not per-character."""
        return [s[i:i + step] for i in range(0, len(s), step)]

    # opening card
    title = [("$ xir — semantic IR for interactive products", PROMPT),
             ("", FG),
             ("One model. Questions answered by traversal,", MUTED),
             ("not by reading code.", MUTED)]
    for _ in range(10):
        emit(title, False, 110)

    committed: list[tuple[str, tuple]] = []
    for cmd, output, colour, pause in script:
        # type the command onto one line
        active = ""
        for piece in chunked(cmd, 4):
            active += piece
            emit((committed + [(active, PROMPT)])[-WINDOW:], True, 45)
        emit((committed + [(active, PROMPT)])[-WINDOW:], False, 300)

        # reveal the output line by line
        for line in output:
            col = line_colour(line, True)
            grow = ""
            for piece in chunked(line, 14):
                grow += piece
                emit((committed + [(grow, col)])[-WINDOW:], True, 40)
            committed.append((line, col))
            emit(committed[-WINDOW:], False, 320)
        for _ in range(int(pause * 6)):
            emit(committed[-WINDOW:], False, 200)

    # closing card
    end = [("", FG),
           ("Component -> Interaction -> Capability -> Permission", CYAN),
           ("                        -> Mutation -> Event -> Transition", CYAN),
           ("", FG),
           ("pip install xir-core        github.com/ZakLr/XIR", MUTED)]
    for _ in range(24):
        emit(end, False, 110)

    # de-duplicate consecutive identical frames, summing their dwell time
    out_frames, out_durations = [], []
    for f, ms in zip(frames, durations):
        if out_frames and out_frames[-1].tobytes() == f.tobytes():
            out_durations[-1] += ms
        else:
            out_frames.append(f)
            out_durations.append(ms)

    out_frames[0].save(OUT, save_all=True, append_images=out_frames[1:],
                       duration=out_durations, loop=0, optimize=True,
                       disposal=2)
    # a 256-colour GIF of a 1000px terminal is still heavy; quantise hard
    _requantise(OUT)
    kb = OUT.stat().st_size / 1024
    secs = sum(out_durations) / 1000
    print(f"  {OUT.relative_to(ROOT)}  {len(out_frames)} frames, {kb:.0f} KB, "
          f"{W}x{H}, {secs:.0f}s")
    return 0


def _requantise(path: Path) -> None:
    """Drop to a small palette. The art uses ~16 colours; 64 is plenty."""
    from PIL import Image
    im = Image.open(path)
    frames = []
    for i in range(im.n_frames):
        im.seek(i)
        frames.append(im.convert("RGB").quantize(colors=32, method=Image.MEDIANCUT,
                                                  dither=Image.NONE))
    durations = []
    im.seek(0)
    for i in range(im.n_frames):
        durations.append(im.info.get("duration", 90))
    frames[0].save(path, save_all=True, append_images=frames[1:],
                   duration=durations, loop=0, optimize=True, disposal=2)


if __name__ == "__main__":
    raise SystemExit(main())
