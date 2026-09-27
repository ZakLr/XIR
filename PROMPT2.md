# XIR v0.3 — Make the Semantic Model Agent-Native

You are working on the XIR repository:

`https://github.com/ZakLr/XIR`

XIR is intended to be a **semantic intermediate representation for interactive products**: agents should be able to understand, query, modify, validate, and compile an application from XIR without having to reconstruct product semantics from source code, screenshots, and prose.

The current implementation is a strong skeleton, but the next step is **not adding lots of features**.

The priority is to make the semantic model substantially richer and then prove that agents actually benefit from it.

---

# 1. Core objective

Evolve XIR from:

> "A structured description of an application"

into:

> "A queryable semantic model of an interactive product."

The semantic model should explicitly represent:

* product goals
* actors
* domain entities
* capabilities
* permissions
* surfaces
* components
* UI interactions
* states
* state transitions
* events
* flows
* relationships between all of the above
* provenance/evidence
* stable semantic identity

The key principle:

**If an agent needs to infer an important product relationship from a string, XIR should eventually represent that relationship explicitly.**

---

# 2. Do NOT blindly rewrite the project

First inspect the existing repository and preserve useful existing architecture.

In particular, understand and reuse:

* `src/xir/ast/`
* `src/xir/parser/`
* `src/xir/semantic/`
* `src/xir/query/`
* `src/xir/patch/`
* `src/xir/compiler/`
* `spec/`
* `benchmarks/`
* `examples/`
* existing tests

Do not introduce unnecessary frameworks or rewrite everything.

The goal is an evolutionary upgrade from v0.2 → v0.3.

Before modifying code:

1. Run the current test suite.
2. Run the existing benchmark suite.
3. Inspect the current AST.
4. Inspect graph construction.
5. Inspect query behavior.
6. Inspect patch behavior.
7. Identify exactly where the current architecture prevents richer semantics.

Document your findings briefly before implementation.

---

# 3. Separate syntax AST from semantic IR

This is one of the most important architectural changes.

Currently the AST is effectively serving as both:

1. what the XIR file literally says
2. what those declarations mean semantically

Separate these concepts.

## Syntax AST

Represents what the parser found.

Example:

```python
CapabilityDecl(
    name="archiveProject",
    ...
)
```

## Semantic IR

Represents the normalized meaning:

```python
Capability(
    id="capability.project.archive",
    name="archiveProject",
    consumes=["entity.project"],
    requires=["permission.project.archive"],
    mutations=["entity.project.status"],
    emits=["event.project.archived"],
)
```

The semantic IR should be the source of truth for:

* graph construction
* validation
* queries
* tracing
* patches
* compilation
* benchmarks

The parser should produce syntax AST → normalization should produce semantic IR → graph should be built from semantic IR.

Do not make the graph directly dependent on parser-specific structures.

---

# 4. Add stable semantic identity

Currently identity is largely derived from names.

This is fragile because renaming:

```text
archiveProject
```

can effectively become a new semantic node.

Introduce explicit stable IDs.

Example:

```text
id: capability.project.archive
name: archiveProject
```

Similarly:

```text
entity.project
entity.task

surface.dashboard
surface.projectDetail

component.projectList
component.archiveAction

flow.projectCreation
flow.projectArchiving

event.project.archived

permission.project.archive
```

Names are display/syntax-level identifiers.

IDs represent semantic identity.

A rename should therefore produce:

```text
same ID
new name
```

rather than:

```text
remove old node
add new node
```

Update diff/patch/query behavior accordingly.

---

# 5. Expand the ontology

The existing primitives are:

* Experience
* Entity
* Capability
* Surface
* State
* Flow

Keep those.

Add the following first-class concepts.

---

## 5.1 Goal

A Goal represents an outcome the user/product is trying to achieve.

Example:

```xir
goal createProject {
    description: "Create a new project."
    actor: member
}
```

Goals should be linkable to:

* capabilities
* flows
* surfaces

Graph relationships:

```text
goal -> achieved-by -> flow
goal -> enabled-by -> capability
goal -> exposed-by -> surface
```

---

# 6. Make Capability semantic instead of just descriptive

Capabilities should become one of the strongest primitives in XIR.

A capability should be able to explicitly declare:

```text
input
output
requires
consumes
produces
mutates
emits
confirmation
audit
```

For example:

```xir
capability archiveProject {
    id: capability.project.archive

    input {
        project: Project
    }

    output: Project

    requires: permission.project.archive

    consumes: Project

    mutates {
        Project.status
    }

    emits: ProjectArchived

    confirmation: required
    audit: required
}
```

Do not require agents to infer relationships such as:

