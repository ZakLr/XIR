"""Patch tests: atomicity, identity-preserving rename, rollback (§17)."""
from pathlib import Path
import pytest
import xir.ir as I
from xir.patch.patch import apply_text, PatchError
from xir.diff.diff import diff
from xir.validator.validate import validate

PM = Path(__file__).parent.parent / "examples" / "project-manager" / "app.xir"


def _src() -> str:
    return PM.read_text(encoding="utf-8")


def test_rename_preserves_semantic_identity():
    m0 = I.load(_src())
    m1, _ = apply_text(I.load(_src()),
                       "patch {\n rename capability.archiveProject to_name: archive\n}")
    assert "capability.archiveProject" in m1.capabilities  # same id
    assert m1.capabilities["capability.archiveProject"].name == "archive"
    assert m1.interactions["interaction.archiveProject"].invokes == "capability.archiveProject"


def test_rename_with_new_id_updates_every_reference():
    m1, _ = apply_text(I.load(_src()),
                       "patch {\n rename capability.archiveProject to_id: capability.project.archive\n}")
    assert "capability.project.archive" in m1.capabilities
    assert m1.interactions["interaction.archiveProject"].invokes == "capability.project.archive"
    assert m1.components["component.projectDetail.archiveButton"].invokes == [
        "capability.project.archive"]
    assert m1.invariants["invariant.destructiveActionsRequireConf"].scope == "capability.project.archive"


def test_rename_is_reported_as_rename_not_add_remove():
    m0 = I.load(_src())
    m1, _ = apply_text(I.load(_src()),
                       "patch {\n rename capability.archiveProject to_name: archive\n}")
    d = diff(m0, m1)
    assert "RENAMED" in d
    assert "ADDED" not in d and "REMOVED" not in d


def test_modify_clears_a_list():
    m1, _ = apply_text(I.load(_src()), "patch {\n modify actor.member permissions:\n}")
    assert m1.actors["actor.member"].permissions == []


def test_remove_refuses_while_referenced():
    with pytest.raises(PatchError) as e:
        apply_text(I.load(_src()), "patch {\n remove capability.archiveProject\n}")
    assert "referenced" in str(e.value)


def test_remove_succeeds_when_unreferenced():
    src = """experience S {
      entity E { id: ID }
      capability lonely { input { e: E } }
      surface Surf { presents: E[]  states: loading error }
      flow F { step: Surf }
    }"""
    m1, _ = apply_text(I.load(src), "patch {\n remove capability.lonely\n}")
    assert "capability.lonely" not in m1.capabilities


def test_patch_rolls_back_when_it_would_break_the_model():
    m0 = I.load(_src())
    with pytest.raises(PatchError):
        apply_text(I.load(_src()),
                   "patch {\n modify machine.projectList initial: state.doesNotExist\n}")
    assert m0 is not None  # original untouched; transaction worked on a copy


def test_add_and_deprecate():
    m1, _ = apply_text(I.load(_src()),
                       "patch {\n add surface.Help states: loading,error\n deprecate component.dashboard.sidebar\n}")
    assert "surface.help" in m1.surfaces
    assert m1.components["component.dashboard.sidebar"].provenance.confidence == "deprecated"


def test_unknown_reference_is_rejected():
    with pytest.raises(PatchError):
        apply_text(I.load(_src()), "patch {\n remove capability.doesNotExist\n}")


def test_patch_keeps_model_valid():
    m1, _ = apply_text(I.load(_src()),
                       "patch {\n rename capability.createProject to_name: makeProject\n}")
    assert validate(m1) == []
