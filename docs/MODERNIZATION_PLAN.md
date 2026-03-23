# Genome Forge Modernization Plan

Date: 2026-03-23

## Purpose

This document turns the current documentation audit into an execution-ready modernization roadmap for Genome Forge.

The goal is not to change the scientific scope of the project. The goal is to make the existing product easier to run, easier to trust, easier to extend, and easier to ship.

## Current Baseline

Genome Forge already has broad workflow coverage and strong feature breadth. The main modernization problem is not missing product ambition. The main problem is that project structure, documentation, packaging, and quality gates have not kept pace with product growth.

Current local baseline:

- Backend entrypoint: `web_ui.py` is now about 130 lines and mostly serves as HTTP/bootstrap glue.
- Frontend shell: `webui/index.html` is now about 700 lines, with browser logic split into domain-oriented assets under `webui/js/`.
- Core engine: `genomeforge_toolkit.py` is about 1000 lines.
- Broad regression coverage exists through `smoke_test.py` and `real_world_functional_test.py`.
- CI runs compile checks plus the smoke and real-world suites on GitHub Actions.
- Tutorial coverage is broad, but tutorial support files do not fully track the source tutorial.
- Documentation is present, but the repo front door still describes the project like a small toolkit instead of a modern web workbench.
- `FEATURE_COVERAGE.md` now distinguishes availability, maturity, and validation, but it is still maintained by hand rather than generated from structured metadata.

## Modernization Objectives

1. Reposition Genome Forge as a product, not just a script bundle.
2. Make documentation accurate, navigable, and generated from durable sources of truth where possible.
3. Reduce architectural risk by breaking up the backend and frontend monoliths.
4. Standardize packaging, local development, testing, and release workflows.
5. Improve UI structure and interaction quality without losing the existing scientific workflows.
6. Make feature maturity and validation status explicit so users know what is production-ready versus heuristic.

## Guiding Principles

1. Preserve working biology workflows while modernizing internals.
2. Prefer incremental migration over large rewrites with long instability windows.
3. Make every modernization step test-backed.
4. Keep the local-first usage model intact.
5. Treat docs, packaging, and release engineering as first-class product surfaces.

## Audit Summary

The documentation review identified these modernization drivers:

1. `README.md` undersells the product and overwhelms new users with a flat feature dump.
2. `HANDOFF_ZERO_MEMORY.md` contains stale commit, test-count, and API-surface expectations.
3. Tutorial source and tutorial support files have drifted apart.
4. `FEATURE_COVERAGE.md` has been reset to distinguish availability, maturity, and validation, but it is still hand-maintained and should eventually derive from structured metadata.
5. The repo lacks a modern Python packaging contract such as `pyproject.toml`.
6. CI is useful but minimal, and does not yet validate docs, packaging, browser workflows, or release artifacts.
7. The current backend and frontend file layout will increasingly slow feature work and bug fixing.

## Target State

At the end of modernization, Genome Forge should look like this:

- A product-first README with screenshots, quickstart, and clear user paths.
- A structured docs system with install, user guide, developer guide, API reference, architecture notes, and changelog.
- A packaged Python application with dependency groups and reproducible local setup.
- A modular backend with typed request and response models.
- A modular frontend with components, state boundaries, and testable visualization units.
- Multi-layer testing: unit, integration, end-to-end, and docs validation.
- CI and release automation that validate the same behaviors maintainers rely on locally.
- A transparent capability matrix that communicates both feature availability and feature maturity.

## Workstreams

### 1. Documentation And Knowledge System

Deliverables:

- Rewrite `README.md` as a product-first entry point.
- Add `docs/INSTALL.md`.
- Add `docs/USER_GUIDE.md`.
- Add `docs/DEVELOPER_GUIDE.md`.
- Add `docs/ARCHITECTURE.md`.
- Add `docs/API.md`.
- Add `CHANGELOG.md`.
- Refresh `HANDOFF_ZERO_MEMORY.md`.
- Make tutorial support files derive from the same source registry as the tutorial itself.

Exit criteria:

