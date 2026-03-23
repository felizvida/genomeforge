# Contributing to Genome Forge

Genome Forge is a local-first bioinformatics workbench for DNA design, cloning, validation, visualization, and training. Contributions are welcome across code, documentation, test coverage, tutorials, workflow polish, and real-world usability feedback.

## Best Ways To Contribute

- report a reproducible bug
- request a feature or workflow improvement
- share a real lab or analysis workflow that feels awkward or incomplete
- improve documentation, tutorial content, or training datasets
- add tests, validation cases, or browser coverage
- submit code changes that improve correctness, clarity, or maintainability

## Where To Put Feedback

- `Issues`: confirmed bugs, concrete feature requests, and workflow gaps that should turn into tracked work
- `Discussions`: questions, design ideas, usage help, showcase posts, and broader product feedback
- `Pull requests`: code, docs, tests, and tutorial improvements

If you are unsure whether something is a bug or a question, start with a Discussion.

## Before Opening An Issue

Please include enough context that someone else can reproduce or understand the problem without guessing:

- Genome Forge version or commit SHA
- operating system and Python version
- whether you are using the web UI, CLI, or both
- the input format involved, for example `FASTA`, `GenBank`, `AB1`, or a training case bundle
- a short sequence fragment or a de-identified minimal example when possible
- exact steps, expected behavior, and actual behavior
- screenshots if the problem is visual

For workflow requests, the most useful details are:

- the biological task you are trying to complete
- the kind of data you start with
- the output you need to trust
- what part of the current workflow feels slow, confusing, or error-prone

## Local Setup

Basic editable install:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[dev,bio]"
```

Run the web UI:

```bash
genomeforge-web --port 8080
```

Or directly:

```bash
python3 web_ui.py --port 8080
```

Optional browser test setup:

```bash
npm install
npx playwright install chromium
```

## Development Workflow

1. Create a focused branch.
2. Make the smallest coherent change that solves the problem.
3. Update docs when behavior, workflow names, screenshots, or tutorial content change.
4. Run the smallest useful test set locally, then broaden validation before opening a PR.
5. Explain the user-facing impact in the PR description.

## Expected Validation

Run what matches the scope of your change.

Documentation-only changes:

```bash
python3 docs/validate_docs.py
```

Python/unit changes:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Broad backend workflow changes:

```bash
python3 smoke_test.py
python3 real_world_functional_test.py
```

Frontend or workflow UI changes:

```bash
npm run test:e2e
```

If you regenerate tutorial assets:

```bash
python3 docs/tutorial/generate_tutorial.py
python3 docs/build_tutorial_pdf.py
```

## Documentation And Tutorial Contributions

Genome Forge’s tutorial is meant to teach both software use and the biology behind each case.

When editing tutorial or training content:

- prefer real-world public or clearly labeled training-derived data
- explain biological meaning in plain language for readers without formal biology training
- include expected results and interpretation, not just button clicks
- keep sample data easy to find under `docs/tutorial/datasets/`
- regenerate screenshots and the PDF when the visible workflow changes

## Pull Request Checklist

Before opening a PR, please check:

- the change is scoped and explained clearly
- affected docs were updated
- generated tutorial assets were rebuilt if needed
- relevant tests passed locally
- screenshots are included when the change is UI-heavy
- known limitations or follow-up work are called out directly

## Notes On Scientific Use

Genome Forge helps with planning, validation, visualization, and interpretation, but software output is not a substitute for experimental judgment. Please sanity-check any result that would affect a wet-lab decision, especially around cloning design, primer choice, CRISPR targeting, and sequence verification.
