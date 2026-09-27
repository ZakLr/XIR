#!/usr/bin/env python3
"""Render the XIR figures as PNG with Pillow.

    python branding/generate_diagram.py

  docs/assets/pipeline.png    the compiler pipeline, source -> projections
  docs/assets/graph.png       the ACTUAL semantic graph around archiveProject,
                              laid out from the real edges of the canonical model

The second figure is generated from `xir.ir`, so it cannot drift from what the
tool does. If the ontology changes, the picture changes with it.

PNG rather than SVG on purpose: this runs with no native toolchain, so the
assets are reproducible on any machine, and every figure is one this script
has actually rendered and looked at.
"""
from __future__ import annotations
import os
import glob
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "docs" / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

S = 2                                   # supersample, then downscale for clean edges
INK, INK_2, INK_3 = "#0B0F19", "#111827", "#0A0E17"
CYAN, VIOLET, PINK = "#22D3EE", "#A78BFA", "#F472B6"
AMBER, GREEN, TEXT, MUTED = "#FBBF24", "#4ADE80", "#E5E7EB", "#94A3B8"


def _hex(c: str):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def _font(kind: str, size: int):
    import matplotlib
    d = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
    names = (["DejaVuSans-Bold.ttf", "DejaVuSans.ttf"] if kind == "bold"
             else ["DejaVuSansMono.ttf"] if kind == "mono"
             else ["DejaVuSans.ttf"])
    for n in names:
        hit = glob.glob(os.path.join(d, n))
        if hit:
            return ImageFont.truetype(hit[0], size)
    return ImageFont.load_default()


def canvas(w: int, h: int):
    img = Image.new("RGB", (w * S, h * S), _hex(INK))
    return img, ImageDraw.Draw(img, "RGBA"), w, h


def save(img, w: int, h: int, path: Path):
    img.resize((w, h), Image.LANCZOS).save(path, "PNG", optimize=True)
    print(f"  {path.relative_to(ROOT)}  {w}x{h}  {path.stat().st_size // 1024} KB")


def diamond(d, cx, cy, r, col, wd):
    pts = [(cx + r * math.cos(-math.pi / 2 + i * math.pi / 2),
            cy + r * math.sin(-math.pi / 2 + i * math.pi / 2)) for i in range(4)]
    d.polygon(pts, outline=_hex(col), width=wd)


def arrow(d, x0, y0, x1, y1, col, wd=2):
    d.line([(x0, y0), (x1, y1)], fill=_hex(col) + (150,), width=wd)
    a = math.atan2(y1 - y0, x1 - x0)
    for s in (0.5, -0.5):
        d.line([(x1, y1), (x1 - 9 * math.cos(a + s), y1 - 9 * math.sin(a + s))],
               fill=_hex(col) + (150,), width=wd)