> archiveProject changes Project.status

from arbitrary strings.

Represent them explicitly.

---

# 7. Add Permission as a first-class primitive

Currently permissions are effectively strings.

Introduce:

```xir
permission project.archive {
    description: "Archive a project."
}
```

Then:

```xir
capability archiveProject {
    requires: permission.project.archive
}
```

Actors should be connectable to permissions.

Example:

```xir
actor member {
    permissions {
        project.read
        project.create
    }
}

actor manager {
    permissions {
        project.read
        project.create
        project.archive
    }
}
```

Validation should be able to detect:

* capability requiring nonexistent permission
* actor invoking capability without permission
* unreachable capability
* unauthorized interaction

---

# 8. Make Component a first-class semantic concept

This is critical.

Currently components are mostly:

```text
components { Sidebar Main Header ProjectList }
```

That is too shallow.

Introduce a real `Component` semantic object.

Example:

```xir
component ArchiveButton {
    id: component.project.archiveButton

    presents: Project

    invokes: archiveProject

    states {
        enabled
        disabled
        loading
        error
    }
}
```

Components should be able to:

* contain other components
* present entities
* invoke capabilities
* trigger interactions
* have states
* participate in flows

Graph relationships:

```text
surface -> contains -> component
component -> contains -> component
component -> presents -> entity
component -> invokes -> capability
component -> has-state -> state
component -> participates-in -> interaction
```

---

# 9. Add Interaction

Interactions represent explicit UI/user actions.

Example:

```xir
interaction archiveProject {
    trigger: click
    target: component.project.archiveButton
    invokes: capability.project.archive
}
```

This creates an explicit bridge between:

```text
UI
↓
interaction
↓
capability
↓
domain mutation
```

This is extremely important for agent reasoning.

An agent should be able to ask:

> What happens when the user clicks Archive?

and get a structured answer rather than searching component strings.

---

# 10. Make State a real state machine

This is probably the most important semantic upgrade.

Do not represent state as only:

```text
states {
    loading
    empty
    populated
    error
}
```

Represent transitions explicitly.

Example:

```xir
state ProjectList {
    initial: loading

    loading {
        on dataReceived -> populated
        on emptyReceived -> empty
        on failure -> error
    }

    empty {
        on createProject -> creating
    }

    populated {
        on archiveProject.success -> populated
        on refresh -> refreshing
    }

    refreshing {
        on success -> populated
        on failure -> error
    }

    error {
        on retry -> loading
    }
}
```

Represent:

* state IDs
* initial state
* transitions
* transition event
* source state
* destination state
* optional guard
* optional action/effect

Graph:

```text
state.loading
    --dataReceived-->
state.populated
```

This should enable validation of:

* unreachable states
* dead-end states
* invalid transitions
* missing initial state
* impossible transitions
* references to nonexistent events
* inconsistent capability/state relationships

---

# 11. Add Event

Events should be first-class.

Example:

```xir
event ProjectCreated
event ProjectArchived
event ProjectUpdated
```

Capabilities can emit events:

```xir
capability archiveProject {
    emits: event.project.archived
}
```

State machines can consume events:

```xir
state ProjectList {
    populated {
        on event.project.archived -> populated
    }
}
```

Graph:

```text
capability.archiveProject
    -> emits
event.project.archived

event.project.archived
    -> triggers
transition.ProjectList.populated
```

This allows XIR to model behavior instead of just structure.

---

# 12. Make Flow substantially richer

Current flows are basically:

```text
A -> B -> C
```

This loses too much information.

Introduce explicit flow steps.

Example:

```xir
flow CreateProject {
    id: flow.project.creation

    goal: goal.createProject

    actor: member

    entry {
        surface: surface.dashboard
    }

    step openForm {
        from: surface.dashboard
        action: interaction.createProject
        to: surface.createProject
    }

    step submit {
        from: surface.createProject
        action: interaction.submitProject
        to: state.projectCreation.validating
    }

    branch validation {
        from: state.projectCreation.validating

        success -> entity.project
        invalid -> state.projectCreation.invalid
        networkError -> state.projectCreation.error
    }
}
```

Flow steps should explicitly represent:

* source
* action
* destination
* capability/interaction
* conditions
* branches
* errors
* success paths

Do not reduce these to strings.

---

# 13. Build a genuinely typed semantic graph

Continue using NetworkX if it is useful.

But make the graph represent semantic relationships explicitly.

Target shape:

```text
Goal
  ↓
Flow
  ├── starts-at → Surface
  ├── invokes → Interaction
  ├── invokes → Capability
  ├── transitions → State
  └── achieves → Goal

Surface
  ├── contains → Component
  └── has-state → State

Component
  ├── contains → Component
  ├── presents → Entity
  ├── invokes → Capability
  └── has-interaction → Interaction

Interaction
  ├── triggered-by → Event/UI trigger
  ├── attached-to → Component
  └── invokes → Capability

Capability
  ├── requires → Permission
  ├── consumes → Entity
  ├── produces → Entity
  ├── mutates → Entity field
  ├── emits → Event
  └── causes → StateTransition

Event
  └── triggers → StateTransition

StateMachine
  └── contains → State

State
  └── transitions-to → State
```

Every edge should have a meaningful semantic type.

Avoid creating relationships simply because two names appear in the same declaration.

---

# 14. Improve graph node representation

A semantic node should contain structured information such as:

```python
Node(
    id="capability.project.archive",
    kind="capability",
    name="archiveProject",
    attrs={
        ...
    }
)
```

Edges should be typed:

```python
Edge(
    source="capability.project.archive",
    relation="requires",
    target="permission.project.archive"
)
```

Prefer typed models over arbitrary dictionaries wherever practical.

The graph should become a reliable intermediate representation, not merely a visualization of the AST.

---

# 15. Replace keyword query routing with semantic queries

The current query engine uses string matching such as:

```python
if "capability" in query:
```

That is acceptable as a temporary convenience layer, but it should not be the core query system.

Introduce structured semantic queries.

For example:

```text
trace capability.project.archive
```

should return:

```text
CAPABILITY
archiveProject

REQUIRES
permission.project.archive

CONSUMES
entity.project

MUTATES
entity.project.status

EMITS
event.project.archived

EXPOSED BY
component.project.archiveButton
surface.projectDetail

FLOWS
flow.project.archiving

STATES
projectDetail.populated
projectDetail.refreshing
```

Also support queries such as:

```text
show capability.project.archive
show surface.dashboard
show component.project.archiveButton
show flow.project.creation
show entity.project
show state.projectList
show event.project.archived
```

And structural traversals:

```text
from capability.project.archive
follow emits
follow requires
follow exposed-by
follow flows
```

The query engine should operate on semantic graph relationships, not text matching.

---

# 16. Improve `inspect`

`inspect` should become a high-value agent operation.

For example:

```text
xir inspect capability.project.archive
```

should return enough structured context for an agent to understand:

* what it does
* inputs
* outputs
* permissions
* affected entities
* mutations
* events
* UI entry points
* surfaces
* flows
* relevant states
* invariants
* provenance

The result should be compact and token-efficient.

The point is not to dump the entire application.

The point is to provide exactly the semantic slice an agent needs.

---

# 17. Improve semantic patches

Current patches directly mutate AST/dataclass fields.

This can create inconsistencies.

Move toward an atomic semantic transaction model:

```text
PATCH
  ↓
resolve semantic IDs
  ↓
apply changes
  ↓
rebuild affected semantic graph
  ↓
validate
  ↓
compile
  ↓
test
  ↓
commit OR rollback
```

A patch should never leave the model in a partially invalid state.

Example:

```text
rename capability.project.archive -> capability.project.archiveProject
```

should update all references atomically.

Example:

```text
remove capability.project.archive
```

should detect:

* interactions referring to it
* flows referring to it
* state transitions referring to it
* permissions
* compiler references

before committing.

---

# 18. Make diff semantic

Current diffing is primarily identity/add/remove based.

Upgrade it so that:

```text
rename
```

is distinguishable from:

```text
remove + add
```

And semantic changes are explicit.

Example:

```text
CHANGED capability.project.archive

requires:
    permission.project.archive
    → permission.project.manage

mutates:
    entity.project.status

emits:
    event.project.archived
```

Also support:

```text
ADDED interaction.project.archiveButton
REMOVED state.projectList.refreshing
CHANGED flow.project.archive
RENAMED component.oldName → component.newName
```

---

# 19. Improve validation

Extend validation to use the richer graph.

At minimum validate:

## Identity

* duplicate IDs
* invalid IDs
* dangling references

## Capabilities

* invalid input/output references
* nonexistent permissions
* invalid mutations
* invalid events

## Components

* nonexistent capability
* nonexistent entity
* invalid child component
* invalid interaction

## Interactions

* invalid target component
* nonexistent capability
* unauthorized capability

## State machines

* missing initial state
* unreachable state
* dead-end state
* nonexistent transition target
* nonexistent event
* invalid capability/event relationship

## Flows

* invalid actor
* invalid surface
* invalid interaction
* invalid capability
* broken branch
* unreachable step
* dead-end flow

## Security

Detect:

```text
actor -> interaction -> capability -> permission
```

