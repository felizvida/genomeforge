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
