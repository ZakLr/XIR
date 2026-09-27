"""Strict Lark parser -> AST. Raises on syntax error; caller falls back."""
from __future__ import annotations
from pathlib import Path
from lark import Lark, Transformer, Token

_GRAMMAR = Path(__file__).with_name("grammar.lark").read_text(encoding="utf-8")

class _T(Transformer):
    def _pairs(self, items):
        for it in items:
            if isinstance(it, list):
                yield from self._pairs(it)
            elif isinstance(it, tuple) and len(it) == 2 and isinstance(it[0], str):
                yield it
    def start(self, items):
        return items[0]
    def experience(self, items):
        name = str(items[0])
        body = list(self._pairs(items[1:]))
        kw = {"goal": "", "version": "", "actors": [], "entities": [], "capabilities": [], "surfaces": [], "flows": [], "meta": []}
        for kind, val in body:
            if kind in ("goal", "version", "actors"):
                kw[kind] = val
            elif kind == "meta":
                kw["meta"].append(val)
            elif kind in ("entities", "capabilities", "surfaces", "flows"):
                kw[kind].append(val)
        from xir.ast.nodes import Experience
        return Experience(name=name, **kw)
    def exp_body(self, items):
        return list(items)
    def goal(self, items):
        s = str(items[-1])
        return ("goal", s.strip('"'))
    def version_stmt(self, items):
        return ("version", str(items[-1]))
    def meta_stmt(self, items):
        from xir.ast.nodes import Meta
        kind = str(items[0])
        text = str(items[-1]).strip('"')
        return ("meta", Meta(kind, text))
    def provenance_block(self, items):
        import re as _re
        prov: dict[str, str] = {}
        for k, v in self._pairs(items):
            parts = _re.findall(r'(source|reference|confidence)\s*:?\s*(.*?)(?=\b(?:source|reference|confidence)\s*:|$)', v, _re.S)
            if parts:
                for pk, pv in parts:
                    pv = pv.strip().strip(',').strip('"')
                    if pv:
                        prov[pk] = pv
            else:
                prov[k] = v
        return ("provenance", prov)
    def prov_attr(self, items):
        return (str(items[0]), str(items[-1]).strip())
    def actors(self, items):
        return ("actors", [str(i) for i in items])
    def entity(self, items):
        from xir.ast.nodes import Entity
        name = str(items[0])
        pairs = list(self._pairs(items[1:]))
        prov = {}
        attrs = {}
        for k, v in pairs:
            if k == "provenance":
                prov = v
            else:
                attrs[k] = v
        return ("entities", Entity(name, attrs, prov))
    def attr(self, items):
        parts = [str(i) for i in items if str(i) not in (":", "|")]
        return (parts[0], " | ".join(parts[1:]))
    def union_type(self, items):
        return " | ".join(str(i) for i in items if str(i) != "|")
    def capability(self, items):
        from xir.ast.nodes import Capability
        name = str(items[0])
        kw: dict = {}
        for k, v in self._pairs(items[1:]):
            kw[k] = v
        return ("capabilities", Capability(name=name, input=kw.get("input", {}),
            output=kw.get("output", ""), requires=kw.get("requires", []),
            effects=kw.get("effects", []), confirmation=kw.get("confirmation", False),
            audit=kw.get("audit", False), provenance=kw.get("provenance", {})))
    def cap_body(self, items):
        return list(items)
    def cap_input(self, items):
        return ("input", dict(self._pairs(items)))
    def cap_output(self, items):
        return ("output", str(items[-1]))
    def cap_requires(self, items):
        return ("requires", [str(i) for i in items if not (isinstance(i, Token) and i.value == "requires") and str(i) not in (",", "requires")])
    def cap_effects(self, items):
        return ("effects", [str(items[-1]).strip().lstrip(":").strip()])
    def cap_confirm(self, items):
        return ("confirmation", str(items[-1]) in ("required", "true"))
    def cap_audit(self, items):
        return ("audit", str(items[-1]) in ("required", "true"))
    def surface(self, items):
        from xir.ast.nodes import Surface
        name = str(items[0])
        presents, comps, states, prov = "", [], [], {}
        for k, v in self._pairs(items[1:]):
            if k == "presents":
                presents = v
            elif k == "components":
                comps = v
            elif k == "states":
                states = v
            elif k == "provenance":
                prov = v
        return ("surfaces", Surface(name, presents, comps, states, prov))
    def surf_body(self, items):
        return list(items)
    def surf_presents(self, items):
        return ("presents", str(items[-1]))
    def surf_comp(self, items):
        names = [str(i) for i in items if str(i) not in ("components", "layout", "{", "}")]
        return ("components", names)
    def surf_states(self, items):
        return ("states", [str(i) for i in items if str(i) not in ("states", ":", ",")])
    def flow(self, items):
        from xir.ast.nodes import Flow
        name = str(items[0])
        actor, steps, prov = "", [], {}
        for k, v in self._pairs(items[1:]):
            if k == "actor":
                actor = v
            elif k == "provenance":
                prov = v
            else:
                steps += v if isinstance(v, list) else [v]
        return ("flows", Flow(name, actor, steps, prov))
    def flow_body(self, items):
        return list(items)
    def flow_actor(self, items):
        return ("actor", str(items[-1]))
    def flow_edge(self, items):
        return ("steps", [str(items[0]), str(items[1])])
    def flow_step(self, items):
        return ("steps", [str(items[-1])])

_parser = Lark(_GRAMMAR, parser="lalr", transformer=_T(), maybe_placeholders=False)

def parse_strict(text: str):
    return _parser.parse(text)
