"""Extended validator tests (Sec 47)."""
from xir.parser.parse import parse_text
from xir.validator.validate import validate

def test_destructive_needs_confirmation():
    exp = parse_text('experience X { capability deleteUser { input { x: Text } } surface S { states: loading error } flow F { actor: a } }')
    assert any("destructive" in e or "confirmation" in e for e in validate(exp))

def test_missing_required_states():
    exp = parse_text('experience X { surface S { states: populated } flow F { step: S } }')
    assert any("missing required states" in e for e in validate(exp))

def test_broken_actor():
    exp = parse_text('experience X { actors { admin } surface S { states: loading error } flow F { actor: ghost step: S } }')
    assert any("actor" in e for e in validate(exp))

def test_duplicate_ids():
    exp = parse_text('experience X { entity E { a: Text } entity E { b: Text } surface S { states: loading error } flow F { step: S } }')
    assert any("duplicate ID" in e for e in validate(exp))

def test_dead_end_flow():
    exp = parse_text('experience X { surface S { states: loading error } flow F { actor: a } }')
    assert any("dead-end" in e for e in validate(exp))
