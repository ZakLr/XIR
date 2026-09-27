# Semantic graph (v0.3)

Built by `src/xir/semantic/graph.py` **from the semantic IR only**. It must never
import the syntax AST — `tests/test_semantics.py` asserts this.

## Node

```python
Node(id="capability.archiveProject", kind="capability", name="archiveProject",
     attrs={"confirmation": True, "audit": True})
```

`kind` is one of the ID prefixes in `spec/ontology.md`, plus `experience` and
`evidence`.

## Edge

```python
Edge(source="capability.archiveProject", relation="mutates",
     target="field.project.status")
```

Every edge carries a relation from `ir.model.Rel`. Edges are added only where the IR
asserts a relationship — never because two names co-occur in a declaration.

## Relations

| Relation | From → To | Meaning |
|---|---|---|
| `has` | experience → anything declared at top level | ownership |
| `achieved-by` / `achieves` | goal ↔ flow | goal/flow pairing |
| `grants` | actor → permission | authorization |
| `requires` | capability → permission | precondition |
| `consumes` | capability → entity | reads |
| `produces` | capability → entity | returns |
| `mutates` | capability → field | changes domain state |
| `emits` | capability → event | produces an event |
| `causes` | capability → transition | the capability drives this transition |
| `triggers` | event → transition | the event fires this transition |
| `contains` | surface → component, machine → state, flow → step | composition |
| `presents` | surface/component → entity | what is shown |
| `invokes` | component/interaction/step → capability | what runs |
| `has-state` | surface/component → machine | state ownership |
| `has-interaction` | component → interaction | UI affordance |
| `transitions-to` | state → transition | outgoing edge |
| `starts-at` | flow → surface | entry point |
| `leads-to` | step/branch → surface/state/entity | navigation |
| `branched-from` | branch → surface/state | branch origin |
| `stepped-as` | actor → flow | who performs the flow |
| `governed-by` | invariant → node | rule scope |
| `evidenced-by` | meta → invariant/evidence | provenance |

## Normalization

1. Parser produces the syntax AST (`ast/nodes.py`) — literally what was written.
2. `semantic/normalize.py` walks it in dependency order and emits the IR:
   meta → permissions → actors → goals → entities → events → capabilities → machines →
   components → interactions → surfaces → flows → invariants.
   A pass may only reference what an earlier pass created.
3. Legacy forms are upgraded here: flat `components {}` becomes components, a bare
   `states: a b c` becomes a machine with no transitions, `A -> B` becomes an explicit
   step, and `effects: x.y = z` becomes a `mutates` field id.

## Invariants the graph holds

- No phantom nodes: every node id is a valid semantic id (`evidence.*` excepted).
- Every edge endpoint exists in the graph.
- Traversal is by relation, not by string matching: `g.out(id, Rel.MUTATES)`.
