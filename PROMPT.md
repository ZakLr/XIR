# Build: A Semantic Interactive Experience Language for Humans and AI Agents

## 0. Mission

You are the lead researcher, language designer, systems architect, and implementation engineer for a new open-source project.

The project is an experimental language and intermediate representation for describing **interactive software as a semantic system**.

The goal is NOT to create another HTML-like markup language, another CSS language, another JSON UI format, or merely another UML variant.

The goal is to create a **machine-readable, agent-optimized semantic representation of an interactive product** that captures:

* product intent
* user goals
* actors
* domain concepts
* entities
* capabilities
* actions
* data
* UI surfaces
* components
* semantic layout
* interaction
* state
* transitions
* user flows
* navigation
* permissions
* constraints
* invariants
* requirements
* design systems
* design decisions
* implementation mappings
* provenance
* assumptions
* uncertainty
* relationships between all of the above

The representation should allow an AI agent to understand, create, modify, validate, query, test, document, and implement an interactive product with significantly less ambiguity and context than relying on source code, screenshots, design files, prose, and disconnected documentation.

The central thesis is:

> An interactive product should have a semantic intermediate representation, analogous to an IR in a compiler, from which UI, code, tests, documentation, agent tools, workflows, and other representations can be derived.

Think of this as a **Product Experience IR** or **Semantic Interactive Experience Language**.

Do not assume the final name is decided.

---

# 1. Core Principles

The project MUST be designed around these principles.

## 1.1 Semantics before presentation

The system should describe what something means before describing how it looks.

For example, prefer:

```text
capability archiveProject
```

over:

```text
button "Archive"
```

and:

```text
action archiveProject
```

over:

```text
onClick(() => ...)
```

A button is one possible representation of a capability.

---

## 1.2 UI is a projection of semantics

The semantic model is the source of truth.

UI is one projection.

Other projections include:

* React
* Vue
* Svelte
* SwiftUI
* Flutter
* A2UI
* Figma
* HTML
* documentation
* tests
* accessibility metadata
* analytics
* agent tools
* API mappings

The system should make these relationships explicit.

---

## 1.3 Framework independence

The core representation MUST NOT depend on:

* React
* Vue
* Angular
* Svelte
* Flutter
* SwiftUI
* Tailwind
* CSS
* Figma
* a specific LLM
* OpenAI
* Anthropic
* Google
* Microsoft

Framework-specific details belong in mappings, adapters, or compiler targets.

---

## 1.4 Agent-first design

The language is specifically intended to improve AI-agent performance.

Optimize for:

* semantic density
* retrieval
* reasoning
* selective context loading
* incremental modification
* deterministic structure
* validation
* diffing
* provenance
* low ambiguity
* low token consumption
* composability

Do NOT optimize only for human readability.

Human readability matters, but semantic precision matters more.

---

## 1.5 Human-friendly authoring

The primary source language should be concise and pleasant for humans to read and write.

Do NOT use raw JSON as the primary authoring syntax.

JSON, MessagePack, CBOR, protobuf, etc. may be used as interchange or serialization formats.

Example desired style:

```text
experience ProjectManager

goal "Help teams manage projects"

actor User

entity Project {
    id: ID
    name: Text
    status: draft | active | archived
}

capability createProject {
    input:
        name: Text

    output:
        Project

    failure:
        validation
        permission
}
```

This is illustrative only. Improve it if research suggests a better design.

---

# 2. Important Existing Technologies to Study

Before implementing the language, conduct serious research into related systems.

At minimum study:

## Modeling

* UML
* SysML
* BPMN
* ArchiMate
* state machines
* finite-state machines
* statecharts

## UI / declarative UI

* HTML
* CSS
* ARIA
* JSON Schema
* Adaptive Cards
* Google's A2UI
* OpenUI
* Web Components

## Agent systems

* MCP
* AG-UI
* A2UI
* agent-to-agent protocols
* structured outputs
* function/tool calling

## Design