# ============================================================ pipeline
def pipeline(path: Path) -> None:
    W, H = 1240, 500
    img, d, W, H = canvas(W, H)
    stages = [
        ("source", "app.xir", CYAN, "authored"),
        ("strict parse", "Earley", VIOLET, "raises on bad input"),
        ("syntax AST", "ast/", VIOLET, "what was written"),
        ("normalize", "semantic/", PINK, "identity + resolution"),
        ("semantic IR", "ir/", PINK, "SOURCE OF TRUTH"),
        ("typed graph", "graph.py", AMBER, "typed edges"),
    ]
    consumers = ["validate", "query", "patch", "diff", "compile"]
    targets = ["react", "html", "a2ui", "docs", "a11y", "playwright"]

    f_title = _font("bold", 14 * S)
    f_sub = _font("mono", 11 * S)
    f_note = _font("", 10 * S)
    f_small = _font("mono", 13 * S)
    f_lbl = _font("bold", 10 * S)

    bw, bh, gap = 182 * S, 78 * S, 22 * S
    x0, y = 32 * S, 78 * S

    # the band that owns meaning
    # the semantic layer is normalize + IR; the graph is built *from* it
    band_x = x0 + 3 * (bw + gap) - 14 * S
    band_w = 2 * bw + 2 * gap + 28 * S
    d.rounded_rectangle([band_x, y - 30 * S, band_x + band_w, y + bh + 28 * S],
                        radius=14 * S, outline=_hex(PINK) + (140,), width=2)
    d.text((band_x + band_w / 2, y - 16 * S), "SEMANTIC LAYER",
           font=f_lbl, fill=_hex(PINK), anchor="mm")

    for i, (title, sub, col, note) in enumerate(stages):
        x = x0 + i * (bw + gap)
        d.rounded_rectangle([x, y, x + bw, y + bh], radius=12 * S,
                            fill=_hex(INK_2), outline=_hex(col), width=2)
        d.text((x + bw / 2, y + 28 * S), title, font=f_title, fill=_hex(TEXT), anchor="mm")
        d.text((x + bw / 2, y + 50 * S), sub, font=f_sub, fill=_hex(col), anchor="mm")
        d.text((x + bw / 2, y + bh + 15 * S), note, font=f_note, fill=_hex(MUTED), anchor="mm")
        if i:
            arrow(d, x - gap + 4, y + bh / 2, x - 6, y + bh / 2, MUTED, 2)

    # agent operations read the semantic layer
    cy0 = 288 * S
    for i, name in enumerate(consumers):
        x = x0 + i * (bw + gap) * 0.92
        d.rounded_rectangle([x, cy0, x + 140 * S, cy0 + 42 * S], radius=10 * S,
                            fill=_hex(INK_2), outline=_hex(GREEN), width=2)
        d.text((x + 70 * S, cy0 + 21 * S), name, font=f_small, fill=_hex(TEXT), anchor="mm")
        d.line([(x + 70 * S, cy0 - 2), (x + 70 * S, y + bh + 24 * S)],
               fill=_hex(GREEN) + (100,), width=1)

    # projections
    ty = 404 * S
    d.text((x0, ty - 18 * S), "PROJECTIONS", font=f_lbl, fill=_hex(MUTED))
    tw = (W * S - x0 * 2 - 5 * 12 * S) / 6
    for i, name in enumerate(targets):
        x = x0 + i * (tw + 12 * S)
        d.rounded_rectangle([x, ty, x + tw, ty + 42 * S], radius=9 * S,
                            outline=_hex(CYAN) + (190,), width=2)
        d.text((x + tw / 2, ty + 21 * S), name, font=f_small, fill=_hex(CYAN), anchor="mm")
        if i < 5:
            d.line([(x + tw / 2, cy0 + 42 * S), (x + tw / 2, ty - 6 * S)],
                   fill=_hex(CYAN) + (85,), width=1)

    save(img, W, H, path)


