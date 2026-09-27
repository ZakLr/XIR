"""Golden tests: every projection must match its checked-in expectation."""
import glob
from pathlib import Path
import pytest
import xir.ir as I
from xir.compiler import emit as E
from xir.compiler.dsl import to_xir
from xir.diff.diff import diff

ALL = sorted(glob.glob("examples/*/app.xir"))
PROJECTORS = [("html", E.to_html), ("react", E.to_react), ("a2ui", E.to_a2ui),
              ("docs", E.to_docs), ("a11y", E.to_a11y), ("playwright", E.to_playwright)]


def test_examples_exist():
    assert len(ALL) >= 5, ALL


@pytest.mark.parametrize("path", ALL, ids=lambda p: Path(p).parent.name)
def test_projections_match_goldens(path):
    m = I.load_file(path)
    base = str(Path(path).parent)
    for ext, fn in PROJECTORS:
        expected = Path(f"{base}/expected.{ext}").read_text(encoding="utf-8")
        assert fn(m) == expected, f"{path} -> {ext}"


@pytest.mark.parametrize("path", ALL, ids=lambda p: Path(p).parent.name)
def test_canonical_xir_golden_round_trips(path):
    m = I.load_file(path)
    canon = Path(str(Path(path).parent / "expected.xir")).read_text(encoding="utf-8")
    assert diff(m, I.load(canon)) == "no semantic changes"
    assert to_xir(m) == canon
