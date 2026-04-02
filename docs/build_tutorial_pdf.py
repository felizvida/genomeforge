#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "docs" / "tutorial" / "user_training_tutorial.html"
PDF_PATH = ROOT / "docs" / "tutorial" / "user_training_tutorial.pdf"


def main() -> None:
    try:
        from weasyprint import HTML
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise SystemExit(
            "WeasyPrint is not installed. Run `python3 -m pip install -e \".[docs]\"` "
            "or `python3 -m pip install --user weasyprint` first."
        ) from exc

    if not HTML_PATH.exists():
        raise SystemExit(f"Tutorial HTML not found: {HTML_PATH}")

    HTML(filename=str(HTML_PATH), base_url=str(HTML_PATH.parent)).write_pdf(
        str(PDF_PATH),
        pdf_tags=True,
        custom_metadata=True,
        presentational_hints=True,
        srgb=True,
    )
    print(f"Wrote {PDF_PATH}")


if __name__ == "__main__":
    main()
