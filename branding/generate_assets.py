#!/usr/bin/env python3
"""Generate every XIR brand asset deterministically.

    python branding/generate_assets.py

Outputs
-------
docs/logo.svg              the mark
docs/wordmark.svg          the mark plus the word, for the README header
docs/favicon.svg           small-size mark
docs/assets/social.svg     1280x630 social preview (open graph / twitter card)
docs/assets/social.png     the same, rasterised for crawlers that ignore SVG
favicon.ico                multi-size favicon for the GitHub tab

Design intent: the mark is a *nested diamond* — an experience contains semantics
contains a single kernel. Three nested outlines read as a graph traversal at a
glance, which is the whole idea. Cyan -> violet on a near-black ground, with a
single pink node marking the thing you were asking about.

Everything is drawn from one palette and one geometry function, so the mark, the
wordmark, the favicon and the social card cannot drift apart.
"""
from __future__ import annotations
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
ASSETS = DOCS / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- palette
INK = "#0B0F19"        # near-black ground
INK_2 = "#111827"      # panel
CYAN = "#22D3EE"       # outer — the experience
VIOLET = "#A78BFA"     # middle — the semantics
PINK = "#F472B6"       # kernel — the thing you asked about
TEXT = "#E5E7EB"
MUTED = "#94A3B8"


# ---------------------------------------------------------------- geometry
def diamond(cx: float, cy: float, r: float) -> str:
    """A square rotated 45 degrees, as an SVG path."""
    return (f"M{cx:.2f} {cy - r:.2f} "
            f"L{cx + r:.2f} {cy:.2f} "
            f"L{cx:.2f} {cy + r:.2f} "
            f"L{cx - r:.2f} {cy:.2f} Z")


def diamond_points(cx: float, cy: float, r: float, n: int = 4, rot: float = -math.pi / 2):
    return [(cx + r * math.cos(rot + i * 2 * math.pi / n),
             cy + r * math.sin(rot + i * 2 * math.pi / n)) for i in range(n)]


def mark_svg(size: int, *, bg: bool = True, stroke_scale: float = 1.0) -> str:
    """The mark, square, centred on `size`."""
    c = size / 2
    sw = max(2.0, size * 0.052 * stroke_scale)
    parts = []
    if bg:
        parts.append(f'<rect width="{size}" height="{size}" rx="{size * 0.1875:.1f}" fill="{INK}"/>')
    parts.append(
        f'<g fill="none" stroke-width="{sw:.2f}" stroke-linejoin="round" stroke-linecap="round">')
    parts.append(f'<path d="{diamond(c, c, size * 0.335)}" stroke="{CYAN}"/>')
    parts.append(f'<path d="{diamond(c, c, size * 0.195)}" stroke="{VIOLET}"/>')
    parts.append("</g>")
    r = size * 0.052
    parts.append(f'<circle cx="{c:.2f}" cy="{c:.2f}" r="{r:.2f}" fill="{PINK}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
            f'viewBox="0 0 {size} {size}" role="img" aria-label="XIR">'
            + "".join(parts) + "</svg>")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
    print(f"  {path.relative_to(ROOT)}  ({len(text)} bytes)")


