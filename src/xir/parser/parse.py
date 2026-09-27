"""Parser entry points and the strict/recovery policy (§21).

`parse_text` is strict: invalid XIR raises. It never degrades silently into a
plausible-but-wrong model. `recover_text` is the explicit opt-in best-effort mode
and marks what it could not resolve.
"""
from __future__ import annotations
import re
from pathlib import Path
from xir.ast import nodes as A
from xir.parser.strict import parse_strict
from xir.semantic.normalize import normalize, Normalizer
from xir.ir.model import Model


class ParseError(Exception):
    """Invalid XIR. Carries a line/column when the parser provides one."""


def _loc(exc: Exception) -> tuple[int, int] | None:
    for attr in ("line", "column"):
        pass
    line = getattr(exc, "line", None)
    col = getattr(exc, "column", None)
    if line:
        return int(line), int(col or 0)
    return None


def parse_strict_text(text: str) -> A.Experience:
    try:
        return parse_strict(text)
    except ParseError:
        raise
    except Exception as exc:
        loc = _loc(exc)
        where = f" at line {loc[0]}, column {loc[1]}" if loc else ""
        raise ParseError(f"invalid XIR{where}: {str(exc).splitlines()[0]}") from exc


def parse_text(text: str) -> A.Experience:
    """Strict. Raises ParseError on anything the grammar rejects."""
    return parse_strict_text(text)


def parse_file(path: str | Path) -> A.Experience:
    return parse_text(Path(path).read_text(encoding="utf-8"))


def recover_text(text: str) -> tuple[Model, list[str]]:
    """Best-effort recovery. Returns the model plus an explicit list of problems.

    Recovery never invents semantics: unresolvable references are dropped and
    reported so the caller knows the model is incomplete.
    """
    problems: list[str] = []
    ast = _tolerant_ast(text, problems)
    n = Normalizer(ast)
    model = n.run()
    for holder, rel, ref in n._dangling:
        problems.append(f"unresolved {rel} reference {ref!r} in {holder}")
    for mid, node in model.meta.items():
        if node.kind == "inference":
            problems.append(f"{mid} is an inference, not an established requirement")
    return model, problems


def _tolerant_ast(text: str, problems: list[str]) -> A.Experience:
    """Try strict; on failure drop offending declarations and retry."""
    try:
        return parse_strict(text)
    except Exception as exc:
        problems.append(f"strict parse failed: {str(exc).splitlines()[0]}")
    for attempt in _degrade(text):
        try:
            ast = parse_strict(attempt)
            problems.append(f"recovered after dropping {len(attempt.splitlines()) and 'some'} declarations")
            return ast
        except Exception:
            continue
    problems.append("recovery failed: returning an empty model")
    return A.Experience(name="Recovered")


def _degrade(text: str):
    """Progressively strip the declarations that do not parse."""
    blocks = _split_top_level(text)
    for drop in range(1, len(blocks)):
        yield "".join(b for i, b in enumerate(blocks) if i != drop)
    yield _header(text)


def _split_top_level(text: str) -> list[str]:
    out, buf, depth, i = [], [], 0, 0
    while i < len(text):
        ch = text[i]
        buf.append(ch)
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                out.append("".join(buf))
                buf = []
        i += 1
    if buf:
        out.append("".join(buf))
    return out


def _header(text: str) -> str:
    m = re.search(r"experience\s+\w+\s*\{", text)
    return (m.group(0) if m else "experience Empty {") + "}"
