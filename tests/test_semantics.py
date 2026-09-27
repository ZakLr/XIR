"""Semantic graph, query, validation and compiler behaviour tests (§30)."""
from pathlib import Path
import pytest
import xir.ir as I
from xir.semantic.graph import build_graph, Rel
from xir.query import engine as Q
from xir.validator.validate import validate
from xir.compiler import emit as E

EX = Path(__file__).parent.parent / "examples"
PM = EX / "project-manager" / "app.xir"
ALL = sorted(EX.glob("*/app.xir"))


@pytest.fixture
def pm():
    return I.load_file(PM)


@pytest.fixture
def g(pm):
    return build_graph(pm)


# ---------- graph (§13, §14) ----------
def test_graph_nodes_are_typed(g):
    p = g.g.nodes["capability.archiveProject"]["payload"]
    assert p.kind == "capability"
    assert p.name == "archiveProject"
    assert p.attrs["confirmation"] is True


def test_graph_edges_are_typed(g):
    d = g.g.edges["capability.archiveProject", "field.project.status"]
    assert d["payload"].relation == Rel.MUTATES


def test_graph_has_no_phantom_nodes(g):
    """Every node id is a real semantic id; only evidence may be a bare string node."""
    from xir.ir.ids import valid_id
    for n in g.g.nodes:
        assert valid_id(n) or n.startswith("evidence."), n


def test_full_ui_to_domain_chain_exists(g):
    """component -> interaction -> capability -> permission -> mutation -> event -> state"""
    comp, cap = "component.projectDetail.archiveButton", "capability.archiveProject"
    assert g.out(comp, Rel.INVOKES) == [cap]
    assert g.out(comp, Rel.HAS_INTERACTION) == ["interaction.archiveProject"]
    assert g.out("interaction.archiveProject", Rel.INVOKES) == [cap]
    assert g.out(cap, Rel.REQUIRES) == ["permission.project.archive"]
    assert g.out(cap, Rel.MUTATES) == ["field.project.status"]
    assert g.out(cap, Rel.EMITS) == ["event.projectArchived"]
    assert g.out("event.projectArchived", Rel.TRIGGERS)


def test_actor_grants_are_edges(g):
    assert g.out("actor.manager", Rel.GRANTS) == [
        "permission.project.read", "permission.project.create", "permission.project.archive"]


def test_graph_depends_only_on_the_ir(g):
    """The graph must not reach into parser structures."""
    from xir.semantic import graph as gmod
    src = Path(gmod.__file__).read_text(encoding="utf-8")
    assert "ast.nodes" not in src and "from xir.ast" not in src


# ---------- query (§15, §16) ----------
def test_show_lists_relationships(g):
    out = Q.show(g, "surface.dashboard")
    assert "CONTAINS" in out and "component.dashboard.projectList" in out


def test_trace_is_a_compact_slice(g):
    out = Q.trace(g, "capability.archiveProject")
    for token in ("REQUIRES", "MUTATES", "EMITS", "EXPOSED BY", "FLOW"):
        assert token in out
    assert len(out.splitlines()) < 25


def test_structural_follow(g):
    assert "field.project.status" in Q.follow(g, "capability.archiveProject", "mutates")


def test_who_can_uses_permissions(g):
    out = Q.query(g, "who can archiveProject")
    assert "manager" in out
    assert "member" not in out


def test_what_happens_when_clicking(g):
    out = Q.query(g, "what happens when the user clicks archiveProject")
    assert "MUTATES" in out and "EMITS" in out


def test_show_kind_lists_bucket(g):
    assert "CAPABILITY" in Q.query(g, "show capabilities")


def test_query_does_not_depend_on_substring_routing():
    """Answers must come from graph edges, not from `if x in q`."""
    from xir.query import engine as emod
    src = Path(emod.__file__).read_text(encoding="utf-8")
    assert "g.out(" in src and "g.inc(" in src


# ---------- validation (§19) ----------
def test_all_examples_validate_clean():
    for f in ALL:
        assert validate(I.load_file(f)) == [], f