where the actor lacks the required permission.

---

# 20. Provenance should become evidence, not just metadata

Current provenance is useful but too shallow.

Support structured evidence.

Example:

```xir
inference archiveProjectLocation {
    claim: "Archive action belongs in the project overflow menu."

    evidence {
        source: screenshot.dashboard
        source: analytics.archiveUsage
        source: design.decision.D14
    }

    confidence: probable
}
```

A semantic fact should ideally be traceable to:

* human requirement
* design document
* source code
* API
* test
* analytics
* screenshot
* inference
* agent proposal

This will eventually make XIR useful as a reverse-engineering representation as well as an authoring representation.

---

# 21. Keep strict parsing strict

Current parsing falls back to a tolerant regex parser whenever strict parsing fails.

Do not silently turn malformed XIR into a partially parsed model.

Instead:

```text
xir parse
```

should be strict by default.

If parsing fails:

```text
ERROR: invalid XIR
```

Provide an explicit recovery operation:

```text
xir recover
```

or equivalent.

Recovery mode may produce best-effort semantics, but it must clearly indicate uncertainty.

This prevents invalid source from silently becoming a plausible but incorrect semantic model.

---

# 22. Do NOT prioritize incremental parsing yet

Do not spend significant time implementing Tree-sitter or sophisticated incremental parsing right now.

The semantic model is currently the bigger bottleneck.

First make:

```text
syntax → semantic IR → graph → query → patch → validation
```

excellent.

Optimize parsing performance only after benchmarks show parsing is actually a bottleneck.

---

# 23. Improve the compiler strategically

Do not implement ten additional compiler targets.

Instead, make one target genuinely useful.

Prioritize:

```text
XIR → React
```

with real behavior.

The generated React application should eventually have:

* components
* state
* interactions
* capability calls
* transitions
* loading/error/empty states
* basic accessibility
* Playwright tests

HTML/docs/A2UI can remain useful projections, but React should become the first serious runtime target.

---

# 24. Make Playwright tests semantic

Instead of generating shallow text describing tests, use the semantic graph.

For example, from:

```text
interaction.archiveProject
    → capability.archiveProject
```

generate a test that conceptually verifies:

```text
open project
→ locate archive interaction
→ trigger interaction
→ confirmation appears
→ confirm
→ ProjectArchived occurs
→ Project.status becomes archived
→ UI enters correct state
```

This is one of the strongest ways to prove that the semantic model contains enough information to generate behaviorally meaningful artifacts.

---

# 25. Redesign the benchmark

This is extremely important.

The existing benchmark is useful as a smoke test, but it is currently a proxy based heavily on string presence and simulated retrieval.

Do not present it as proof that XIR improves agents.

Build a real agent-oriented benchmark.

Compare representations of the SAME application:

```text
A. prose
B. JSON
C. source code
D. XIR
```

Optionally:

```text
E. XIR + source
```

Give an agent identical tasks.

Examples:

### Retrieval

> Where is project archiving implemented?

### Reasoning

> What permission is required to archive a project?

### UI reasoning

> Which UI interaction invokes archiveProject?

### State reasoning

> What happens after archiveProject succeeds?

### Modification

> Add a confirmation step before archiveProject executes.

### Modification

> Add an error state when project archiving fails.

### Modification

> Make archiveProject unavailable to members.

### Cross-cutting modification

> Rename the archive capability and update all references.

### Regression

> Change the project status model and identify every affected flow/component/state.

Measure:

* task success
* semantic correctness
* state correctness
* flow correctness
* UI correctness
* regression count
* input tokens
* output tokens
* number of retrieval/tool calls
* wall-clock time
* validation failures
* repair attempts

Do not use only keyword/string matching.

---

# 26. Make benchmark tasks adversarial

The benchmark should specifically test situations where semantics matter.

Examples:

```text
The archive button is on a different surface than the archive capability.

Find the actual relationship.
```

```text
A capability mutates an entity and emits an event.

What UI state changes as a consequence?
```

```text
An actor can see a component but lacks the permission required by the capability.

Is the interaction valid?
```

```text
A state exists but is unreachable.

Identify it.
```

```text
Rename a capability while preserving semantic identity.
```

These tasks test whether XIR actually captures meaning rather than merely exposing strings.

---

# 27. Add benchmark provenance

Every benchmark result should clearly distinguish:

```text
MEASURED
```

from:

```text
SIMULATED
```

from:

```text
INFERRED
```

Never claim:

> XIR uses 36% fewer tokens than source code

unless this has been measured under a reproducible agent evaluation.

It is okay to say:

> In the current synthetic proxy benchmark, XIR used 0.64× the JSON character budget.

