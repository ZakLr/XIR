"""Golden tests: emit must match checked-in expected.* files."""
import glob
from pathlib import Path
from xir.parser.parse import parse_file
from xir.compiler.emit import to_html, to_react, to_a2ui, to_docs, to_a11y, to_playwright
from xir.compiler.dsl import to_xir
from xir.parser.parse import parse_text
from xir.diff.diff import diff

def test_goldens():
    files = sorted(glob.glob("examples/*/app.xir"))
    assert len(files) >= 5, files
    for f in files:
        exp = parse_file(f)
        base = str(Path(f).parent)
        assert open(f"{base}/expected.html", encoding="utf-8").read() == to_html(exp), f
        assert open(f"{base}/expected.react", encoding="utf-8").read() == to_react(exp), f
        assert open(f"{base}/expected.a2ui", encoding="utf-8").read() == to_a2ui(exp), f
        assert open(f"{base}/expected.docs", encoding="utf-8").read() == to_docs(exp), f
        assert open(f"{base}/expected.a11y", encoding="utf-8").read() == to_a11y(exp), f
        assert open(f"{base}/expected.playwright", encoding="utf-8").read() == to_playwright(exp), f
        canon = open(f"{base}/expected.xir", encoding="utf-8").read()
        assert diff(exp, parse_text(canon)) == "no semantic changes", f