- A new contributor can install, run, test, and navigate the project without reading source first.
- Handoff documentation matches current commit, test counts, and API surface.
- Tutorial metadata stays in sync across HTML, PDF, and supporting case indexes.

### 2. Packaging And Local Developer Experience

Deliverables:

- Add `pyproject.toml`.
- Define install extras such as `dev`, `docs`, and optional biology adapters.
- Add one task runner entrypoint such as `Makefile` or `justfile`.
- Standardize run commands for CLI, server, tests, and docs builds.
- Document optional dependencies such as Biopython and external aligners.

Exit criteria:

- A clean environment can install Genome Forge with one documented command path.
- Local setup does not depend on undocumented global tools.
- Development commands are short, stable, and discoverable.

### 3. Backend Architecture

Deliverables:

- Split `web_ui.py` into route, service, persistence, and visualization modules.
- Introduce typed schema boundaries for inputs and outputs.
- Isolate sequence I/O, analysis logic, and HTML-serving concerns.
- Decide whether to remain on stdlib HTTP or migrate gradually to FastAPI.

Recommended direction:

- Gradual FastAPI migration with compatibility-preserving endpoint paths.

Rationale:

- FastAPI would provide structured validation, cleaner routing, easier OpenAPI generation, and a more maintainable contract surface.

Exit criteria:

- Endpoint logic is no longer concentrated in one giant file.
- New endpoints can be added without editing a large dispatch monolith.
- API contracts are explicit and testable.

### 4. Frontend Architecture And UI Modernization

Deliverables:

- Replace the single-file frontend with a modular app, ideally Vite plus React plus TypeScript.
- Build a small design system with shared tokens for typography, spacing, color, and panels.
- Split visualization panels into components with clear props and state ownership.
- Preserve current SVG-rich visualizations while improving layout, state persistence, and workflow discoverability.
- Add browser-based tests for primary workflows.

Design goals:

- Product-quality navigation.
- Clear workflow grouping by biological task.
- Better progressive disclosure for advanced options.
- Stronger visual hierarchy for results, warnings, and action recommendations.
- Better support for long sessions and large records.

Exit criteria:

- Frontend code is componentized and typed.
- The UI remains local-first and fast.
- Core workflows can be validated through browser automation.

### 5. Testing And Quality Gates

Deliverables:

- Add `pytest` for unit and API integration coverage.
- Preserve `smoke_test.py` and `real_world_functional_test.py` as broad regression layers.
- Add frontend end-to-end tests, ideally with Playwright.
- Add docs build validation.
- Add SVG golden or structural tests for major renderers where practical.
- Add linting and optional type checking.

Recommended baseline:

- `ruff`
- `pytest`
- `mypy` or another incremental typing gate
- Playwright for end-to-end validation

Exit criteria:

- Quality gates are layered rather than concentrated in two large scripts.
- High-risk algorithms and renderers have focused regression coverage.
- CI failure output points clearly to the failing layer.

### 6. Release Engineering And Operations

Deliverables:

- Consolidate release history into `CHANGELOG.md`.
- Keep release notes in `docs/releases/` only if they are generated from the changelog or release template.
- Add release automation on tag pushes.
- Build and attach source artifacts automatically.
- Add docs artifact validation during release.
- Add a containerization path if deployment beyond local usage remains important.

Optional but recommended:

- Add `Dockerfile`.
- Add health-check guidance.
- Document data directories and backup expectations.

Exit criteria:

- A release can be cut from a repeatable checklist or automated workflow.
- The release pipeline verifies the same artifacts users download.

### 7. Capability Communication

Deliverables:

- Replace the current feature legend with a matrix that distinguishes availability, maturity, validation, and known constraints.
- Link major features to tests, docs, and example workflows where possible.

Recommended maturity labels:

- `Production-ready`
- `Validated heuristic`
- `Experimental`
- `Out of scope`

Exit criteria:

- Users can tell not only whether a feature exists, but how much confidence to place in it.

## Phased Roadmap

### Phase 0: Documentation Reset And Source-Of-Truth Cleanup

Duration:

- 1 week

Tasks:

- Rewrite README as product-first.
- Refresh handoff with current commit, test counts, API counts, and repo structure.
- Create install, developer, architecture, and API docs.
- Create changelog.
- Bring tutorial source and support files into sync.
- Add a docs index page.

Success criteria:

- A newcomer can understand what Genome Forge is within five minutes.
- Core docs no longer contradict one another.

### Phase 1: Packaging And Developer Ergonomics

Duration:

- 1 to 2 weeks

Tasks:

- Add `pyproject.toml`.
- Create dependency extras.
- Add `Makefile` or equivalent.
- Standardize docs build commands.
- Document supported Python versions and optional tools.

Success criteria:

- A clean checkout can be installed and run with a small documented command set.

### Phase 2: CI And Test Stack Hardening

Duration:

- 1 to 2 weeks

Tasks:

- Add `pytest` coverage for core logic and API slices.
- Add lint and optional type checks.
- Add tutorial/docs validation.
- Add browser end-to-end coverage for critical workflows.
- Expand CI matrix to at least Python 3.11 and 3.12.

Success criteria:

- CI failures identify whether a breakage is in core logic, API contract, UI workflow, or docs generation.

### Phase 3: Backend Decomposition

Duration:

- 2 to 4 weeks

Tasks:

- Extract route handlers by domain.
- Extract visualization renderers.
- Extract persistence adapters.
- Introduce typed models.
- Optionally begin FastAPI compatibility layer.

Success criteria:

- `web_ui.py` is reduced to composition and app wiring rather than being the primary implementation surface.

### Phase 4: Frontend Rebuild Around Existing Workflows

Duration:

- 3 to 5 weeks

Tasks:

- Set up Vite, React, and TypeScript.
- Rebuild navigation and workflow panels.
- Port map, track, trace, and comparison visualizations into components.
- Add persistent session and project state architecture.
- Add browser tests for user-critical flows.

Success criteria:

- Users get a cleaner, faster, more structured interface without losing feature access.

### Phase 5: Productization And Deployment

Duration:

- 2 to 3 weeks

Tasks:

- Add container support if desired.
- Document production-like local deployment.
- Add release automation.
- Add health checks and basic operational troubleshooting docs.

Success criteria:

- The repo supports repeatable release and deployment workflows rather than ad hoc local serving only.

## Dependencies And Order

Recommended execution order:

1. Phase 0
2. Phase 1
3. Phase 2
4. Phase 3
5. Phase 4
6. Phase 5

This order is intentional. Documentation and packaging need to be trustworthy before deeper architecture changes begin. Backend decomposition should also land before or alongside the frontend rebuild, because the future UI will benefit from cleaner API boundaries.

## Risks And Mitigations

Risk:

- A full rewrite could stall feature delivery.

Mitigation:

- Use compatibility-preserving incremental migration.

Risk:

- Docs can drift again after cleanup.

Mitigation:

- Generate what can be generated and keep source-of-truth registries small and explicit.

Risk:

- UI modernization could degrade advanced workflows.

Mitigation:

- Preserve workflow-level browser tests before large UI changes.

Risk:

- Increased tooling can burden contributors.

Mitigation:

- Keep the default local path simple and document optional tools as optional.

## Immediate Next Actions

1. Rewrite `README.md`.
2. Refresh `HANDOFF_ZERO_MEMORY.md`.
3. Add `docs/INSTALL.md`.
4. Add `docs/DEVELOPER_GUIDE.md`.
5. Add `docs/ARCHITECTURE.md`.
6. Add `docs/API.md`.
7. Add `CHANGELOG.md`.
8. Add `pyproject.toml`.
9. Add `pytest` baseline and first focused unit tests.
10. Expand CI to validate docs and packaging.

## Non-Goals For This Modernization Pass

1. Replacing scientific heuristics with full proprietary parity.
2. Changing the local-first product direction.
3. Introducing cloud complexity unless there is a concrete deployment requirement.
4. Removing working endpoints before replacements are ready.

## Definition Of Success

Modernization is successful when Genome Forge is easier to understand, easier to contribute to, easier to test, and easier to release, while preserving the practical biology workflows that make the project valuable.