* Figma
* Figma MCP
* Figma Code Connect
* design tokens
* W3C Design Tokens Community Group specifications
* component systems

## APIs and data

* OpenAPI
* AsyncAPI
* GraphQL schemas
* JSON Schema
* Protocol Buffers

## Programming language / compiler design

* ASTs
* IRs
* compiler pipelines
* language servers
* tree-sitter
* incremental parsing
* semantic diffing

## Knowledge representation

* RDF
* OWL
* JSON-LD
* property graphs
* knowledge graphs
* ontologies

## Agent context optimization

Study how current coding/design agents retrieve context.

Pay particular attention to:

* context windows
* retrieval granularity
* hierarchical representations
* semantic compression
* structured output
* tool calls
* incremental patches

Do not copy existing systems.

Identify what they solve and what they do not solve.

---

# 3. Research Deliverable

Before committing to the architecture, create:

```text
research/
    landscape.md
    competitors.md
    related-systems.md
    design-principles.md
    open-problems.md
    differentiation.md
```

For each related technology document:

1. What problem it solves.
2. Its abstraction level.
3. Its strengths.
4. Its weaknesses.
5. Its representation format.
6. Its agent relevance.
7. How our proposed language overlaps with it.
8. How our proposed language differs.
9. Whether we should integrate with it.
10. Whether we should explicitly avoid duplicating it.

Do not make unsupported claims.

When internet access is available, use primary sources wherever possible.

---

# 4. The Central Abstraction

The central abstraction should be an **interactive experience**, not a screen.

A conceptual hierarchy should look approximately like:

```text
Experience
│
├── Intent
│   ├── Goals
│   ├── Principles
│   └── Requirements
│
├── Actors
│
├── Domain
│   ├── Entities
│   ├── Attributes
│   ├── Relationships
│   └── Events
│
├── Capabilities
│   ├── Inputs
│   ├── Outputs
│   ├── Preconditions
│   ├── Effects
│   ├── Failures
│   └── Permissions
│
├── Surfaces
│   ├── Regions
│   ├── Components
│   ├── Layout
│   ├── Presentation
│   └── Accessibility
│
├── State
│   ├── State variables
│   ├── States
│   └── Transitions
│
├── Flows
│   ├── Goals
│   ├── Actors
│   ├── Steps
│   ├── Branches
│   └── Outcomes
│
├── Constraints
│
├── Invariants
│
├── Design System
│
├── Decisions
│
├── Assumptions
│
├── Provenance
│
└── Mappings
    ├── UI
    ├── API
    ├── Code
    ├── Tools
    └── Tests
```

This is a starting hypothesis, not an unquestionable specification.

Challenge it.

---

# 5. Core Ontology

Create a formal ontology.

Start by investigating these concepts:

```text
Experience
Goal
Intent
Actor
Role
Entity
Attribute
Relationship
Capability
Action
Event
Data
Surface
Region
Component
Pattern
Interaction
State
Transition
Flow
Precondition
Postcondition
Constraint
Invariant
Requirement
Permission
DesignToken
DesignSystem
Decision
Assumption
Evidence
Provenance
Mapping
Implementation
```

For every primitive document:

* definition
* purpose
* required fields
* optional fields
* relationships
* inheritance/composition rules
* defaults
* validation rules
* examples
* anti-examples
* whether it belongs in core or extension

Do not create primitives merely because they sound useful.

Every primitive must justify its existence.

---

# 6. Minimal Core

Try to identify the smallest useful core.

The first candidate core is:

```text
Concept
Capability
Surface
State
Flow
```

But do not assume this is correct.

Determine the smallest set required to express real applications.

The language should remain small enough that an LLM can learn and reason over it without spending enormous context navigating the schema.

---

# 7. Semantic Defaults

Use semantic defaults aggressively.

For example:

```text
Button
```

should imply a known set of semantics.

Do not require the representation to repeat obvious information.

Avoid verbose structures such as:

```text
{
    "type": "button",
    "interactive": true,
    "focusable": true,
    "role": "button"
}
```

