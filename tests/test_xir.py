"""Smoke tests for XIR v0.1."""
from pathlib import Path
from xir.parser.parse import parse_file, parse_text
from xir.validator.validate import validate
from xir.query.engine import query
from xir.diff.diff import diff
from xir.compiler.emit import to_html, to_react

EX = Path(__file__).parent.parent / "examples" / "project-manager" / "app.xir"

def test_parse_pm():
    exp = parse_file(EX)
    assert exp.name == "ProjectManager"
    assert any(c.name == "archiveProject" for c in exp.capabilities)

def test_validate_pm():
    assert validate(parse_file(EX)) == []

def test_query():
    exp = parse_file(EX)
    assert "archiveProject" in query(exp, "capability")

def test_diff():
    exp = parse_file(EX)
    assert diff(exp, exp) == "no semantic changes"

def test_compile():
    exp = parse_file(EX)
    assert "Dashboard" in to_html(exp) and "ProjectManager" in to_react(exp)

def test_undefined_ref():
    exp = parse_text('experience X { capability c { input { x: Nope } } surface S { } flow F { } }')
    assert any("undefined reference" in e for e in validate(exp))