But make clear that this is not equivalent to real-world agent performance.

---

# 28. Create a canonical example that exercises the ontology

Update `examples/project-manager`.

It should demonstrate:

* Goal
* Actor
* Permission
* Entity
* Capability
* Event
* Component
* Interaction
* Surface
* State machine
* Flow
* provenance

Example conceptually:

```text
Goal
  Create Project

Actor
  Member

Surface
  Dashboard
      ↓
Component
  CreateProjectButton
      ↓
Interaction
  click
      ↓
Capability
  createProject
      ↓
Entity
  Project
      ↓
Event
  ProjectCreated
      ↓
State Transition
  creating → populated
```

This example should become the canonical reference implementation for XIR semantics.

---

29. Update the specifications

Update:

spec/ontology.md
spec/semantics.md
spec/queries.md
spec/patches.md
spec/validation.md

so they describe the actual implementation.

Do not allow the docs and implementation to drift.

Add a new:

spec/semantic-graph.md

documenting:

node types
edge types
identity
normalization
traversal semantics
invariants

Also update the README once the implementation stabilizes.

30. Add tests before declaring v0.3 complete

Add unit tests for:

Parsing
goals
permissions
components
interactions
events
state machines
richer flows
Semantic normalization
stable IDs
references
relationships
Graph
typed nodes
typed edges
traversal
Query
inspect
trace
structural queries
Patch
rename
modify
add/remove
reference updates
rollback
Validation
invalid references
unreachable states
permission violations
invalid transitions
Compiler
semantic state
interactions
basic React behavior
Round-trip
XIR
→ parse
→ semantic IR
→ graph
→ serialize
→ parse

should preserve semantic meaning.

31. Preserve backward compatibility where reasonable

Existing simple XIR should continue to work where possible.

For example:

surface Dashboard {
    components {
        Sidebar
        Main
    }
}

can still be accepted.

Internally it may normalize to:

surface.dashboard
    contains component.sidebar
    contains component.main

This lets XIR evolve without forcing every existing example to become maximally verbose.

32. Avoid premature complexity

Do NOT implement all of the following unless there is a concrete benchmark-driven reason:

distributed semantic graphs
databases
LLM-specific embeddings
vector search
autonomous agents
complex optimization passes
Tree-sitter incremental parsing
dozens of compiler targets
UUID-heavy identity systems
a huge query language

The core product is the semantic model.

Make this excellent first.

33. Definition of done

XIR v0.3 should satisfy the following:

Semantic model

An agent can answer:

What happens when the user clicks Archive?

by traversing:

Component
→ Interaction
→ Capability
→ Permission
→ Entity mutation
→ Event
→ State transition

without relying on string matching.

State model

A state machine is explicit and machine-traversable.

Flow model

Flows have explicit actions, transitions, and branches.

Identity

Renaming a thing does not destroy its semantic identity.

Queries

An agent can request a compact semantic slice of the product.

Patches

Changes are atomic and validated.

Validation

The system catches semantic inconsistencies.

Compiler

At least one generated target meaningfully reflects the richer semantics.

Benchmark

There is at least one real agent evaluation showing how XIR compares against alternative representations.

34. Suggested implementation order

Implement in this order:

Phase 1 — Foundation
Stable semantic IDs
Syntax AST → semantic IR separation
Component primitive
Permission primitive
Event primitive
Interaction primitive
Phase 2 — Behavior
Real state machines
Rich flow steps
Typed semantic graph
Explicit graph relationships
Phase 3 — Agent interface
Semantic inspect
Structural queries
Capability tracing
Semantic diff
Atomic graph-aware patches
Phase 4 — Correctness
Rich validation
Provenance/evidence
Round-trip tests
Phase 5 — Compilation
Improve React compiler
Generate meaningful Playwright tests
Phase 6 — Proof
Build real agent benchmark
Compare XIR/prose/JSON/source
Measure success, tokens, retrievals, correctness, regressions
Document results honestly
35. Final product philosophy

Throughout the implementation, keep this principle in mind:

XIR should not be another format for writing down what an application looks like.

It should be:

A compact, typed, queryable semantic model of what an interactive product means and how it behaves.

The killer capability is not:

"Describe my UI."

It is:

"Give an agent the exact semantic slice it needs to understand, modify,
validate, test, and compile this part of the product."

Optimize the system around that.

Do not optimize for maximum syntax.

Optimize for:

semantic fidelity + queryability + correctness + agent usefulness + compactness.

Before adding any new feature, ask:

Does this make the semantic model more expressive, more queryable, more verifiable, or more useful to an agent?

If not, defer it.