if the ontology already defines these properties.

The objective is:

> maximum semantic information per token.

Do NOT use arbitrary abbreviations like:

```text
btn.prm.act
```

Token efficiency should come from ontology and semantics, not cryptic syntax.

---

# 8. Multi-Resolution Context

This is a fundamental requirement.

The complete model may be huge.

Agents should NOT need to load the entire model for every task.

Design hierarchical context levels.

For example:

```text
L0 Product summary

L1 Experience/domain

L2 Capability/flow

L3 Surface

L4 Component

L5 State

L6 Implementation
```

Design a query mechanism allowing agents to request only what they need.

Examples:

```text
query flow "CreateProject"
```

```text
query surface Dashboard
include:
    layout
    interactions
    states
```

```text
query capability archiveProject
include:
    callers
    permissions
    effects
```

```text
query component ProjectCard
include:
    semantic
    states
    mapping
```

The system should support context slicing.

---

# 9. Stable IDs

Every semantic object should have a stable identity.

Example:

```text
surface.dashboard
component.dashboard.projectList
capability.project.create
flow.project.creation
state.projectList.loading
```

IDs should survive formatting changes.

Agents should be able to refer to objects without rewriting the entire document.

---

# 10. Patches and Incremental Modification

Design an explicit patch system.

Example:

```text
patch {

    modify surface.dashboard {

        component ProjectList {
            state: virtualized
        }
    }
}
```

Or:

```text
patch {

    replace:
        surface.CreateProject.presentation
            from page
            to modal
}
```

The agent should be able to modify small portions of a product model.

Do not require regeneration of the entire document.

Support:

* add
* remove
* replace
* modify
* move
* rename
* deprecate

---

# 11. Semantic Diff

Build a semantic diff system.

A textual diff:

```text
+ Button
- Button
```

is insufficient.

A semantic diff should be able to say:

```text
Added capability:
    archiveProject

Changed surface:
    Dashboard

Changed interaction:
    CreateProject

Changed flow:
    CreateProjectFlow

Changed invariant:
    destructive actions require confirmation
```

The diff should operate on semantic identity rather than raw text.

---

# 12. State Modeling

State is a first-class concept.

Support:

```text
loading
empty
populated
refreshing
error
success
disabled
unauthorized
offline
partial
```

But allow arbitrary domain-specific states.

Example:

```text
ProjectList {

    states:
        loading
        empty
        populated
        error

    transitions:

        initial -> loading

        loading --dataReceived--> populated

        loading --empty--> empty

        loading --failure--> error

        populated --refresh--> refreshing

        refreshing --success--> populated
    }
}
```

Study statecharts and state-machine theory before implementing this.

The representation should eventually support validation such as:

* unreachable states
* impossible transitions
* missing transitions
* dead ends
* inconsistent conditions

---

# 13. User Flow Modeling

Flows are not simply navigation.

A flow represents a user goal.

Example:

```text
flow CreateProject {

    actor User

    goal:
        "Create a new project"

    precondition:
        authenticated

    Dashboard
        -> CreateProject
        -> validating

    validating {
        success -> Project
        validation -> CreateProject.error
        permission -> CreateProject.error
        network -> CreateProject.retry
    }

    outcome:
        Project.created
}
```

Support:

* goals
* actors
* entry points
* steps
* branches
* conditions
* alternative paths
* errors
* retries
* cancellation
* completion
* side effects

---

# 14. Capabilities

Capabilities are more important than UI controls.

Example:

```text
capability archiveProject {

    input:
        project: Project

    requires:
        permission(project.archive)

    effects:
        project.status = archived

    confirmation:
        required

    audit:
        required
}
```

A capability may be represented by:

* button
* menu item
* keyboard shortcut
* command palette
* voice interaction
* mobile gesture
* agent tool
* API
* automation

This distinction is essential.

---

# 15. UI Representation

UI should be semantic.

Prefer:

```text
surface Project {

    presents Project

    layout {

        Header {
            title: project.name

            actions:
                editProject
                archiveProject
        }

        Content {
            ProjectOverview
            TaskList
        }
    }
}
```

rather than encoding every pixel.

The language should support:

* hierarchy
* regions
* semantic components
* layout relationships
* responsive constraints
* component variants
* interaction
* accessibility

---

# 16. Layout Model

Do not recreate CSS.

The language should describe layout relationships and constraints.

Examples:

```text
stack vertical
row
grid
split
sidebar
content
overlay
modal
drawer
```

And constraints:

```text
sidebar collapses < 768

primaryAction remains visible

title may truncate

content must remain readable

actions remain reachable
```

Absolute coordinates should be an escape hatch, not the fundamental representation.

---

# 17. Design Systems

Design systems must be first-class.

Example:

```text
designSystem Acme {

    tokens {
        spacing.sm
        spacing.md
        spacing.lg

        radius.sm
        radius.md

        typography.body
        typography.heading
    }

    components {
        Button
        Card
        Modal
        Input
        Table
    }
}
```

The product model should reference design-system primitives rather than rediscovering them.

---

# 18. Component Mapping

Support mappings between semantic components and implementation components.

Example:

```text
mapping {

    ProjectCard
        -> react.ProjectCard

    Button
        -> react.Button

    Modal
        -> react.Modal
}
```

Likewise support:

```text
semantic component
    -> Figma component

semantic component
    -> A2UI component

semantic capability
    -> MCP tool

semantic entity
    -> API resource
```

---

# 19. Accessibility

Accessibility must not be an afterthought.

The semantic model should allow renderers to derive accessibility behavior.

Study:

* ARIA
* semantic HTML
* keyboard interaction
* focus management
* accessible names
* state announcements
* relationships

Prefer semantic definitions over repeated low-level implementation metadata.

---

# 20. Invariants

Make product invariants first-class.

Examples:

```text
invariant {
    destructive actions require confirmation
}
```

```text
invariant {
    unauthenticated users cannot access Dashboard
}
```

```text
invariant {
    archived projects cannot receive tasks
}
```

```text
invariant {
    every form has validation and error states
}
```

These should eventually be machine-checkable.

---

# 21. Requirements vs Observations vs Inferences

This distinction is mandatory.

The system must distinguish:

```text
requirement
observation
decision
assumption
inference
proposal
implementation
```

For example:

```text
requirement:
    "Users must confirm destructive actions."
```

versus:

```text
observation:
    "The current implementation uses a confirmation dialog."
```

versus:

```text
inference:
    "Archive probably belongs in an overflow menu."
```

Do not allow inferred information to silently become authoritative product requirements.

---

# 22. Provenance

Support provenance.

Possible sources:

```text
human
requirement-document
code
design
API
test
analytics
inference
agent
```

Example:

```text
capability archiveProject {

    provenance {
        source: code
        reference: ProjectService.archive
        confidence: confirmed
    }
}
```

For inferred information:

```text
provenance {
    source: inference
    confidence: tentative
}
```

This is important for preventing agent hallucinations.

---

# 23. Design Rationale

Support decisions.

Example:

```text
decision D14 {

    subject:
        navigation

    selected:
        sidebar

    rationale:
        "Users frequently switch between projects."

    alternatives:
        topNavigation
        commandPalette

    status:
        accepted
}
```

Agents should be able to understand WHY something exists, not merely WHAT exists.

---

# 24. Uncertainty

Support uncertainty explicitly.

Possible states:

```text
confirmed
probable
inferred
tentative
proposed
deprecated
unknown
```

Never force the model to pretend uncertainty does not exist.

---

# 25. Security and Permissions

Capabilities should support:

```text
permission
role
authorization
confirmation
audit
sensitivity
```

Example:

```text
capability deleteUser {

    requires:
        role.admin

    confirmation:
        required

    audit:
        required
}
```

The representation itself should be safe to expose to agents.

