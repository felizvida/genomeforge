PYTHON ?= python3
COVERAGE_TARGETS := --cov=backend --cov=bio --cov=collab --cov=compat --cov=canonical_schema --cov=genomeforge_toolkit --cov=web_ui

.PHONY: install install-dev install-docs run smoke functional unit pytest coverage lint docs-check tutorial-pdf tutorial-screenshots e2e quality

install:
	$(PYTHON) -m pip install -e .

install-dev:
	$(PYTHON) -m pip install -e ".[dev,bio]"

install-docs:
	$(PYTHON) -m pip install -e ".[docs]"

run:
	$(PYTHON) web_ui.py --port 8080

smoke:
	$(PYTHON) smoke_test.py

functional:
	$(PYTHON) real_world_functional_test.py

unit:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py'

pytest:
	$(PYTHON) -m pytest

coverage:
	$(PYTHON) -m pytest $(COVERAGE_TARGETS) --cov-report=term-missing:skip-covered --cov-report=xml

lint:
	$(PYTHON) -m ruff check .

docs-check:
	$(PYTHON) docs/validate_docs.py

tutorial-pdf:
	$(PYTHON) docs/build_tutorial_pdf.py

tutorial-screenshots:
	npm run tutorial:screenshots

e2e:
	npm run test:e2e

quality: lint coverage docs-check