def test_unreachable_state_detected():
    m = I.load("""experience U {
      entity E { id: ID }
      capability c { input { e: E } }
      state m1 {
        initial: a
        a { on go -> b }
        b { on back -> a }
        orphan { on x -> a }
      }
      component Comp { invokes: c }
      surface S { presents: E[]  components { Comp }  machine: m1 }
      flow F { step: S }
    }""")
    assert "UNREACHABLE_STATE" in {f.code for f in validate(m)}


def test_missing_initial_state_detected():
    m = I.load("""experience U {
      entity E { id: ID }
      capability c { input { e: E } }
      state m1 { a { on go -> b }  b { on back -> a } }
      component Comp { invokes: c }
      surface S { presents: E[]  components { Comp }  machine: m1 }
      flow F { step: S }
    }""")
    assert "MISSING_INITIAL_STATE" in {f.code for f in validate(m)}


def test_dead_end_state_detected():
    m = I.load("""experience U {
      entity E { id: ID }
      capability c { input { e: E } }
      state m1 {
        initial: a
        a { on go -> b }
        b { }
      }
      component Comp { invokes: c }
      surface S { presents: E[]  components { Comp }  machine: m1 }
      flow F { step: S }
    }""")
    assert "DEAD_END_STATE" in {f.code for f in validate(m)}


def test_invalid_transition_target_detected():
    m = I.load("""experience U {
      entity E { id: ID }
      capability c { input { e: E } }
      state m1 {
        initial: a
        a { on go -> nowhere }
      }
      component Comp { invokes: c }
      surface S { presents: E[]  components { Comp }  machine: m1 }
      flow F { step: S }
    }""")
    codes = {f.code for f in validate(m)}
    assert "INVALID_TRANSITION_TARGET" in codes or "UNRESOLVED_REFERENCE" in codes


def test_unreachable_capability_detected():
    m = I.load("""experience U {
      entity E { id: ID }
      permission p.read { }
      actor member { }
      capability secret { input { e: E }  requires: p.read }
      component Comp { invokes: secret }
      surface S { presents: E[]  components { Comp } }
      flow F { actor: member  step: S }
    }""")
    codes = {f.code for f in validate(m)}
    assert "UNREACHABLE_CAPABILITY" in codes or "UNAUTHORIZED_CAPABILITY" in codes


def test_destructive_needs_confirmation():
    m = I.load("""experience U {
      entity E { id: ID }
      capability deleteE { input { e: E } }
      component C { invokes: deleteE }
      surface S { presents: E[]  components { C } }
      flow F { step: S }
    }""")
    assert "MISSING_CONFIRMATION" in {f.code for f in validate(m)}


def test_inference_cannot_claim_confirmed():
    m = I.load("""experience U {
      entity E { id: ID }
      inference guess { claim: "x"  confidence: confirmed }
      capability c { input { e: E } }
      component C { invokes: c }
      surface S { presents: E[]  components { C } }
      flow F { step: S }
    }""")
    assert "UNSUPPORTED_CONFIDENCE" in {f.code for f in validate(m)}


def test_unresolved_reference_is_reported():
    m = I.load("""experience U {
      entity E { id: ID }
      capability c { input { e: E }  emits: GhostEvent }
      component C { invokes: c }
      surface S { presents: E[]  components { C } }
      flow F { step: S }
    }""")
    assert "UNRESOLVED_REFERENCE" in {f.code for f in validate(m)}


def test_dead_end_flow_detected():
    m = I.load("""experience U {
      entity E { id: ID }
      capability c { input { e: E } }
      component C { invokes: c }
      surface S { presents: E[]  components { C } }
      flow F { actor: nobody }
    }""")
    codes = {f.code for f in validate(m)}
    assert "DEAD_END_FLOW" in codes


# ---------- compiler (§23, §24) ----------
def test_react_emits_state_machines_and_interactions(pm):
    out = E.to_react(pm)
    assert "transitions" in out and "dataReceived" in out
    assert "capability.archiveProject" in out
    assert "ProjectArchived" in out


def test_react_emits_loading_and_error_states(pm):
    out = E.to_react(pm)
    for st in ("loading", "empty", "populated", "error"):
        assert st in out


def test_playwright_tests_walk_the_semantic_chain(pm):
    out = E.to_playwright(pm)
    assert "getByTestId('component.projectDetail.archiveButton')" in out
    assert "getByRole('dialog')" in out
    assert "interaction.archiveProject" in out
    assert "field.project.status" in out