Do not make executable arbitrary code part of the semantic DSL.

---

# 26. Queries

Design a query language or API.

Agents should be able to ask:

```text
What can a guest user do?
```

```text
Which surfaces expose archiveProject?
```

```text
What happens when checkout fails?
```

```text
Show all paths to Checkout.
```

```text
Which capabilities mutate Order?
```

```text
Which states does ProjectList have?
```

```text
What changed between version 1 and version 2?
```

The query layer may eventually become as important as the syntax.

---

# 27. Agent Operations

Define canonical agent operations:

```text
inspect
query
create
modify
delete
diff
validate
explain
trace
compile
render
test
```

Example:

```text
inspect surface Dashboard
```

```text
trace capability archiveProject
```

```text
validate flow CreateProject
```

```text
explain decision D14
```

---

# 28. Compilation Architecture

Design the system like a compiler.

Conceptually:

```text
Source DSL
    ↓
Lexer / Parser
    ↓
AST
    ↓
Semantic Graph / IR
    ↓
Validation
    ↓
Optimization / Normalization
    ↓
Target Compiler
```

Potential targets:

```text
React
HTML
SwiftUI
Flutter
A2UI
Figma
documentation
Playwright
accessibility tests
agent tools
```

The semantic graph should be the central representation.

---

# 29. Canonical AST vs Graph

Investigate both.

Do not assume the AST is sufficient.

A tree is useful for:

* syntax
* parsing
* formatting

A graph may be necessary for:

* relationships
* references
* capabilities
* flows
* provenance
* mappings
* cross-surface relationships

Likely architecture:

```text
DSL
 ↓
AST
 ↓
Canonical Semantic Graph
```

Research and validate this assumption.

---

# 30. Interoperability

The project should integrate with existing standards rather than replace them.

Investigate adapters for:

```text
OpenAPI
JSON Schema
MCP
A2UI
AG-UI
Figma
ARIA
design tokens
React
HTML
```

For example:

```text
semantic capability
        ↓
       MCP
```

```text
semantic UI
        ↓
       A2UI
```

```text
semantic API mapping
        ↓
     OpenAPI
```

---

# 31. Token Efficiency

Treat token efficiency as a research problem.

Do not merely count characters.

Measure:

```text
semantic information / token
```

Compare:

1. natural-language specification
2. JSON representation
3. source code
4. screenshot + text
5. existing UI DSL
6. proposed DSL

Test whether agents can perform tasks with fewer tokens and fewer context retrievals.

---

# 32. Agent Benchmark

Create a benchmark suite.

Start with at least 20 tasks.

Examples:

```text
Add project creation.

Add project deletion.

Add loading state.

Add empty state.

Add error state.

Add mobile navigation.

Add bulk actions.

Add search.

Add filtering.

Add onboarding.

Add permissions.

Add confirmation.

Modify layout.

Change navigation.

Add a new capability.

Change a flow.

Find all callers of a capability.

Explain why a component exists.

Detect an unreachable state.

Detect a missing error state.
```

Compare:

```text
baseline source code
baseline screenshots
baseline prose
proposed semantic representation
```

Measure:

```text
token usage
context size
tool calls
task completion
correctness
state coverage
flow correctness
UI fidelity
accessibility
regressions
time
```

Do not optimize for one metric only.

---

# 33. Reconstruction Benchmark

One particularly important experiment:

Take a real application.

Produce the semantic representation.

Remove access to the original implementation.

Give another agent only the semantic representation.

Ask it to reconstruct the application.

Measure:

* semantic fidelity
* behavior fidelity
* flow fidelity
* visual fidelity
* accessibility
* edge-case coverage

Then test the reverse:

```text
existing application
        ↓
semantic extraction
        ↓
semantic model
        ↓
new implementation
```

This should become one of the flagship experiments.

---

# 34. Round-Trip Stability

Test:

```text
DSL
 ↓
compiler
 ↓
implementation
 ↓
extractor
 ↓
DSL
```

The result does not need to be textually identical.

