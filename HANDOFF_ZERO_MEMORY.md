# Genome Forge Zero-Memory Handoff

This document is for resuming work on Genome Forge with no prior context.

## 1. What This Repo Is

Genome Forge is a local-first DNA and plasmid workbench.

Core surfaces:

- `backend/`: extracted backend API-domain modules
- `genomeforge_toolkit.py`: sequence engine and CLI
- `web_ui.py`: local HTTP server and API dispatch
- `webui/`: browser UI shell plus extracted CSS/JS assets
- `bio/`, `compat/`, `collab/`: helper modules
- `smoke_test.py`: broad endpoint regression
- `real_world_functional_test.py`: realistic workflow validation
- `tests/`: focused unit-test baseline

Primary docs:

- [README.md](/Users/liux17/Documents/Playground/README.md)
- [docs/README.md](/Users/liux17/Documents/Playground/docs/README.md)
- [docs/API.md](/Users/liux17/Documents/Playground/docs/API.md)
- [docs/ARCHITECTURE.md](/Users/liux17/Documents/Playground/docs/ARCHITECTURE.md)
- [docs/MODERNIZATION_PLAN.md](/Users/liux17/Documents/Playground/docs/MODERNIZATION_PLAN.md)

## 2. Current State

What matters operationally:

- The product already has broad feature coverage.
- Backend decomposition has started: record I/O/core workflows, design-assist workflows, trace, BLAST-like search, reference-library, siRNA, project/share/history, cloning/assembly, analysis/alignment, and biology-support workflows now live in `backend/`.
- Current known local regression baseline is:
  - `smoke_test.py`: `108` passing checks
  - `real_world_functional_test.py`: `97` passing steps
- The API surface currently includes `102` `/api/*` endpoints plus `GET /share/<share_id>`.
- The biggest engineering constraint is structural: the frontend is now split into domain-oriented assets under `webui/js/`, but it still relies on plain browser globals rather than typed components or a dedicated frontend framework, and `web_ui.py` is still the HTTP entry point plus compatibility-preserving dispatcher.

Do not trust stale hard-coded commit references in old docs. Confirm actual state locally with:

```bash
git log -1 --oneline
git status --short
```

## 3. How To Run

Direct source run:

```bash
python3 web_ui.py --host 127.0.0.1 --port 8080
```

Open:

```text
http://127.0.0.1:8080
```

If installed in editable mode:

```bash
genomeforge-web --host 127.0.0.1 --port 8080
```

## 4. Validation Commands

Docs consistency:

```bash
python3 docs/validate_docs.py
```

Focused unit baseline:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Broad regressions:

```bash
python3 smoke_test.py
python3 real_world_functional_test.py
```

If dev dependencies are installed:

```bash
python3 -m pytest
```

## 5. Documentation Map

Use these in order:

1. [README.md](/Users/liux17/Documents/Playground/README.md)
2. [docs/INSTALL.md](/Users/liux17/Documents/Playground/docs/INSTALL.md)
3. [docs/USER_GUIDE.md](/Users/liux17/Documents/Playground/docs/USER_GUIDE.md)
4. [docs/DEVELOPER_GUIDE.md](/Users/liux17/Documents/Playground/docs/DEVELOPER_GUIDE.md)
5. [docs/API.md](/Users/liux17/Documents/Playground/docs/API.md)
6. [docs/ARCHITECTURE.md](/Users/liux17/Documents/Playground/docs/ARCHITECTURE.md)
7. [docs/MODERNIZATION_PLAN.md](/Users/liux17/Documents/Playground/docs/MODERNIZATION_PLAN.md)

## 6. Architecture Snapshot

Current runtime path:

```text
browser -> web_ui.py -> genomeforge_toolkit.py / bio / compat / collab -> JSON-backed local storage
```

Current storage directories created at runtime:

- `projects/`
- `collections/`
- `shares/`
- `annotation_db/`
- `enzyme_sets/`
- `reference_db/`
- `collab_data/`

The repo is intentionally local-first and file-backed.

## 7. API Surface

Do not use this handoff file as the canonical endpoint list.

The authoritative human-readable inventory is:

- [docs/API.md](/Users/liux17/Documents/Playground/docs/API.md)

The doc validator checks that `docs/API.md` matches the endpoint inventory extracted from `web_ui.py`.

## 8. Tutorial And Training

Training assets:

- [docs/tutorial/user_training_tutorial.html](/Users/liux17/Documents/Playground/docs/tutorial/user_training_tutorial.html)
- [docs/tutorial/user_training_tutorial.pdf](/Users/liux17/Documents/Playground/docs/tutorial/user_training_tutorial.pdf)
- [docs/tutorial/datasets/case_playbook.md](/Users/liux17/Documents/Playground/docs/tutorial/datasets/case_playbook.md)

The tutorial currently covers `37` cases and the supporting playbook should match those same `37` case identifiers.

## 9. What Changed In The Modernization Foundation Pass

Recent structural improvements added:

- `pyproject.toml`
- `Makefile`
- `docs/build_tutorial_pdf.py`
- `docs/validate_docs.py`
- structured docs under `docs/`
- a focused unit-test baseline in `tests/`

This means the repo now has a clearer package/install story even though the architecture refactor is not finished yet.

## 10. Known Constraints

- `webui/js/` is now split by domain, but it is still plain-script architecture rather than typed components with isolated state.
- `web_ui.py` is lightweight now, but it is still a custom HTTP entrypoint rather than a framework-backed app.
- Some biological algorithms are intentionally heuristic rather than proprietary parity implementations.
- Optional workflows still depend on external tooling or optional Python packages.

## 11. Recommended Next Work

See [docs/MODERNIZATION_PLAN.md](/Users/liux17/Documents/Playground/docs/MODERNIZATION_PLAN.md).

If you are continuing implementation, the recommended order is:

1. finish the Phase 0 doc reset details
2. expand packaging and developer ergonomics
3. harden CI and focused tests
4. decompose `web_ui.py`
5. decompose the frontend

## 12. Quick Restart Checklist

```bash
git status --short
python3 docs/validate_docs.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 smoke_test.py
python3 real_world_functional_test.py
python3 web_ui.py --port 8080
```

If those pass, you are back at a good working baseline.
