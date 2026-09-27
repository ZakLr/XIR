"""Semantic IR: stable identity and the canonical model.

`load` / `load_file` / `graph_of` are re-exported lazily (PEP 562) so that importing
`xir.ir.ids` or `xir.ir.model` does not drag in the parser. Loading needs the parser,
and the normalizer needs this package, so an eager import would be circular.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from xir.ir.ids import camel, make_id, valid_id, kind_of, KINDS  # noqa: F401
from xir.ir.model import Model, Rel, Provenance  # noqa: F401

if TYPE_CHECKING:  # pragma: no cover
    from xir.parser.parse import ParseError
    from xir.semantic.graph import Graph

__all__ = ["load", "load_text", "load_file", "graph_of", "parse_text", "parse_file",
           "ParseError", "Model", "Rel", "Provenance", "camel", "make_id",
           "valid_id", "kind_of", "KINDS"]


def load(text: str) -> "Model":
    from xir.parser.parse import parse_text
    from xir.semantic.normalize import normalize
    return normalize(parse_text(text))


def load_file(path) -> "Model":
    from xir.parser.parse import parse_file
    from xir.semantic.normalize import normalize
    return normalize(parse_file(path))


def graph_of(m: "Model") -> "Graph":
    from xir.semantic.graph import build_graph
    return build_graph(m)


def __getattr__(name: str):
    if name in ("parse_text", "parse_file", "ParseError"):
        from xir.parser import parse as _p
        return getattr(_p, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


load_text = load
