"""Patch op tests."""
import pytest
from xir.parser.parse import parse_file
from xir.patch.patch import apply_patch, apply_patch_text
from xir.validator.validate import validate
from pathlib import Path

EX = Path(__file__).parent.parent / "examples" / "project-manager" / "app.xir"

def test_full_ops():
    exp = parse_file(EX)
    assert apply_patch(exp, "add", "surface", "Help", {"states": ["loading", "error"]}).startswith("added")
    assert apply_patch(exp, "modify", "surface", "Help", {"presents": "Project[]"}).startswith("modified")
    assert apply_patch(exp, "rename", "surface", "Help", {"to": "Support"}).startswith("renamed")
    assert apply_patch(exp, "deprecate", "surface", "Support").startswith("deprecated")
    assert apply_patch(exp, "move", "surface", "Support", {"to": 0}).startswith("moved")
    assert apply_patch(exp, "replace", "surface", "Support", {"states": ["loading", "error"]}).startswith("replaced")
    assert apply_patch(exp, "remove", "surface", "Support").startswith("removed")
    assert validate(exp) == []

def test_patch_text():
    exp = parse_file(EX)
    out = apply_patch_text(exp, "patch {\n add surface.Help\n states: loading error\n}")
    assert out == ["added surface.Help"]
    with pytest.raises(ValueError):
        apply_patch(exp, "remove", "surface", "Nope")