# ---------------------------------------------------------------- social card
def social_svg(w: int = 1280, h: int = 630) -> str:
    """Open-graph card: mark, wordmark, one-line pitch, a live terminal line."""
    s = w / 1280.0
    fs = lambda n: round(n * s, 1)
    grid = []
    for i in range(1, 22):
        x = i * w / 22
        grid.append(f'<line x1="{x:.0f}" y1="0" x2="{x:.0f}" y2="{h}" '
                    f'stroke="{INK_2}" stroke-width="1"/>')
    for j in range(1, 11):
        y = j * h / 11
        grid.append(f'<line x1="0" y1="{y:.0f}" x2="{w}" y2="{y:.0f}" '
                    f'stroke="{INK_2}" stroke-width="1"/>')

    # a faint node-link motif, echoing the semantic graph
    motif = [f'<circle cx="{fs(1020)}" cy="{fs(190)}" r="{fs(9)}" fill="{PINK}"/>',
             f'<circle cx="{fs(1140)}" cy="{fs(300)}" r="{fs(7)}" fill="{VIOLET}"/>',
             f'<circle cx="{fs(940)}" cy="{fs(340)}" r="{fs(7)}" fill="{VIOLET}"/>',
             f'<line x1="{fs(1020)}" y1="{fs(190)}" x2="{fs(1140)}" y2="{fs(300)}" '
             f'stroke="{VIOLET}" stroke-width="{fs(2)}" opacity="0.55"/>',
             f'<line x1="{fs(1020)}" y1="{fs(190)}" x2="{fs(940)}" y2="{fs(340)}" '
             f'stroke="{VIOLET}" stroke-width="{fs(2)}" opacity="0.55"/>',
             f'<circle cx="{fs(1090)}" cy="{fs(470)}" r="{fs(6)}" fill="{CYAN}"/>',
             f'<line x1="{fs(1140)}" y1="{fs(300)}" x2="{fs(1090)}" y2="{fs(470)}" '
             f'stroke="{CYAN}" stroke-width="{fs(2)}" opacity="0.4"/>']

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{INK}"/>
      <stop offset="100%" stop-color="#0E1424"/>
    </linearGradient>
    <radialGradient id="glow" cx="72%" cy="34%" r="46%">
      <stop offset="0%" stop-color="{VIOLET}" stop-opacity="0.20"/>
      <stop offset="100%" stop-color="{VIOLET}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="{w}" height="{h}" fill="url(#g)"/>
  <g opacity="0.55">{''.join(grid)}</g>
  <rect width="{w}" height="{h}" fill="url(#glow)"/>
  {''.join(motif)}

  <g transform="translate({fs(96)}, {fs(150)}) scale({fs(0.36)})">
    <g fill="none" stroke-width="{fs(8.5)}" stroke-linejoin="round">
      <path d="{diamond(fs(100), fs(100), fs(67))}" stroke="{CYAN}"/>
      <path d="{diamond(fs(100), fs(100), fs(39))}" stroke="{VIOLET}"/>
    </g>
    <circle cx="{fs(100)}" cy="{fs(100)}" r="{fs(10.4)}" fill="{PINK}"/>
  </g>

  <text x="{fs(230)}" y="{fs(230)}" font-family="Inter, Segoe UI, Helvetica, Arial, sans-serif"
        font-size="{fs(96)}" font-weight="700" letter-spacing="{fs(-2)}" fill="{TEXT}">XIR</text>
  <text x="{fs(232)}" y="{fs(288)}" font-family="Inter, Segoe UI, Helvetica, Arial, sans-serif"
        font-size="{fs(27)}" font-weight="500" letter-spacing="{fs(1.2)}" fill="{MUTED}">SEMANTIC IR FOR INTERACTIVE PRODUCTS</text>

  <text x="{fs(96)}" y="{fs(410)}" font-family="Inter, Segoe UI, Helvetica, Arial, sans-serif"
        font-size="{fs(46)}" font-weight="600" fill="{TEXT}">Give an agent the exact</text>
  <text x="{fs(96)}" y="{fs(468)}" font-family="Inter, Segoe UI, Helvetica, Arial, sans-serif"
        font-size="{fs(46)}" font-weight="600" fill="{TEXT}">semantic slice it needs.</text>

  <rect x="{fs(96)}" y="{fs(516)}" width="{fs(1088)}" height="{fs(62)}" rx="{fs(10)}"
        fill="#0A0E17" stroke="#1E293B"/>
  <text x="{fs(120)}" y="{fs(556)}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace"
        font-size="{fs(25)}" fill="{CYAN}">$ xir trace app.xir archiveProject</text>
  <text x="{fs(724)}" y="{fs(556)}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace"
        font-size="{fs(25)}" fill="{PINK}">MUTATES field.project.status</text>
</svg>'''


# ---------------------------------------------------------------- wordmark
def wordmark_svg(w: int = 720, h: int = 120) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"
     role="img" aria-label="XIR">
  <g transform="translate(8, 6)">
    <g fill="none" stroke-width="6.5" stroke-linejoin="round">
      <path d="{diamond(54, 54, 44)}" stroke="{CYAN}"/>
      <path d="{diamond(54, 54, 25)}" stroke="{VIOLET}"/>
    </g>
    <circle cx="54" cy="54" r="8.5" fill="{PINK}"/>
  </g>
  <text x="128" y="80" font-family="Inter, Segoe UI, Helvetica, Arial, sans-serif"
        font-size="66" font-weight="700" letter-spacing="-1.5" fill="{TEXT}">XIR</text>
</svg>'''


# ---------------------------------------------------------------- favicon.ico
def write_ico(path: Path, sizes=(16, 32, 48, 64, 128, 256)) -> None:
    """ICO is a container of PNGs, so render each size with Pillow and splice."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("  (Pillow not installed; skipping favicon.ico)")
        return
    import io
    import struct

    images = []
    for s in sizes:
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        c, r = s / 2, s / 2
        sw = max(1, round(s * 0.052))
        for rad, col in ((s * 0.335, CYAN), (s * 0.195, VIOLET)):
            d.polygon(diamond_points(c, c, rad), outline=col, width=sw)
        kr = max(1, s * 0.052)
        d.ellipse([c - kr, c - kr, c + kr, c + kr], fill=PINK)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        images.append((s, buf.getvalue()))

    out = io.BytesIO()
    out.write(struct.pack("<HHH", 0, 1, len(images)))
    offset = 6 + 16 * len(images)
    for s, data in images:
        out.write(struct.pack("<BBBBHHII", 0 if s == 256 else s, 0 if s == 256 else s,
                              0, 0, 1, 32, len(data), offset))
        offset += len(data)
    for _, data in images:
        out.write(data)
    path.write_bytes(out.getvalue())
    print(f"  {path.relative_to(ROOT)}  ({len(out.getvalue())} bytes, {len(sizes)} sizes)")


# ---------------------------------------------------------------- social png
def _font(kind: str, size: int):
    """DejaVu, which ships with matplotlib — so this needs no system fonts."""
    import os
    import glob
    import matplotlib
    from PIL import ImageFont
    d = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
    if kind == "mono":
        pats = ["DejaVuSansMono-Bold.ttf", "DejaVuSansMono.ttf"]
    else:
        pats = ["DejaVuSans-Bold.ttf", "DejaVuSans.ttf"]
    for p in pats:
        hit = glob.glob(os.path.join(d, p))
        if hit:
            return ImageFont.truetype(hit[0], size)
    return ImageFont.load_default()


def _hex(c: str) -> tuple[int, int, int]:
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def write_social_png(svg_path: Path, png_path: Path, w: int = 1280, h: int = 630) -> None:
    """Rasterise the social card.

    Tries cairosvg/resvg first, then draws the same composition with Pillow so the
    asset is always produced without a native toolchain.
    """
    def _cairosvg():
        import cairosvg
        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path),
                         output_width=w, output_height=h)

    def _resvg():
        import subprocess
        subprocess.run(["resvg", str(svg_path), str(png_path)], check=True,
                       capture_output=True)

    for attempt in (_cairosvg, _resvg):
        try:
            attempt()
            print(f"  {png_path.relative_to(ROOT)}")
            return
        except Exception:
            continue

    from PIL import Image, ImageDraw, ImageFilter
    img = Image.new("RGB", (w, h), _hex(INK))
    d = ImageDraw.Draw(img, "RGBA")

    # glow behind the motif
    glow = Image.new("RGB", (w, h), _hex(INK))
    gd = ImageDraw.Draw(glow)
    for i in range(60, 0, -1):
        r = int(w * 0.55 * i / 60)
        gd.ellipse([w * 0.72 - r, h * 0.34 - r, w * 0.72 + r, h * 0.34 + r],
                   fill=tuple(int(c * 0.014) for c in _hex(VIOLET)))
    img = Image.blend(img, glow, 0.0)
    img = Image.composite(Image.blend(img, glow, 0.55), img,
                          Image.new("L", (w, h), 0))
    d = ImageDraw.Draw(img, "RGBA")

    # grid
    for i in range(1, 22):
        d.line([(i * w / 22, 0), (i * w / 22, h)], fill=_hex(INK_2), width=1)
    for j in range(1, 11):
        d.line([(0, j * h / 11), (w, j * h / 11)], fill=_hex(INK_2), width=1)

    # node-link motif
    motif = [((1020, 190), 9, PINK), ((1140, 300), 7, VIOLET), ((940, 340), 7, VIOLET),
             ((1090, 470), 6, CYAN)]
    for a, b, col in [((1020, 190), (1140, 300), VIOLET), ((1020, 190), (940, 340), VIOLET),
                      ((1140, 300), (1090, 470), CYAN)]:
        d.line([a, b], fill=_hex(col) + (150,), width=2)
    for (x, y), r, col in motif:
        d.ellipse([x - r, y - r, x + r, y + r], fill=_hex(col))

    # mark
    cx, cy = 172, 214
    for rad, col, wdt in ((56, CYAN, 7), (33, VIOLET, 7)):
        d.polygon(diamond_points(cx, cy, rad), outline=_hex(col), width=wdt)
    d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=_hex(PINK))

    sans, mono = "sans", "mono"
    d.text((230, 150), "XIR", font=_font(sans, 96), fill=_hex(TEXT), anchor="ls")
    d.text((232, 196), "SEMANTIC IR FOR INTERACTIVE PRODUCTS",
           font=_font(sans, 27), fill=_hex(MUTED), anchor="ls")
    d.text((96, 356), "Give an agent the exact", font=_font(sans, 46), fill=_hex(TEXT), anchor="ls")
    d.text((96, 412), "semantic slice it needs.", font=_font(sans, 46), fill=_hex(TEXT), anchor="ls")

    d.rounded_rectangle([96, 500, 96 + 1088, 500 + 62], radius=10,
                        fill=_hex("#0A0E17"), outline=_hex("#1E293B"), width=1)
    d.text((120, 531), "$ xir trace app.xir archiveProject",
           font=_font(mono, 25), fill=_hex(CYAN), anchor="lm")
    d.text((700, 531), "MUTATES field.project.status",
           font=_font(mono, 25), fill=_hex(PINK), anchor="lm")

    img.save(png_path, "PNG", optimize=True)
    print(f"  {png_path.relative_to(ROOT)}  (Pillow fallback)")


def main() -> None:
    print("brand assets:")
    write(DOCS / "logo.svg", mark_svg(128))
    write(DOCS / "logo-light.svg", mark_svg(128, bg=False))
    write(DOCS / "favicon.svg", mark_svg(32, stroke_scale=1.25))
    write(DOCS / "wordmark.svg", wordmark_svg())
    social = ASSETS / "social.svg"
    write(social, social_svg())
    write_social_png(social, ASSETS / "social.png")
    write_ico(ROOT / "favicon.ico")
    print("\nPalette:", f"ink={INK} cyan={CYAN} violet={VIOLET} pink={PINK}")


if __name__ == "__main__":
    main()
