"""Tolerant .xir parser -> AST. Strict Lark first, brace fallback."""
from __future__ import annotations
import re
from pathlib import Path
from xir.ast.nodes import Experience, Entity, Capability, Surface, Flow, Meta

_SOURCES = {"human", "requirement-document", "code", "design", "API", "test", "analytics", "inference", "agent"}
_CONF = {"confirmed", "probable", "inferred", "tentative", "proposed", "deprecated", "unknown"}

def _prov(body: str) -> dict[str, str]:
    m = re.search(r'provenance\s*\{(.*?)\}', body, re.S)
    if not m:
        return {}
    out = {}
    for mm in re.finditer(r'(source|reference|confidence)\s*:?\s*(.*?)(?=\b(?:source|reference|confidence)\s*:|$)', m.group(1), re.S):
        out[mm.group(1)] = mm.group(2).strip().strip(',').strip('"')
    return {k: v for k, v in out.items() if v}

def _strip_prov(body: str) -> str:
    return re.sub(r'provenance\s*\{.*?\}', '', body, flags=re.S)

_EXP = re.compile(r'experience\s+(\w+)')
_GOAL = re.compile(r'goal\s*:?\s*"([^"]+)"')
_ACTORS = re.compile(r'actors\s*\{([^}]*)\}', re.S)
_ENTITY = re.compile(r'entity\s+(\w+)\s*\{([^}]*)\}', re.S)
def _blocks(text: str, keyword: str) -> list[tuple[str, str]]:
    out = []
    pat = re.compile(rf'{keyword}\s+(\w+)\s*\{{', re.S)
    for m in pat.finditer(text):
        name = m.group(1)
        i = m.end()
        depth = 1
        while i < len(text) and depth:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        out.append((name, text[m.end():i - 1]))
    return out

def _attrs(body: str) -> dict[str, str]:
    out = {}
    for m in re.finditer(r'(\w+)\s*:\s*([A-Za-z_][\w\|\[\] ]*)', body):
        out[m.group(1)] = m.group(2).strip()
    return out

def parse_text(text: str) -> Experience:
    try:
        from xir.parser.strict import parse_strict
        return parse_strict(text)
    except Exception:
        return parse_tolerant(text)


def parse_tolerant(text: str) -> Experience:
    m = _EXP.search(text)
    name = m.group(1) if m else "App"
    g = _GOAL.search(text)
    goal = g.group(1) if g else ""
    mv = re.search(r'version\s*:?\s*(\w[\w\.\-]*)', text)
    version = mv.group(1) if mv else ""
    actors: list[str] = []
    am = _ACTORS.search(text)
    if am:
        actors = re.findall(r'\w+', am.group(1))
    meta: list[Meta] = []
    for kind in ("requirement", "observation", "decision", "assumption", "inference", "proposal"):
        for mm in re.finditer(rf'(?:^|\n)\s*{kind}\s*:?\s*"([^"]+)"', text):
            meta.append(Meta(kind, mm.group(1)))
    entities = [Entity(n, _attrs(_strip_prov(b)), _prov(b)) for n, b in _blocks(text, "entity")]
    caps = []
    for n, b in _blocks(text, "capability"):
        inp = {}
        mi = re.search(r'input\s*\{(.*?)\}', b, re.S)
        if mi:
            inp = _attrs(mi.group(1))
        mo = re.search(r'output\s*:?\s*(\w+)', b)
        mr = re.search(r'requires\s*:?\s*([^\n]+)', b)
        me = re.search(r'effects\s*:?\s*([^\n]+)', b)
        caps.append(Capability(
            name=n, input=inp,
            output=mo.group(1) if mo else "",
            requires=re.findall(r'[\w\.]+', mr.group(1)) if mr else [],
            effects=[me.group(1).strip()] if me else [],
            confirmation="confirmation" in b and "required" in b,
            audit="audit" in b and "required" in b,
            provenance=_prov(b),
        ))
    surfaces = []
    for n, b in _blocks(text, "surface"):
        mp = re.search(r'presents\s*:?\s*([\w\.\[\]]+)', b)
        ms = re.search(r'states\s*:?\s*([^\n]+)', b)
        comps = re.findall(r'(?:components?|layout|Header|Main|Sidebar|Content|ProjectList|action)\s*\{?([^}\n]*)\}?', b)
        flat = []
        for c in comps:
            flat += re.findall(r'\w+', c)
        surfaces.append(Surface(n, mp.group(1) if mp else "",
            flat, re.findall(r'\w+', ms.group(1)) if ms else [], _prov(b)))
    flows = []
    for n, b in _blocks(text, "flow"):
        ma = re.search(r'actor\s*:?\s*(\w+)', b)
        steps = re.findall(r'(\w+)\s*->\s*(\w+)', b)
        flat = [s for pair in steps for s in pair]
        if not flat:
            flat = re.findall(r'^\s*(\w+)\s*$', b, re.M)
        flows.append(Flow(n, ma.group(1) if ma else "", flat, _prov(b)))
    exp = Experience(name, goal, version, actors, entities, caps, surfaces, flows, meta)
    return exp

def parse_file(path: str | Path) -> Experience:
    return parse_text(Path(path).read_text(encoding="utf-8"))
