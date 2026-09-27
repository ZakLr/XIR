# Related systems (10-point notes, condensed)

## UML / SysML / BPMN / ArchiMate / Statecharts
1. Problem: formal software/systems/process modeling. 2. Level: design-time diagrams.
3. Strengths: standardized semantics, statecharts executable. 4. Weaknesses: heavy authoring,
drift from code, poor UI/agent story. 5. Format: XMI/diagrams. 6. Agent relevance: low direct;
good ideas for states/flows. 7. Overlap: states, flows, actors. 8. Differ: XIR executable-adjacent,
UI-projecting, retrieval-oriented. 9. Integrate: borrow statechart semantics. 10. Avoid duplicating: full UML.

## HTML / CSS / ARIA / Web Components
1. Rendering documents/components. 2. Browser runtime. 3/4. Universal but presentational, verbose,
a11y bolted on. 5. Markup. 6. Agents read DOM but drown in divs. 7/8. Overlap: surfaces/components;
differ: semantics-first vs pixels. 9. Integrate: HTML is a compiler target. 10. Avoid: recreating CSS.

## JSON Schema / OpenAPI / AsyncAPI / GraphQL / Protobuf
1. Data/API contracts. 2. Interface level. 3/4. Precise validation, no UX/flow/provenance.
5. Schema IDLs. 6. Good for tool args. 7/8. Overlap: entities/inputs; differ: no surfaces/flows.
9. Integrate: import/export schemas. 10. Avoid: new IDL.

## Adaptive Cards / A2UI / AG-UI / OpenUI
1. Portable UI cards/agent UI. 2. Render level. 3/4. Standard renderers, but no product intent,
permissions, flows. 5. JSON. 6. Direct agent-UI relevance. 7/8. Overlap: surfaces; differ: XIR sits above.
9. Integrate: A2UI/AG-UI as targets. 10. Avoid: competing card format.

## MCP / A2A / tool calling / structured outputs
1. Agent capability invocation. 2. Protocol level. 3/4. Interop, but no product model.
5. JSON-RPC/schemas. 6. Core agent relevance. 7/8. Overlap: capabilities→tools; differ: model vs wire.
9. Integrate: capability→MCP tool mapping. 10. Avoid: new protocol.

## Figma / Code Connect / design tokens (W3C DTCG)
1. Visual design systems. 2. Design level. 3/4. High fidelity, weak semantics/behavior.
5. Proprietary + tokens JSON. 6. Agents struggle with pixels. 7/8. Overlap: design system/tokens;
differ: semantic references. 9. Integrate: tokens + component mappings. 10. Avoid: canvas clone.

## ASTs / IRs / tree-sitter / language servers
1. Language tooling. 2. Compiler level. 3/4. Incremental parsing, diffing; generic, no UX ontology.
5. Trees/graphs. 6. Direct inspiration for pipeline. 7/8. Overlap: pipeline shape; differ: domain.
9. Integrate: tree-sitter/LSP patterns. 10. Avoid: generic code IR.

## RDF / OWL / JSON-LD / property graphs / ontologies
1. Knowledge representation. 2. Graph level. 3/4. Rich relations/reasoning, verbose, no UX primitives.
5. Triples/JSON-LD. 6. Good for queries/provenance. 7/8. Overlap: graph/queries; differ: product ontology.
9. Integrate: export JSON-LD. 10. Avoid: full ontology stack.
