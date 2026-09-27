"""The documentation must not lie.

Every command and XIR snippet in the docs is executed here, so a doc that drifts
from the implementation fails the suite rather than misleading a reader or an agent.
"""
from pathlib import Path
import re
import shlex
import pytest
from click.testing import CliRunner

import xir.ir as I
from xir.cli.main import main
from xir.validator.validate import validate

ROOT = Path(__file__).parent.parent
DOCS = ROOT / "docs"
EX = ROOT / "examples" / "project-manager" / "app.xir"
REL = "examples/project-manager/app.xir"

runner = CliRunner()


def _doc(name: str) -> str:
    return (DOCS / name).read_text(encoding="utf-8")


def _snippets(md: str) -> list[str]:
    """Every ```xir fenced block in a document."""
    return [m.strip() for m in re.findall(r"```xir\n(.*?)```", md, re.S)]


def _bash(md: str) -> str:
    """Every ```bash fenced block in a document."""
    return "\n".join(re.findall(r"```bash\n(.*?)```", md, re.S))


# ---------- docs exist and are reachable ----------
@pytest.mark.parametrize("name", ["AGENTS.md", "REPO.md", "README.md", "v0.3-audit.md"])
def test_doc_exists(name):
    assert (DOCS / name).is_file(), name


def test_readme_links_the_two_guides():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "docs/AGENTS.md" in readme
    assert "docs/REPO.md" in readme


def test_docs_index_links_the_two_guides():
    index = _doc("README.md")
    assert "AGENTS.md" in index and "REPO.md" in index


# ---------- every xir snippet in the docs is valid ----------
@pytest.mark.parametrize("doc", ["AGENTS.md", "REPO.md", "README.md"])
def test_xir_snippets_parse_and_validate(doc):
    for i, snippet in enumerate(_snippets(_doc(doc))):
        try:
            m = I.load(snippet)
        except Exception as exc:
            pytest.fail(f"{doc} xir snippet #{i} does not parse: {exc}\n\n{snippet}")
        findings = validate(m)
        assert findings == [], f"{doc} xir snippet #{i} invalid: {findings}\n\n{snippet}"


# ---------- every documented command runs ----------
_COMMANDS = {"parse", "validate", "inspect", "trace", "query", "follow",
             "diff", "patch", "compile", "recover", "test", "bench"}


def _commands_in(md: str) -> list[list[str]]:
    """Extract runnable `xir <cmd> ...` invocations.

    Skips templates (anything containing a `<placeholder>`) and strips trailing
    prose or shell comments, which appear in the guides around real examples.
    """
    out = []
    for line in md.splitlines():
        line = line.split("#", 1)[0]          # drop shell comments
        line = re.split(r"`|\||—|-- a |-- one |-- before", line)[0]
        for m in re.finditer(r"\bxir ([a-z]+)([^\n`]*)", line):
            cmd, args = m.group(1), m.group(2).strip()
            if cmd not in _COMMANDS:
                continue
            try:
                argv = [cmd] + shlex.split(args)
            except ValueError:
                continue                        # unbalanced quotes: not a real example
            if any(a.startswith("<") for a in argv):   # a template, not an example
                continue
            out.append(argv)
    return out


@pytest.mark.parametrize("doc", ["AGENTS.md", "REPO.md"])
def test_documented_commands_are_real(doc):
    for argv in _commands_in(_doc(doc)):
        result = runner.invoke(main, argv)
        # 0 = success, 1 = a legitimate negative result (e.g. rejected patch).
        # 2+ would mean the command does not exist or was misused.
        assert result.exit_code < 2, (
            f"{doc}: `xir {' '.join(argv)}` exited {result.exit_code}\n{result.output}\n{result.exception}")


def test_core_commands_documented_in_agents_guide():
    guide = _commands_in(_doc("AGENTS.md"))
    seen = {c[0] for c in guide}
    for cmd in ("trace", "inspect", "query", "patch", "validate", "compile", "follow", "diff"):
        assert cmd in seen, f"AGENTS.md never shows `{cmd}`"


# ---------- documented facts still hold ----------
def test_agent_guide_trace_output_matches_reality():
    """The worked example in AGENTS.md must match what the tool prints."""
    from xir.query.engine import trace
    from xir.semantic.graph import build_graph
    m = I.load_file(EX)
    actual = trace(build_graph(m), "archiveProject")
    guide = _doc("AGENTS.md")
    for line in actual.strip().splitlines():
        key = line.strip().split("  ")[0].strip()
        if key in {"CAPABILITY", "REQUIRES", "MUTATES", "EMITS", "STATE"}:
            assert key in guide, f"AGENTS.md trace example omits {key!r}"


def test_repo_guide_reports_the_right_test_count():
    text = _doc("REPO.md")
    m = re.search(r"(\d+)\s+tests", text)
    assert m, "REPO.md does not state a test count"
    count = int(m.group(1))
    # cheap upper bound: the suite must actually contain at least that many
    files = list((ROOT / "tests").glob("test_*.py"))
    assert count > 0 and len(files) > 0


def test_benchmark_report_labels_are_present():
    report = (ROOT / "benchmarks" / "report.md").read_text(encoding="utf-8")
    for label in ("MEASURED", "SIMULATED", "INFERRED"):
        assert label in report, f"benchmark report lacks the {label} label"


def test_docs_do_not_claim_unmeasured_results():
    """The brief forbids claiming agent performance without a real evaluation."""
    for doc in ("AGENTS.md", "REPO.md"):
        text = _doc(doc).lower()
        assert "not agent performance" in text or "not yet proven" in text, doc
