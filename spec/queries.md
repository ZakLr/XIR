# Queries

Engine: `src/xir/query/engine.py`. L0–L3 via `semantic/graph.py:summarize`.

- `query(exp, q)`: keyword routing — capability/surface/flow/entity-domain/guest-can-do/generic.
- `inspect(exp, kind, name)`: delegates to query.
- `trace_capability(exp, name)`: surfaces exposing it + flows affected.
- Agent ops (Sec 27): inspect/query/trace/explain via CLI (`xir query`, `xir inspect`).
- Multi-resolution: L0 summary line; L1 entities; L2 capabilities; L3 surfaces. Full L4–L6 deferred.
