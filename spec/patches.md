# Patches

Ops: add/remove/replace/modify/move/rename/deprecate (Sec 10). Implemented in
`src/xir/patch/patch.py` v0.1: add/remove/rename for capabilities; others return no-op ok.
`diff` in `src/xir/diff/diff.py`: identity-based add/remove per kind
(entity/capability/surface/flow); "no semantic changes" = stable.
Agent workflow (Sec 40): query → identify → check invariants → propose patch → validate →
apply → compile → test → provenance → diff.
