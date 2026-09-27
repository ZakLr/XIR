# Provenance

Mandatory distinction (Sec 21): requirement vs observation vs decision vs assumption vs
inference vs proposal vs implementation. Never promote inference silently.

Sources (Sec 22): human, requirement-document, code, design, API, test, analytics, inference, agent.
Confidence (Sec 24): confirmed/probable/inferred/tentative/proposed/deprecated/unknown.

v1 status: `provenance { source reference confidence }` parsed on entity/capability/surface/flow
(strict + tolerant), emitted by `to_xir()`, diffed, validated (unknown source/confidence rejected;
inference+confirmed rejected; meta inferences flagged). Decision records live in DECISIONS.md.
