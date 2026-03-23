PYTHON ?= python3

.PHONY: install install-dev install-docs run smoke functional unit pytest docs-check tutorial-pdf tutorial-screenshots e2e

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

docs-check:
	$(PYTHON) docs/validate_docs.py

tutorial-pdf:
	$(PYTHON) docs/build_tutorial_pdf.py

tutorial-screenshots:
	npm run tutorial:screenshots

e2e:
	npm run test:e2e