# ============================================================ real graph
def graph(path: Path) -> None:
    import xir.ir as XIR
    from xir.semantic.graph import build_graph, Rel

    m = XIR.load_file(ROOT / "examples" / "project-manager" / "app.xir")
    g = build_graph(m)
    focus = "capability.archiveProject"

    # walk backwards: capability <- interaction -> component <- surface
    interactions = [i for i in m.interactions if m.interactions[i].invokes == focus][:1]
    comps = [m.interactions[i].target for i in interactions if m.interactions[i].target][:1]
    surfaces = [s for c in comps for s in g.inc(c, Rel.CONTAINS)[:1]]

    perms = [t for _, t, dd in g.g.out_edges(focus, data=True) if dd.get("rel") == Rel.REQUIRES]
    mutes = [t for _, t, dd in g.g.out_edges(focus, data=True) if dd.get("rel") == Rel.MUTATES]
    emitted = [t for _, t, dd in g.g.out_edges(focus, data=True) if dd.get("rel") == Rel.EMITS]
    triggered = [t for e in emitted for t in g.out(e, Rel.TRIGGERS)[:1]]

    left = [("SURFACE", surfaces, "exposes"),
            ("COMPONENT", comps, "invokes"),
            ("INTERACTION", interactions, "invokes")]
    right = [("PERMISSION", perms, "requires"),
             ("MUTATES", mutes, "mutates"),
             ("EMITS", emitted, "emits"),
             ("TRIGGERS", triggered, "triggers")]

    W, H = 1180, 580
    img, d, W, H = canvas(W, H)
    f_h1 = _font("bold", 19 * S)
    f_h2 = _font("mono", 12 * S)
    f_kind = _font("bold", 10 * S)
    f_name = _font("mono", 13 * S)
    f_id = _font("mono", 9 * S)
    f_rel = _font("", 10 * S)

    d.text((34 * S, 40 * S), "The chain, from the real model",
           font=f_h1, fill=_hex(TEXT))
    d.text((34 * S, 62 * S),
           'xir trace app.xir archiveProject  —  laid out from the semantic graph, not drawn by hand',
           font=f_h2, fill=_hex(MUTED))

    bw, bh, rh = 300 * S, 70 * S, 20 * S
    cx, cy = (W * S) / 2 - bw / 2, 150 * S

    def node(x, y, w, kind, ident, col):
        node_obj = m.get(ident)
        name = node_obj.name if node_obj else ident
        short = ident.split(".", 1)[1] if "." in ident else ident
        d.rounded_rectangle([x, y, x + w, y + bh], radius=10 * S,
                            fill=_hex(INK_2), outline=_hex(col), width=2)
        d.text((x + 12 * S, y + 14 * S), kind, font=f_kind, fill=_hex(col))
        d.text((x + 12 * S, y + 36 * S), name, font=f_name, fill=_hex(TEXT))
        d.text((x + 12 * S, y + 58 * S), short[:34], font=f_id, fill=_hex(MUTED))

    def stack(groups, x, side):
        out, y = [], 104 * S
        for kind, ids, rel in groups:
            if not ids:
                continue
            d.text((x, y - 12 * S), kind, font=f_kind, fill=_hex(MUTED))
            for i, ident in enumerate(ids):
                col = {"SURFACE": CYAN, "COMPONENT": CYAN, "INTERACTION": "#67E8F9",
                       "PERMISSION": AMBER, "MUTATES": GREEN, "EMITS": VIOLET,
                       "TRIGGERS": "#C4B5FD"}[kind]
                yy = y + i * (bh + rh)
                node(x, yy, bw - 20 * S, kind, ident, col)
                if side == "left":
                    arrow(d, x + bw - 20 * S, yy + bh / 2, cx - 6, cy + bh / 2, MUTED, 2)
                    d.text(((x + bw - 20 * S + cx) / 2, yy + bh / 2 - 6 * S), rel,
                           font=f_rel, fill=_hex(MUTED), anchor="mm")
                else:
                    arrow(d, cx + bw + 6 * S, cy + bh / 2, x - 6, cy + bh / 2 and yy + bh / 2, MUTED, 2)
                    d.text(((cx + bw + 6 * S + x) / 2, yy + bh / 2 - 6 * S), rel,
                           font=f_rel, fill=_hex(MUTED), anchor="mm")
            y += len(ids) * (bh + rh) + 18 * S
        return out

    stack(left, 34 * S, "left")
    stack(right, W * S - (bw - 20 * S) - 34 * S, "right")

    d.rounded_rectangle([cx, cy, cx + bw, cy + bh], radius=10 * S,
                        fill=_hex(INK_3), outline=_hex(PINK), width=3)
    d.text((cx + 12 * S, cy + 14 * S), "CAPABILITY", font=f_kind, fill=_hex(PINK))
    d.text((cx + 12 * S, cy + 36 * S), m.capabilities[focus].name,
           font=_font("mono", 15 * S), fill=_hex(TEXT))
    d.text((cx + 12 * S, cy + 58 * S), focus.split(".", 1)[1], font=f_id, fill=_hex(MUTED))
    d.text((cx + bw / 2, cy + bh + 20 * S),
           "confirm · audit · consumes Project · returns Project",
           font=f_rel, fill=_hex(MUTED), anchor="mm")

    save(img, W, H, path)


def main() -> None:
    print("figures:")
    pipeline(ASSETS / "pipeline.png")
    graph(ASSETS / "graph.png")


if __name__ == "__main__":
    main()