It should be **semantically stable**.

Define what semantic equivalence means.

---

# 35. Do Not Overengineer V0

V0 should NOT attempt to solve:

* perfect visual fidelity
* every CSS property
* every programming language
* complete formal verification
* automatic extraction from every framework
* every design system
* every agent protocol

The goal of V0 is to prove:

> A compact semantic representation helps agents understand and modify interactive products better than conventional context alone.

---

# 36. Suggested Repository

Create approximately:

```text
/
├── README.md
├── LICENSE
├── CONTRIBUTING.md
│
├── spec/
│   ├── ontology.md
│   ├── grammar.md
│   ├── semantics.md
│   ├── validation.md
│   ├── queries.md
│   ├── patches.md
│   ├── provenance.md
│   └── versioning.md
│
├── research/
│   ├── landscape.md
│   ├── competitors.md
│   ├── related-systems.md
│   ├── differentiation.md
│   └── benchmarks.md
│
├── examples/
│   ├── todo/
│   ├── project-manager/
│   ├── ecommerce/
│   └── dashboard/
│
├── parser/
│
├── ast/
│
├── semantic/
│
├── validator/
│
├── query/
│
├── diff/
│
├── compiler/
│   ├── html/
│   ├── react/
│   ├── a2ui/
│   └── tests/
│
├── cli/
│
└── benchmarks/
```

Adapt the structure if the chosen technology makes another organization substantially better.

---

# 37. CLI

Create a CLI eventually supporting commands like:

```bash
ixl parse app.ixl

ixl validate app.ixl

ixl query app.ixl "flow CreateProject"

ixl inspect app.ixl surface Dashboard

ixl diff old.ixl new.ixl

ixl compile app.ixl --target react

ixl compile app.ixl --target a2ui

ixl test app.ixl
```

The exact command name is not important.

The workflow is.

---

# 38. Example Product

Create a complete example around a project-management application.

It should include:

```text
authentication

dashboard

projects

project detail

tasks

task creation

task editing

task completion

project archive

search

filters

loading

empty states

errors

permissions

mobile layout

responsive behavior
```

The example should demonstrate the entire ontology.

---

# 39. Example Representation

The final project should include a readable example approximately like:

```text
experience ProjectManager {

    goal:
        "Help teams organize and execute work."

    actors {
        member
        manager
        admin
    }

    entity Project {
        id: ID
        name: Text
        status: draft | active | archived
    }

    capability createProject {

        input {
            name: Text
        }

        output:
            Project

        failure:
            validation
            permission
            network
    }

    capability archiveProject {

        input {
            project: Project
        }

        requires:
            project.archive

        confirmation:
            required

        effects:
            project.status = archived
    }

    surface Dashboard {

        presents:
            Project[]

        layout {

            Sidebar

            Main {

                Header

                ProjectList {
                    states:
                        loading
                        empty
                        populated
                        error
                }

                action CreateProject {
                    invokes:
                        createProject
                }
            }
        }
    }

    flow CreateProject {

        actor:
            member

        Dashboard
            -> CreateProject
            -> validating

        validating {
            success -> Project
            validation -> CreateProject.error
            network -> CreateProject.retry
        }
    }
}
```

Again, treat this as inspiration, not fixed syntax.

---

# 40. Agent Behavior

When an agent is asked to implement a product feature, it should ideally follow:

```text
1. Understand task.
2. Query semantic model.
3. Identify affected concepts.
4. Identify affected capabilities.
5. Identify affected surfaces.
6. Identify affected flows.
7. Identify affected states.
8. Check invariants.
9. Propose semantic patch.
10. Validate patch.
11. Apply patch.
12. Compile implementation.
13. Run tests.
14. Update provenance.
15. Produce semantic diff.
```

This should become a reference workflow.

---

# 41. Critical Design Question

Investigate whether the language should distinguish:

```text
semantic component
```

from:

```text
visual component
```

For example:

```text
Collection<Project>
```

may render as:

