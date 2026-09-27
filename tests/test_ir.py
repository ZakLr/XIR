"""Parsing, normalization and stable-identity tests (§30)."""
from pathlib import Path
import pytest
import xir.ir as I
from xir.parser.parse import ParseError, parse_text, recover_text
from xir.ir import ids as Ids

ROOT = Path(__file__).parent.parent
EX = ROOT / "examples"
PM = EX / "project-manager" / "app.xir"


# ---------- strict parsing (§21) ----------
def test_all_examples_parse_strictly():
    for f in sorted(EX.glob("*/app.xir")):
        assert I.load_file(f) is not None


def test_invalid_xir_raises_not_degrades():
    with pytest.raises(ParseError):
        parse_text("experience X { entity { broken")


def test_parse_error_reports_location():
    with pytest.raises(ParseError) as e:
        parse_text("experience X {\n  entity E { a: Text\n}\n")
    assert "line" in str(e.value).lower()


def test_recover_is_explicit_and_reports_problems():
    text = "experience X { entity E { a: Text } surface S { states: loading error } flow F { step: S } }"
    model, problems = recover_text(text)
    assert model is not None
    assert isinstance(problems, list)


# ---------- legacy compatibility (§31) ----------
def test_legacy_flat_surface_still_parses():
    m = I.load_text("""experience Legacy {
      entity E { id: ID }
      surface S {
        presents: E[]
        components { Sidebar Main }
        states: loading empty populated error
      }
      flow F { actor: u  S -> F }
    }""") if hasattr(I, "load_text") else I.load("""experience Legacy {
      entity E { id: ID }
      surface S {
        presents: E[]
        components { Sidebar Main }
        states: loading empty populated error
      }
      flow F { actor: u  S -> F }
    }""")
    assert "surface.s" in m.surfaces
    assert m.surfaces["surface.s"].components
    assert m.surfaces["surface.s"].states


def test_legacy_effects_upgrade_to_structured_mutation():
    m = I.load("""experience L {
      entity P { status: Text }
      capability archiveP { input { p: P }  effects: p.status = archived }
      surface S { presents: P[]  states: loading error }
      flow F { step: S }
    }""")
    cap = next(iter(m.capabilities.values()))
    assert cap.mutates == ["field.p.status"]


# ---------- stable identity (§4) ----------
def test_ids_are_canonical_and_typed():
    m = I.load_file(PM)
    assert m.id == "exp.projectManager"
    assert "capability.archiveProject" in m.capabilities
    assert "permission.project.archive" in m.permissions
    assert "field.project.status" in m.fields


def test_camel_preserves_dotted_names():
    assert Ids.camel("project.archive") == "project.archive"
    assert Ids.camel("ProjectDetail") == "projectDetail"
    assert Ids.make_id("permission", "project.archive") == "permission.project.archive"


def test_invalid_id_is_rejected():
    assert not Ids.valid_id("not-an-id")
    assert Ids.valid_id("capability.project.archive")


def test_resolve_by_name_and_id():
    m = I.load_file(PM)
    assert m.resolve("archiveProject") == "capability.archiveProject"
    assert m.resolve("capability.archiveProject") == "capability.archiveProject"
    assert m.resolve("nope") is None


# ---------- ontology primitives (§5-§11) ----------
def test_goals_permissions_actors_events_present():
    m = I.load_file(PM)
    assert m.goals and m.permissions and m.actors and m.events
    assert m.actors["actor.manager"].permissions == [
        "permission.project.read", "permission.project.create", "permission.project.archive"]


def test_capability_declares_typed_relations():
    m = I.load_file(PM)
    c = m.capabilities["capability.archiveProject"]
    assert c.requires == ["permission.project.archive"]
    assert c.mutates == ["field.project.status"]
    assert c.emits == ["event.projectArchived"]
    assert c.confirmation and c.audit


def test_component_is_first_class():
    m = I.load_file(PM)
    b = m.components["component.projectDetail.archiveButton"]
    assert b.presents == "entity.project"
    assert b.invokes == ["capability.archiveProject"]


def test_interaction_bridges_ui_to_capability():
    m = I.load_file(PM)
    i = m.interactions["interaction.archiveProject"]
    assert i.trigger == "click"
    assert i.target == "component.projectDetail.archiveButton"
    assert i.invokes == "capability.archiveProject"


def test_state_machine_has_initial_and_transitions():
    m = I.load_file(PM)
    mc = m.machines["machine.projectList"]
    assert mc.initial == "state.projectList.loading"
    assert len(mc.transitions) == 9  # includes the event-driven one
    t = m.transitions["transition.projectList.loading.dataReceived"]
    assert t.source == "state.projectList.loading"
    assert t.target == "state.projectList.populated"
    assert t.event == "dataReceived"


def test_rich_flow_steps_and_branches():
    m = I.load_file(PM)
    f = m.flows["flow.createProject"]
    assert f.actor == "actor.member"
    assert f.goal == "goal.createProject"
    assert f.entry == "surface.dashboard"
    step = m.steps["step.createProject.submit"]
    assert step.action == "interaction.submitProject"
    branch = m.branches["branch.createProject.validation"]
    assert ("success", "entity.project") in branch.cases


# ---------- provenance / evidence (§20) ----------
def test_evidence_carries_sources_and_confidence():
    m = I.load_file(PM)
    inf = m.meta["meta.inference.archiveLocation"]
    assert inf.kind == "inference"
    assert inf.confidence == "probable"
    assert "screenshot.dashboard" in inf.evidence
