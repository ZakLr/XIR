"""The XIR skill must stay true to the tool.

Documentation drifts. These tests execute every command and every XIR snippet in the
skill, and run the health script, so a skill that no longer describes the real
behaviour fails the suite rather than misleading an agent that loads it.
"""
from pathlib import Path
import json
import re
import shlex
import subprocess
import sys

import pytest
from click.testing import CliRunner

import xir.ir as XIR
from xir.cli.main import main
from xir.validator.validate import validate

ROOT = Path(__file__).parent.parent
SKILL = ROOT / "skills" / "xir"
SKILL_MD = SKILL / "SKILL.md"
EX = ROOT / "examples" / "project-manager" / "app.xir"
REL = "examples/project-manager/app.xir"

runner = CliRunner()

COMMANDS = {"parse", "validate", "inspect", "trace", "query", "follow",
            "diff", "patch", "compile", "recover", "test", "bench"}


def _text(name: str) -> str:
    return (SKILL / name).read_text(encoding="utf-8")


def _plain(name: str) -> str:
    """Text with markdown emphasis removed, so assertions survive formatting."""
    return re.sub(r"[*`_>]", "", _text(name)).lower()


def _xir_snippets(md: str) -> list[str]:
    return [m.strip() for m in re.findall(r"```xir\n(.*?)```", md, re.S)]


def _commands(md: str) -> list[list[str]]:
    out = []
    for line in md.splitlines():
        line = line.split("#", 1)[0]
        line = re.split(r"`|\||—|-- ", line)[0]
        for m in re.finditer(r"\bxir ([a-z]+)([^\n`]*)", line):
            cmd, args = m.group(1), m.group(2).strip()
            if cmd not in COMMANDS:
                continue
            try:
                argv = [cmd] + shlex.split(args)
            except ValueError:
                continue
            if any(a.startswith("<") for a in argv):
                continue
            out.append(argv)
    return out


# ---------- structure ----------
def test_skill_has_required_layout():
    assert SKILL_MD.is_file()
    for rel in ("references/ontology.md", "references/cli.md", "references/patterns.md",
                "references/authoring.md", "references/troubleshooting.md",
                "scripts/xir_health.py"):
        assert (SKILL / rel).is_file(), rel


def test_frontmatter_is_valid_and_triggered():
    text = SKILL_MD.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, "SKILL.md has no YAML frontmatter"
    try:
        import yaml
        fm = yaml.safe_load(m.group(1))
    except ImportError:
        pytest.skip("pyyaml not installed")
    assert fm["name"] == "xir"
    desc = fm["description"]
    assert len(desc) > 300, "description is too thin to trigger reliably"
    for trigger in ("xir", ".xir", "semantic model", "user flow", "state machine",
                    "permission", "what happens when"):
        assert trigger.lower() in desc.lower(), f"description lacks trigger: {trigger}"


def test_readme_install_instructions_exist():
    readme = _text("README.md")
    assert "SKILL.md" in readme
    assert "xir_health.py" in readme


# ---------- the skill must not lie about the tool ----------
@pytest.mark.parametrize("doc", ["SKILL.md", "references/ontology.md",
                                 "references/cli.md", "references/patterns.md",
                                 "references/authoring.md",
                                 "references/troubleshooting.md", "README.md"])
def test_every_xir_snippet_parses_and_validates(doc):
    for i, snippet in enumerate(_xir_snippets(_text(doc))):
        # fragments that continue an earlier block are not standalone models
        if not snippet.lstrip().startswith("experience"):
            continue
        try:
            m = XIR.load(snippet)
        except Exception as exc:
            pytest.fail(f"{doc} xir snippet #{i} does not parse: {exc}\n\n{snippet}")
        findings = validate(m)
        assert findings == [], f"{doc} snippet #{i} invalid: {findings}\n\n{snippet}"


@pytest.mark.parametrize("doc", ["SKILL.md", "references/cli.md", "references/patterns.md"])
def test_every_documented_command_runs(doc):
    seen = 0
    for argv in _commands(_text(doc)):
        result = runner.invoke(main, argv)
        assert result.exit_code < 2, (
            f"{doc}: `xir {' '.join(argv)}` exited {result.exit_code}\n"
            f"{result.output}\n{result.exception}")
        seen += 1
    assert seen >= 3, f"{doc} contains too few runnable examples ({seen})"


def test_skill_teaches_traversal_not_searching():
    """The central discipline must be stated, not implied."""
    text = _plain("SKILL.md")
    assert "traversal, not a search" in text
    assert "grep" in text  # named as the anti-pattern


def test_skill_covers_the_full_arc():
    text = _plain("SKILL.md")
    for topic in ("conceive", "permission", "state machine", "provenance",
                  "roll back", "blast radius"):
        assert topic in text, f"SKILL.md never mentions {topic}"


def test_skill_forbids_overclaiming():
    """The brief forbids presenting simulated figures as agent performance."""
    for doc in ("SKILL.md", "references/cli.md", "README.md"):
        text = _plain(doc)
        assert "not agent performance" in text or "simulated" in text, doc


def test_troubleshooting_covers_every_rejection_reason():
    text = _text("references/troubleshooting.md").lower()
    for reason in ("patch rejected", "unresolved_reference", "unreachable_state",
                   "orphan_component", "still referenced", "unknown reference"):
        assert reason in text, f"troubleshooting omits: {reason}"


# ---------- the health script works ----------
def _run_health(*args) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SKILL / "scripts" / "xir_health.py"), *args],
        capture_output=True, text=True, cwd=ROOT)


def test_health_script_reports_clean_model():
    r = _run_health(str(EX))
    assert r.returncode == 0, r.stderr
    assert "findings: none" in r.stdout
    assert "round-trip: stable" in r.stdout
    assert "capabilities_typed" in r.stdout


def test_health_script_shows_coverage_gap_on_legacy_model():
    """A bare model should look under-specified even though it validates."""
    r = _run_health(str(ROOT / "examples" / "todo" / "app.xir"))
    assert r.returncode == 0, r.stderr
    assert "machines_with_transitions          0/1" in r.stdout


def test_health_script_json_mode():
    r = _run_health(str(EX), "--json")
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["valid"] is True
    assert data["round_trip_stable"] is True
    assert "coverage" in data and "provenance" in data and "cost" in data


def test_health_script_reports_unparseable_input(tmp_path):
    bad = tmp_path / "bad.xir"
    bad.write_text("experience X { entity { broken", encoding="utf-8")
    r = _run_health(str(bad))
    assert r.returncode == 2
    assert "UNPARSEABLE" in r.stdout
