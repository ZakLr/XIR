# Landscape

Interactive products today described via disconnected artifacts: source code (React/Vue/SwiftUI/Flutter),
markup (HTML/CSS/ARIA), design files (Figma), API schemas (OpenAPI/GraphQL/JSON Schema), docs prose,
screenshots, analytics. Agents retrieve these as flat context: large, ambiguous, lossy.

Modeling traditions (UML/SysML/BPMN/ArchiMate, statecharts) capture structure/behavior formally but are
heavyweight, rarely kept in sync with implementation, weak on UI presentation and agent retrieval.
Declarative UI (Adaptive Cards, A2UI, OpenUI, Web Components) standardizes rendering, not product
intent/goals/permissions/provenance. Agent protocols (MCP, AG-UI, A2A, tool calling/structured outputs)
standardize capability invocation, not the semantic product model behind them.
Knowledge representation (RDF/OWL/JSON-LD, property graphs) offers graph semantics but no UX ontology.

Gap: no compact IR linking intent → domain → capabilities → surfaces → state → flows → mappings,
queryable at multiple resolutions with stable IDs, patches, diffs, validation, provenance.
XIR targets that layer and compiles to the rest instead of competing with them.
