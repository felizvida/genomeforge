# Install Guide

## Requirements

- Python 3.11 or newer
- A modern browser for the web UI
- Node.js 20 or newer if you want to run browser end-to-end tests locally
- Optional:
  - Biopython for native proprietary `.dna` parsing
  - WeasyPrint for rebuilding the PDF tutorial
  - External aligners such as MAFFT, MUSCLE, ClustalW, or T-Coffee for adapter-backed MSA workflows

## Fastest Path: Run From Source

If you only want to launch the local UI and use the existing built-in functionality:

```bash
python3 web_ui.py --port 8080
```

Then open:

```text
http://127.0.0.1:8080
```

The web UI is loopback-only by default. If you intentionally expose it to a trusted network, you must opt in:

```bash
python3 web_ui.py --host 0.0.0.0 --port 8080 --allow-remote
```

Do not use remote binding on an untrusted network; the current server is a local-first workbench, not a hosted multi-user service.

The JSON API accepts POST bodies up to 64 MiB by default. For unusually large trusted local records, raise the cap explicitly:

```bash
python3 web_ui.py --port 8080 --max-post-mb 128
```

## Recommended Path: Editable Local Install

Create an environment and install the project in editable mode:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e .
```

This gives you console entry points:

```bash
genomeforge --help
genomeforge-web --port 8080
```

## Development Install

Install the repository with development helpers and optional bioinformatics adapters:

```bash
python3 -m pip install -e ".[dev,bio]"
```

This adds:

- `pytest`
- `pytest-cov`
- `ruff`
- `biopython`

## Documentation Install

If you want to rebuild the tutorial PDF:

```bash
python3 -m pip install -e ".[docs]"
```

Then rebuild:

```bash
python3 docs/build_tutorial_pdf.py
```

If WeasyPrint installation fails on your platform, consult the WeasyPrint platform dependency notes. Genome Forge itself does not require WeasyPrint at runtime.

## Verify The Install

Minimal validation:

```bash
python3 docs/validate_docs.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 smoke_test.py
python3 real_world_functional_test.py
```

If you installed development dependencies, you can also run:

```bash
python3 -m pytest
python3 -m pytest --cov=backend --cov=bio --cov=collab --cov=compat --cov=canonical_schema --cov=genomeforge_toolkit --cov=web_ui --cov-report=term-missing:skip-covered --cov-report=xml
python3 -m ruff check .
```

If you want browser end-to-end validation:

```bash
npm install
npx playwright install chromium
npm run test:e2e
```

## Common Optional Tools

- Native `.dna` parsing: `python3 -m pip install -e ".[bio]"`
- Tutorial PDF generation: `python3 -m pip install -e ".[docs]"`
- Full local contributor setup: `python3 -m pip install -e ".[dev,bio,docs]"`