```text
Table
List
Grid
Cards
```

depending on:

* device
* density
* design system
* user preference
* context

This distinction could be extremely important.

---

# 42. Responsive Design

Responsive behavior should be semantic.

Instead of:

```text
@media ...
```

represent:

```text
when width < 768:
    Sidebar -> Drawer

when width < 480:
    ProjectTable -> ProjectList

when width < 480:
    secondaryActions -> overflow
```

The compiler can translate these into implementation-specific behavior.

---

# 43. Agent-Specific Features

Explore features that ordinary UI languages do not need.

Potential examples:

```text
context priority

retrieval hints

semantic summaries

confidence

provenance

agent-readable explanations

stable IDs

incremental patches

queryable relationships

task-specific projections
```

However, do not blindly add "AI features."

Every feature must have a measurable benefit.

---

# 44. Avoid Prompt-Specific Semantics

Do not encode concepts that only make sense for a particular LLM.

Avoid things like:

```text
prompt this component strongly
```

or:

```text
tell the model to...
```

The language should represent the product.

The agent should derive its behavior from the semantics.

---

# 45. Versioning

Design versioning from the beginning.

Semantic models will evolve.

Support:

```text
version 1
version 2
migration
deprecation
compatibility
```

Do not allow schema evolution to become an afterthought.

---

# 46. Formal Specification

Eventually produce:

```text
spec/
    grammar.md
    semantics.md
    ontology.md
```

The grammar should define syntax.

The ontology should define concepts.

The semantics should define what those concepts mean.

These must be separate.

A parser should not be the definition of the language.

---

# 47. Validation

The validator should eventually detect:

```text
undefined references

duplicate IDs

invalid capabilities

unreachable states

dead-end flows

missing transitions

missing required states

invalid permissions

invalid mappings

circular dependencies

inconsistent domain relationships

broken references
```

Design the validator as a first-class component.

---

# 48. Explainability

Agents should be able to explain a model.

For example:

```text
explain capability archiveProject
```

could produce:

```text
archiveProject is exposed by:

Dashboard.ProjectList
Project.Header
CommandPalette

It requires:
    project.archive

It changes:
    Project.status

It affects flows:
    ArchiveProject
```

The semantic model should make these explanations straightforward.

---

# 49. Do Not Create a Giant Monolith

Keep the architecture modular.

Possible packages:

```text
core ontology
parser
semantic graph
validator
query engine
patch engine
compiler SDK
renderers
agent SDK
```

External projects should be able to consume the core without installing every compiler.

---

# 50. Open Source Strategy

Assume the project could eventually become an ecosystem.

Design extension mechanisms.

Allow:

```text
extension ecommerce
extension healthcare
extension enterprise
extension gaming
```

without changing the core ontology.

But protect the core from becoming fragmented.

---

# 51. What Success Looks Like

Success is NOT:

> "We created a cool syntax."

Success is:

> An agent given the semantic representation can perform interactive-product engineering tasks with fewer tokens, fewer mistakes, fewer context retrievals, and better behavioral fidelity than when given conventional source/design/prose context.

Everything should ultimately be tested against this claim.

---

# 52. Required Final Deliverables

By the end of the initial implementation, produce:

## Research

```text
research/landscape.md
research/competitors.md
research/related-systems.md
research/differentiation.md
```

## Specification

```text
spec/ontology.md
spec/grammar.md
spec/semantics.md
spec/validation.md
spec/queries.md
spec/patches.md
```

## Implementation

A working:

```text
parser
AST
semantic graph
validator
query engine
semantic diff
CLI
```

## Examples

At least:

```text
todo
project-manager
ecommerce
dashboard
```

## Benchmarks

A reproducible benchmark suite comparing:

```text
prose
JSON
source code
screenshots/context
proposed language
```

## Documentation

A README that explains:

1. The problem.
2. Why existing approaches are insufficient.
3. The core thesis.
4. The ontology.
5. The syntax.
6. A complete example.
7. How agents use it.
8. How it compiles.
9. Benchmark methodology.
10. Known limitations.

