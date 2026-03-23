#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API_DOC = ROOT / "docs" / "API.md"
TUTORIAL = ROOT / "docs" / "tutorial" / "user_training_tutorial.html"
PLAYBOOK = ROOT / "docs" / "tutorial" / "datasets" / "case_playbook.md"
DATASET_README = ROOT / "docs" / "tutorial" / "datasets" / "README.md"
CASE_BUNDLES_DIR = ROOT / "docs" / "tutorial" / "datasets" / "case_bundles"
SCREENSHOT_DIR = ROOT / "docs" / "tutorial" / "assets" / "screenshots"
README = ROOT / "README.md"
HANDOFF = ROOT / "HANDOFF_ZERO_MEMORY.md"
WEB_UI = ROOT / "web_ui.py"
BACKEND_DIR = ROOT / "backend"

EXPECTED_CASE_COUNT = 37
EXPECTED_SECTION_LABELS = [
    "Step-by-Step in Genome Forge",
    "Sample Results",
    "Expected Results",
    "How to Interpret the Results",
    "Biological Explanation",
]


def fail(errors: list[str]) -> int:
    for error in errors:
        print(f"[FAIL] {error}")
    return 1


def unique_case_ids(html: str) -> list[str]:
    seen: list[str] = []
    for case_id in re.findall(r"Case ([A-Z]{1,2}):", html):
        if case_id not in seen:
            seen.append(case_id)
    return seen


def extract_api_inventory(text: str) -> set[str]:
    return set(re.findall(r"/api/[a-z0-9\\-]+", text))


def extract_code_api_inventory(text: str) -> set[str]:
    return set(re.findall(r'"(/api/[a-z0-9\\-]+)"', text))


def main() -> int:
    errors: list[str] = []

    required_files = [
        ROOT / "docs" / "README.md",
        ROOT / "docs" / "INSTALL.md",
        ROOT / "docs" / "USER_GUIDE.md",
        ROOT / "docs" / "DEVELOPER_GUIDE.md",
        ROOT / "docs" / "ARCHITECTURE.md",
        API_DOC,
        ROOT / "docs" / "MODERNIZATION_PLAN.md",
        ROOT / "CHANGELOG.md",
        README,
        HANDOFF,
        TUTORIAL,
        PLAYBOOK,
        DATASET_README,
    ]
    for path in required_files:
        if not path.exists():
            errors.append(f"Missing required documentation file: {path}")

    tutorial_text = TUTORIAL.read_text(encoding="utf-8")
    case_ids = unique_case_ids(tutorial_text)
    if len(case_ids) != EXPECTED_CASE_COUNT:
        errors.append(f"Tutorial case count is {len(case_ids)}, expected {EXPECTED_CASE_COUNT}")
    if tutorial_text.count("Cluster ") < 8:
        errors.append("Tutorial cluster headings appear incomplete")
    for label in EXPECTED_SECTION_LABELS:
        count = tutorial_text.count(label)
        if count != EXPECTED_CASE_COUNT:
            errors.append(f"Tutorial section '{label}' appears {count} times, expected {EXPECTED_CASE_COUNT}")

    playbook_text = PLAYBOOK.read_text(encoding="utf-8")
    playbook_cases = set(re.findall(r"## Case ([A-Z]{1,2}):", playbook_text))
    if len(playbook_cases) != EXPECTED_CASE_COUNT:
        errors.append(f"Case playbook contains {len(playbook_cases)} cases, expected {EXPECTED_CASE_COUNT}")
    if playbook_cases != set(case_ids):
        missing = sorted(set(case_ids) - playbook_cases)
        extra = sorted(playbook_cases - set(case_ids))
        if missing:
            errors.append(f"Case playbook is missing tutorial cases: {', '.join(missing)}")
        if extra:
            errors.append(f"Case playbook contains unknown cases: {', '.join(extra)}")

    if not CASE_BUNDLES_DIR.exists():
        errors.append(f"Missing generated tutorial case bundles directory: {CASE_BUNDLES_DIR}")
    else:
        bundle_dirs = sorted(path for path in CASE_BUNDLES_DIR.glob("case_*") if path.is_dir())
        if len(bundle_dirs) != EXPECTED_CASE_COUNT:
            errors.append(f"Tutorial case bundle count is {len(bundle_dirs)}, expected {EXPECTED_CASE_COUNT}")
        sample_bundle = CASE_BUNDLES_DIR / "case_a"
        for required in [sample_bundle / "records.fasta", sample_bundle / "manifest.json"]:
            if not required.exists():
                errors.append(f"Tutorial sample bundle is missing required file: {required}")

    if not SCREENSHOT_DIR.exists():
        errors.append(f"Missing tutorial screenshot directory: {SCREENSHOT_DIR}")
    else:
        pngs = sorted(SCREENSHOT_DIR.glob("*.png"))
        if len(pngs) < 8:
            errors.append(f"Tutorial screenshot count is {len(pngs)}, expected at least 8 flagship screenshots")

    api_doc_text = API_DOC.read_text(encoding="utf-8")
    code_api: set[str] = set()
    code_api |= extract_code_api_inventory(WEB_UI.read_text(encoding="utf-8"))
    if BACKEND_DIR.exists():
        for path in sorted(BACKEND_DIR.glob("*.py")):
            code_api |= extract_code_api_inventory(path.read_text(encoding="utf-8"))
    doc_api = extract_api_inventory(api_doc_text)
    if code_api != doc_api:
        missing = sorted(code_api - doc_api)
        extra = sorted(doc_api - code_api)
        if missing:
            errors.append(f"API.md is missing endpoints: {', '.join(missing)}")
        if extra:
            errors.append(f"API.md documents unknown endpoints: {', '.join(extra)}")

    readme_text = README.read_text(encoding="utf-8")
    for needle in ["docs/README.md", "docs/INSTALL.md", "docs/API.md", "docs/MODERNIZATION_PLAN.md"]:
        if needle not in readme_text:
            errors.append(f"README.md does not reference {needle}")

    handoff_text = HANDOFF.read_text(encoding="utf-8")
    for needle in ["docs/API.md", "docs/MODERNIZATION_PLAN.md", "108", "97", "102", "generate_tutorial.py", "case_bundles"]:
        if needle not in handoff_text:
            errors.append(f"HANDOFF_ZERO_MEMORY.md does not include expected marker '{needle}'")

    if errors:
        return fail(errors)
    print("Documentation validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
