# Architecture

## Current Architecture

Genome Forge is currently a local-first application with three dominant layers:

1. Sequence engine and CLI
2. HTTP API and persistence
3. Browser-based single-page UI

## Runtime Topology

```text
Browser UI
  -> web_ui.py
    -> genomeforge_toolkit.py
    -> bio/*
    -> compat/*
    -> collab/*
    -> JSON-backed local storage directories
```

## Primary Modules

## `backend/`

Responsibilities:

- extracted API-domain logic from the former `web_ui.py` monolith
- current extracted domains include record I/O and core sequence workflows, design-assist workflows, trace workflows, search/reference workflows, project/share/history workflows, cloning/assembly workflows, analysis/alignment workflows, and biology-support workflows for digest, enzyme, annotation, feature, and gel operations
- compatibility-preserving step toward route/service decomposition

Current state:

- this package is the first backend decomposition layer
- `web_ui.py` still owns the server and much of the route dispatch, but stable workflow families have started moving out

## `genomeforge_toolkit.py`

Responsibilities:

- sequence parsing
- basic GenBank and EMBL support
- translation and ORF logic
- primer design helpers
- digest simulation
- PCR simulation
- map rendering primitives
- CLI entry point

Strength:

- concentrated core logic for common sequence operations

Current limitation:

- still script-shaped rather than package-shaped

## `web_ui.py`

Responsibilities:

- local HTTP server
- API dispatch
- request parsing
- visualization responses
- workflow orchestration across helper modules

Strength:

- lightweight local server entry point with compatibility-preserving dispatch

Current limitation:

- still owns HTTP serving and top-level route delegation
- request parsing is still coupled to the local HTTP layer
- frontend serving remains coupled here while decomposition continues

## `bio/`

Focused helper modules for:

- CRISPR design
- primer specificity
- trace workflows
- project diffing

These are the beginning of a healthier service-layer split.

## `compat/`

Format and interoperability helpers:

- AB1 parsing
- DNA container import/export

## `collab/`

Persistence and collaboration helpers:

- review state
- workspace and permission storage
- audit events

## `webui/`

Current frontend shape:

- HTML app shell
- extracted CSS asset
- extracted browser-side JavaScript assets
- tab-driven workflow access
- interactive SVG render targets

Strength:

- easy local serving
- zero frontend build step

Current limitation:

- browser logic is now domain-split under `webui/js/`, but it still depends on global script scope
- limited state boundaries
- difficult long-term maintainability

## Persistence Model

The project is intentionally local-first. Runtime state is stored as JSON files in repo-local directories.

Advantages:

- simple to inspect
- easy to back up
- low infrastructure overhead

Tradeoff:

- no transactional durability model
- not designed for concurrent multi-user server deployment

## Testing Layers

Current:

- `tests/` for focused unit checks
- `smoke_test.py` for endpoint breadth
- `real_world_functional_test.py` for realistic workflow coverage
- `docs/validate_docs.py` for documentation drift detection

Target:

- deeper unit coverage
- richer integration testing
- browser-based end-to-end tests
- release artifact validation

## Key Architectural Risks

1. the browser app logic in `webui/js/` is cleaner and domain-split now, but still lacks typed components and stronger state boundaries.
2. the HTTP entrypoint is still custom and not framework-backed.
3. product docs and tutorial support files can drift without automated checks.
4. packaging and dependency management were historically implicit.

## Modernization Direction

The current plan is incremental, not a flag-day rewrite.

Recommended direction:

1. stabilize docs and packaging
2. strengthen CI and focused tests
3. extract backend modules by domain
4. move the frontend to a typed component model
5. preserve endpoint compatibility during migration

See [Modernization Plan](MODERNIZATION_PLAN.md) for phases and sequencing.