---

# 53. Critical Self-Criticism Requirement

Throughout the project, actively try to disprove the idea.

Do not assume the language is useful.

For every major design decision ask:

```text
Does this actually help an agent?

Could an existing standard solve this?

Does this increase semantic density?

Does this increase or decrease ambiguity?

Does this increase token efficiency?

Does this make retrieval easier?

Does this make modification safer?

Does this create unnecessary complexity?

Could this be inferred?

Should this belong in the core?

Would this still make sense without an LLM?
```

If a proposed feature is unnecessary, remove it.

If an existing standard solves the problem sufficiently, integrate with that standard instead of reinventing it.

---

# 54. Important Strategic Constraint

Do NOT build a competitor to:

```text
HTML
CSS
Figma
A2UI
MCP
AG-UI
OpenAPI
JSON Schema
UML
```

Build the semantic layer that can connect them.

The project should ideally look like:

```text
                    SEMANTIC EXPERIENCE MODEL
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
        Design              Agent              Code
          │                   │                   │
       Figma               MCP/A2UI            React
                              │                 SwiftUI
                              │                 Flutter
                              │
                             API
```

---

# 55. First Milestone

Do NOT immediately build a full compiler.

First produce:

```text
1. Research
2. Ontology v0.1
3. Grammar v0.1
4. Semantic graph v0.1
5. One complete example
6. Parser
7. Validator
8. Query engine
```

Then test the representation with an LLM.

Only after that build renderers.

---

# 56. First Experiment

Create two versions of the same product.

### Version A

Give an agent:

```text
screenshots
source code
prose requirements
```

### Version B

Give the agent:

```text
semantic model
```

Then give both agents the same modification tasks.

Measure:

```text
tokens
time
tool calls
correctness
regressions
behavioral fidelity
UI fidelity
```

If the semantic representation does not produce a measurable improvement, investigate why before expanding the language.

---

# 57. Final Architectural Hypothesis

Start from this hypothesis:

```text
Human Intent
      ↓
Semantic Experience Language
      ↓
Canonical Semantic Graph
      ↓
 ┌────┼────┬────┬────┬────┐
 ↓    ↓    ↓    ↓    ↓    ↓
 UI  Code  Flow Tests Docs Agents
```

The semantic graph is the heart of the system.

The DSL is its human-friendly representation.

The query system is how agents retrieve context.

The patch system is how agents modify products.

The compiler system is how the model becomes implementation.

The validator is how correctness is enforced.

The benchmark is how we determine whether the entire idea is actually useful.

---

# 58. Your Role

Act as:

* language designer
* compiler engineer
* AI systems researcher
* UX systems architect
* product architect
* skeptical reviewer
* benchmark designer

Do not simply execute the specification literally.

If research reveals that a different architecture is substantially better, explain the evidence and change course.

Do not optimize for producing lots of code.

Optimize for discovering whether this idea can become a genuinely useful technical standard.

When uncertain, prefer:

```text
research → experiment → measurement → decision
```

over:

```text
assumption → implementation
```

---

# 59. Start Now

Begin in this order:

### Phase 1

Research the landscape deeply.

### Phase 2

Write the ontology proposal.

### Phase 3

Challenge the ontology against at least 5 real applications.

### Phase 4

Design the minimal grammar.

### Phase 5

Design the canonical semantic graph.

### Phase 6

Implement parser + validator + query engine.

### Phase 7

Create examples.

### Phase 8

Build the first agent benchmark.

### Phase 9

Measure token efficiency and task performance.

### Phase 10

Only then design compiler targets.

At every phase, maintain:

```text
DECISIONS.md
OPEN_QUESTIONS.md
RESEARCH.md
```

Record why architectural decisions were made.

Do not hide uncertainty.

The purpose of this project is not merely to build a DSL.

The purpose is to discover and validate a **semantic intermediate representation for interactive software that is exceptionally usable by both humans and AI agents.**
