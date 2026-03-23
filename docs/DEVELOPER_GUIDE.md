# Developer Guide

## Repo Shape

Current major implementation surfaces:

- `backend/`: extracted API-domain modules for backend decomposition, currently including record I/O/core workflows, design-assist workflows, trace, search/reference, project/share/history, cloning/assembly, analysis/alignment, and biology-support domains
- `genomeforge_toolkit.py`: core sequence engine and CLI
- `web_ui.py`: HTTP server and compatibility-preserving dispatch/bootstrap layer
- `bio/`: biology-focused helper modules
- `compat/`: interop and format adapters
- `collab/`: collaboration and persistence helpers
- `webui/`: HTML app shell plus extracted CSS and browser-side JavaScript assets
- `smoke_test.py`: broad API regression runner
- `real_world_functional_test.py`: real-sequence workflow validation
- `docs/`: product, training, release, and modernization documentation

## Common Commands

Runtime:

```bash
python3 web_ui.py --port 8080
```

Editable install:

```bash
python3 -m pip install -e ".[dev,bio]"
```

Docs validation:

```bash
python3 docs/validate_docs.py
```

Tutorial PDF rebuild:

```bash
python3 docs/build_tutorial_pdf.py
```

Tutorial source regeneration:

```bash
python3 docs/tutorial/generate_tutorial.py
```

Tutorial screenshot regeneration:

```bash
npm run tutorial:screenshots
```

Unit baseline:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

If dev dependencies are installed:

```bash
python3 -m pytest
```

Broader regression:

```bash
python3 smoke_test.py
python3 real_world_functional_test.py
```

Browser regression:

```bash
npm install
npx playwright install chromium
npm run test:e2e
```

## Make Targets

This repo now includes a `Makefile`:

- `make run`
- `make smoke`
- `make functional`
- `make unit`
- `make pytest`
- `make e2e`
- `make docs-check`
- `make tutorial-pdf`
- `make tutorial-screenshots`

## Testing Strategy

The intended test stack is layered:

1. `unittest` and `pytest` for focused algorithm and contract checks
2. `smoke_test.py` for broad endpoint coverage
3. `real_world_functional_test.py` for workflow validation on real biological examples
4. Playwright for browser-level user workflow checks
5. `docs/validate_docs.py` for documentation consistency

Current shipped baseline:

- focused unit coverage in `tests/`
- broad API regression through `smoke_test.py`
- end-to-end biology workflow regression through `real_world_functional_test.py`
- browser workflow regression through `e2e/webui.spec.js` and shared helpers under `e2e/support/`

## Generated Runtime Data

The application creates JSON-backed runtime directories in the repo root as needed:

- `projects/`
- `collections/`
- `shares/`
- `annotation_db/`
- `enzyme_sets/`
- `reference_db/`
- `collab_data/`

These are data artifacts, not source code. Test suites may create and clean them.

The tutorial generator also writes reproducible training assets under `docs/tutorial/datasets/`, including:

- `training_real_world_dataset.json`
- `case_playbook.md`
- `README.md`
- `case_bundles/` with one ready-to-load bundle per tutorial case

## Contribution Priorities

Current engineering priorities are tracked in:

- [Modernization Plan](MODERNIZATION_PLAN.md)
- [Architecture](ARCHITECTURE.md)
- [API Reference](API.md)
- [Contributing Guide](../CONTRIBUTING.md)

In practice, the highest-value work right now is:

1. doc accuracy and discoverability
2. packaging and local development ergonomics
3. migrating the domain-split browser scripts under `webui/js/` toward typed components and clearer state ownership
4. hardening the HTTP entry layer beyond the current lightweight custom server
5. stronger layered testing

## Release Discipline

Before cutting a release:

```bash
python3 docs/validate_docs.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 smoke_test.py
python3 real_world_functional_test.py
```

If development dependencies are installed, also run:

```bash
python3 -m pytest
npm run test:e2e
```

Then update:

- `CHANGELOG.md`
- tutorial HTML via `python3 docs/tutorial/generate_tutorial.py`
- release notes in `docs/releases/`
- tutorial PDF if tutorial HTML changed
- any affected product docs

## Community Intake

GitHub community-facing files now live in:

- `.github/ISSUE_TEMPLATE/`: structured issue intake for bugs, feature requests, and workflow feedback
- `.github/DISCUSSION_TEMPLATE/`: prompts for ideas, questions, general discussion, and show-and-tell posts
- `.github/pull_request_template.md`: PR summary and validation checklist

When changing user-facing workflows, update these files if the best intake path or expected reproduction details change.
