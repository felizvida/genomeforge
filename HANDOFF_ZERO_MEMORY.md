# Genome Forge Zero-Memory Handoff

This is the canonical restart document for picking up Genome Forge from a new chat thread with no human memory.

Use it before reading older plans or release notes. It is intentionally operational, concrete, and redundant where that prevents ambiguity.

## 1. Fresh Thread Starter

Paste this into a new Codex thread when resuming:

```text
We are working in /Users/liux17/Documents/Playground on Genome Forge.
Start by reading HANDOFF_ZERO_MEMORY.md, README.md, docs/README.md, docs/API.md, docs/ARCHITECTURE.md, docs/SECURITY_MODEL.md, and docs/MODERNIZATION_PLAN.md.
Treat dist/ release archives as intentionally untracked unless asked to clean them.
Do not remove or revert user changes.
Confirm git status, run docs validation and the unit baseline, then continue from the recommended next work.
```

If the new thread has enough time, run the full validation stack before making release decisions.

## 2. Repository Identity

- Product name: `Genome Forge`
- Repository: `felizvida/genomeforge`
- Local path: `/Users/liux17/Documents/Playground`
- Main branch in use: `master`
- License: Apache-2.0
- Latest documented release at this handoff: `v0.1.17`
- Latest release URL: `https://github.com/felizvida/genomeforge/releases/tag/v0.1.17`
- Runtime model: local-first workstation web app plus CLI, not a hosted multi-tenant SaaS service.

Genome Forge is a local-first DNA design, cloning, validation, visualization, and bioinformatics training workbench. It combines plasmid/sequence visualization, cloning simulation, primer/PCR/trace workflows, CRISPR helpers, reference search, project sharing/review, and a large tutorial built around real biological examples.

## 3. Current Git Hygiene

At the time this document was written, the expected dirty state is only untracked release archives under `dist/`.

Check:

```bash
git status --short
```

Expected pattern:

```text
?? dist/genomeforge-v0.1.*-source.tar.gz
?? dist/genomeforge-v0.1.*-source.zip
?? dist/genomeforge-v0.1.*-sha256.txt
```

Do not delete these archives unless the user explicitly asks for cleanup. They are local release assets, not source changes.

If anything outside `dist/` is modified or untracked, inspect it before editing. If it looks unrelated to your work, do not revert it.

## 4. Primary Code Surfaces

- `web_ui.py`: local HTTP server, security headers, request parsing, request-size guard, host binding guard, and API dispatch.
- `genomeforge_toolkit.py`: core sequence parsing, conversion, translation, ORF, digest, primer, PCR, rendering, and CLI logic.
- `backend/`: domain handlers extracted from the old monolithic server path.
- `bio/`: focused helper logic for CRISPR, primer specificity, trace tools, and project diffing.
- `compat/`: import/export support, including `.dna` and AB1-adjacent compatibility helpers.
- `collab/`: JSON-backed permissions, audit, workspace, and review helpers.
- `webui/`: browser UI assets.
- `webui/js/`: split browser-side workflow modules, still plain JavaScript globals.
- `tests/`: focused unit and domain regression tests.
- `e2e/`: Playwright browser workflow tests.
- `docs/`: structured documentation, tutorial, test reports, release notes, and modernization plan.

## 5. Documentation Map

Start here:

- [README.md](/Users/liux17/Documents/Playground/README.md): product overview, quickstart, validation snapshot, docs index, roadmap summary.
- [docs/README.md](/Users/liux17/Documents/Playground/docs/README.md): structured docs index.
- [docs/INSTALL.md](/Users/liux17/Documents/Playground/docs/INSTALL.md): local runtime, editable install, optional dependencies, validation setup.
- [docs/USER_GUIDE.md](/Users/liux17/Documents/Playground/docs/USER_GUIDE.md): user workflow guide.
- [docs/DEVELOPER_GUIDE.md](/Users/liux17/Documents/Playground/docs/DEVELOPER_GUIDE.md): repo layout, commands, tests, release workflow.
- [docs/API.md](/Users/liux17/Documents/Playground/docs/API.md): endpoint inventory grouped by workflow.
- [docs/ARCHITECTURE.md](/Users/liux17/Documents/Playground/docs/ARCHITECTURE.md): architecture state and decomposition notes.
- [docs/SECURITY_MODEL.md](/Users/liux17/Documents/Playground/docs/SECURITY_MODEL.md): local trust boundary, browser headers, bind safety, request limits, non-goals.
- [FEATURE_COVERAGE.md](/Users/liux17/Documents/Playground/FEATURE_COVERAGE.md): capability and maturity matrix.
- [docs/MODERNIZATION_PLAN.md](/Users/liux17/Documents/Playground/docs/MODERNIZATION_PLAN.md): phased roadmap.
- [CHANGELOG.md](/Users/liux17/Documents/Playground/CHANGELOG.md): release history.
- [docs/releases/](/Users/liux17/Documents/Playground/docs/releases): release-specific notes.

Training docs:

- [docs/tutorial/user_training_tutorial.html](/Users/liux17/Documents/Playground/docs/tutorial/user_training_tutorial.html)
- [docs/tutorial/user_training_tutorial.pdf](/Users/liux17/Documents/Playground/docs/tutorial/user_training_tutorial.pdf)
- [docs/tutorial/generate_tutorial.py](/Users/liux17/Documents/Playground/docs/tutorial/generate_tutorial.py)
- [docs/tutorial/datasets/README.md](/Users/liux17/Documents/Playground/docs/tutorial/datasets/README.md)
- [docs/tutorial/datasets/case_playbook.md](/Users/liux17/Documents/Playground/docs/tutorial/datasets/case_playbook.md)
- [docs/tutorial/datasets/case_bundles/](/Users/liux17/Documents/Playground/docs/tutorial/datasets/case_bundles)

## 6. Current Validation Baseline

Current shipped baseline:

- `python3 docs/validate_docs.py`: passes
- `python3 -m unittest discover -s tests -p 'test_*.py'`: `63` tests pass
- `./.venv-docs/bin/python -m pytest`: `63` tests pass when the docs virtualenv exists
- `python3 smoke_test.py`: `122/122` checks pass
- `python3 real_world_functional_test.py`: `113/113` workflow steps pass
- `npm run test:e2e`: `17/17` browser tests pass

Use the fast baseline before small edits:

```bash
python3 docs/validate_docs.py
python3 -m py_compile web_ui.py tests/test_web_ui_security.py docs/validate_docs.py
python3 -m unittest discover -s tests -p 'test_*.py'
git diff --check
```

Use the full baseline before releases:

```bash
python3 docs/validate_docs.py
python3 -m py_compile web_ui.py tests/test_web_ui_security.py docs/validate_docs.py
for f in webui/js/*.js e2e/support/ui.js; do node --check "$f" || exit 1; done
python3 -m unittest discover -s tests -p 'test_*.py'
./.venv-docs/bin/python -m pytest
python3 smoke_test.py
python3 real_world_functional_test.py
npm run test:e2e
git diff --check
```

If `./.venv-docs` is missing, use `python3 -m pytest` after installing development dependencies, or note that the docs virtualenv was unavailable.

## 7. How To Run The App

Direct source run:

```bash
python3 web_ui.py --host 127.0.0.1 --port 8080
```

Open:

```text
http://127.0.0.1:8080
```

Editable install:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[dev,bio]"
genomeforge-web --host 127.0.0.1 --port 8080
```

Important runtime safety:

- Default bind host is loopback.
- Non-loopback hosts require `--allow-remote`.
- JSON POST bodies are capped at 64 MiB by default.
- Use `--max-post-mb N` only for trusted local workflows that genuinely need larger payloads.

Examples:

```bash
python3 web_ui.py --port 8080 --max-post-mb 128
python3 web_ui.py --host 0.0.0.0 --port 8080 --allow-remote
```

Do not expose this server to an untrusted network. It does not provide production-grade authentication, sessions, rate limiting, encrypted-at-rest storage, or regulated electronic-record compliance.

## 8. Architecture Snapshot

Runtime topology:

```text
Browser UI
  -> web_ui.py
    -> backend/* domain handlers
      -> genomeforge_toolkit.py
      -> bio/*
      -> compat/*
      -> collab/*
      -> JSON-backed local storage directories
```

Current storage paths created at runtime:

- `projects/`
- `collections/`
- `shares/`
- `annotation_db/`
- `enzyme_sets/`
- `reference_db/`
- `collab_data/`
- `gel_ladders/`

`gel_ladders/` can be generated by browser tests and is usually cleanup residue unless the user intentionally created custom ladders. Ask before deleting user-created scientific data; generated E2E ladder files may be removed during release cleanup.

## 9. Security And Trust Decisions Already Made

Recent hardening releases established:

- `v0.1.11`: SVG label escaping and browser-side SVG sanitizer hardening.
- `v0.1.12`: local HTTP security headers and a documented local-first security model.
- `v0.1.13`: non-loopback bind guard requiring `--allow-remote`.
- `v0.1.14`: configurable JSON POST body limit with default 64 MiB and HTTP `413` oversized-payload response.

Current server hardening:

- CSP with local scripts only.
- `X-Content-Type-Options: nosniff`.
- `X-Frame-Options: DENY`.
- `Referrer-Policy: no-referrer`.
- `Cross-Origin-Opener-Policy: same-origin`.
- `Permissions-Policy` disables camera, microphone, geolocation, payment, and USB.
- Non-loopback binding is explicit opt-in.
- Oversized POST bodies are rejected before reads.
- Share pages escape stored project metadata.
- Project permission updates require owner authority after initial ownership is established.
- Audit log API is read-only.

Known security non-goals:

- No hosted SaaS tenant isolation.
- No authenticated browser sessions.
- No encrypted-at-rest project store.
- No network-facing access control model.
- No regulated electronic-records compliance claim.

The correct framing is "local-first scientific workbench with defense-in-depth," not "production web service."

## 10. API Surface

The authoritative endpoint list is [docs/API.md](/Users/liux17/Documents/Playground/docs/API.md).

The docs validator checks that [docs/API.md](/Users/liux17/Documents/Playground/docs/API.md) matches the endpoint inventory extracted from [web_ui.py](/Users/liux17/Documents/Playground/web_ui.py).

Do not manually maintain endpoint counts in multiple places unless you also update docs validation expectations.

Current notable workflow domains:

- record conversion and interoperability
- core sequence and translation
- visualization
- restriction enzymes and digest workflows
- primers, PCR, and mutagenesis
- alignment, assembly, and comparative analysis
- annotation, features, references, and RNAi
- cloning and construct design
- genome editing
- gel simulation
- project, collections, sharing, audit, and review

Current inventory marker expected by docs validation:

- `120` documented `/api/*` endpoints plus `GET /share/<share_id>`

## 11. Tutorial And Dataset State

The tutorial is intentionally more than a button walkthrough. It teaches bioinformatics concepts to a computer-science-oriented reader with limited biology background.

Current tutorial state:

- `47` lessons/cases.
- Publication-style HTML and PDF outputs.
- Real-world-inspired training records and derived training variants.
- Biological meaning sections, expected results, interpretation, and common wrong interpretations.
- Screenshot atlas for flagship workflows.
- Concept illustrations for diagnostic digest logic, silent-site engineering, and trace evidence navigation.
- Case bundles under `docs/tutorial/datasets/case_bundles/`.

When tutorial source changes:

```bash
python3 docs/tutorial/generate_tutorial.py
python3 docs/build_tutorial_pdf.py
python3 docs/validate_docs.py
```

If screenshots change:

```bash
npm run tutorial:screenshots
python3 docs/tutorial/generate_tutorial.py
python3 docs/build_tutorial_pdf.py
```

Be careful with page layout. The tutorial has been tuned for US Letter print orientation and double-sided printing; do not revert it to A4 or infinite-scroll assumptions.

## 12. Release Process

Use semantic version tags like `v0.1.17`.

Typical release sequence:

```bash
git status --short
python3 docs/validate_docs.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 smoke_test.py
python3 real_world_functional_test.py
npm run test:e2e
git diff --check
```

Update release metadata:

- `VERSION`
- `package.json`
- `package-lock.json`
- `pyproject.toml`
- `README.md` latest-release link
- validation snapshots in `README.md` and this handoff if test counts changed
- `CHANGELOG.md`
- `docs/releases/vX.Y.Z.md`

Commit and tag:

```bash
git add -u
git add docs/releases/vX.Y.Z.md
git commit -m "Release vX.Y.Z <short summary>"
git ls-remote --tags origin vX.Y.Z
git tag -a vX.Y.Z -m "Genome Forge vX.Y.Z"
```

Build release assets:

```bash
mkdir -p dist
git archive --format=tar.gz --prefix=genomeforge-vX.Y.Z/ -o dist/genomeforge-vX.Y.Z-source.tar.gz HEAD
git archive --format=zip --prefix=genomeforge-vX.Y.Z/ -o dist/genomeforge-vX.Y.Z-source.zip HEAD
shasum -a 256 dist/genomeforge-vX.Y.Z-source.tar.gz dist/genomeforge-vX.Y.Z-source.zip > dist/genomeforge-vX.Y.Z-sha256.txt
```

Push and publish:

```bash
git push origin master
git push origin vX.Y.Z
gh release create vX.Y.Z --repo felizvida/genomeforge --title "Genome Forge vX.Y.Z" --notes-file docs/releases/vX.Y.Z.md dist/genomeforge-vX.Y.Z-source.tar.gz dist/genomeforge-vX.Y.Z-source.zip dist/genomeforge-vX.Y.Z-sha256.txt
gh run list --repo felizvida/genomeforge --branch master --limit 5
gh run view <run-id> --repo felizvida/genomeforge --json status,conclusion,jobs
```

After publishing, verify:

- release URL exists
- assets are uploaded
- GitHub digests match local tar/zip hashes
- CI passes on Python 3.11 and 3.12
- only untracked files are expected `dist/` archives

## 13. Current CI Expectations

GitHub Actions run on push to `master`.

Expected matrix:

- Python 3.11 full leg with docs, unit, smoke, browser E2E, and real-world functional tests.
- Python 3.12 faster compatibility leg with docs and unit checks; heavier browser/functional steps may be skipped.

When a release is pushed, do not call it complete until the new CI run passes.

## 14. Recent Release Context

Recent releases, newest first:

- `v0.1.17`: compatibility audit reports, SBOL conversion, golden migration project, UI compatibility table, 47-case tutorial/book, and expanded validation.
- `v0.1.16`: NGS-lite FASTQ QC/trimming, read mapping, variant evidence, workflow report UI, 46-case tutorial/book, and expanded validation.
- `v0.1.15`: Geneious-inspired annotation transfer and multi-read Sanger consensus, tutorial/book updates, and audit fixes.
- `v0.1.14`: request-size safety, `--max-post-mb`, `413` oversized POST handling, 48-test baseline.
- `v0.1.13`: bind safety, `--allow-remote`, deterministic E2E output waits.
- `v0.1.12`: local HTTP security headers and security model docs.
- `v0.1.11`: SVG sanitizer and SVG/text escaping hardening.
- `v0.1.10`: Learning Mode, evidence-to-decision cards, tutorial teaching expansion, scoped minimap pointer handling.

Use [CHANGELOG.md](/Users/liux17/Documents/Playground/CHANGELOG.md) for older details.

## 15. Known Constraints And Risks

Architecture:

- `web_ui.py` is now compact, but it still owns stdlib HTTP serving and top-level route dispatch.
- Backend logic is split into domains, but not yet a framework-backed API with formal request schemas.
- Browser code is split into modules by workflow but still uses plain global state.
- There is no TypeScript, bundler, component system, or state model.

Biology/product:

- Some algorithms are intentionally heuristic.
- Some external tool workflows depend on optional packages or command-line tools.
- Do not overclaim parity with commercial products; present Genome Forge as its own local-first workbench.

Security:

- Local hardening is meaningful, but this is not a network-exposed multi-user app.
- Removing `style-src 'unsafe-inline'` from CSP remains a future cleanup because dynamic panels and share pages still rely on inline styling.

Docs:

- Tutorial PDF/HTML are generated artifacts; update source and rebuild rather than editing generated output by hand when possible.
- Keep the case count at `47` unless intentionally changing tutorial scope.
- Keep paper size US Letter for print material.

## 16. Recommended Next Work

Highest-leverage next steps:

1. Frontend state cleanup: isolate global UI state into a small app-state module and add regression tests around state transitions.
2. CSP cleanup: reduce inline style dependency so `style-src 'unsafe-inline'` can eventually be removed.
3. API request schema layer: add typed request validators for high-risk endpoints before deeper server framework migration.
4. Project data safety: add backup/export/import workflow tests for `projects/`, `shares/`, `collections/`, and `collab_data/`.
5. Tutorial maintenance: keep screenshots aligned with any UI changes and rebuild PDF after tutorial edits.
6. Capability docs generation: derive endpoint/capability tables from code to reduce hand-maintained drift.

If the user says "continue" without specifics, a pragmatic default is:

```text
Pick the highest-leverage hardening or maintainability item, implement it with tests, update docs, run validation, and ask only if a release/push decision is ambiguous.
```

## 17. Do-Not-Do List

- Do not revert user changes.
- Do not delete untracked `dist/` release archives unless explicitly asked.
- Do not use destructive git commands like `git reset --hard` or `git checkout --` unless explicitly approved.
- Do not reintroduce references to products Genome Forge used to be compared against as if Genome Forge were a clone.
- Do not change tutorial print format back to A4.
- Do not claim hosted security properties the project does not have.
- Do not hand-edit generated tutorial PDF/HTML without considering the generator source.

## 18. Quick Restart Checklist

Use this when opening a new thread:

```bash
cd /Users/liux17/Documents/Playground
git status --short
git log -1 --oneline
cat VERSION
python3 docs/validate_docs.py
python3 -m unittest discover -s tests -p 'test_*.py'
```

If continuing implementation:

```bash
python3 smoke_test.py
python3 real_world_functional_test.py
npm run test:e2e
```

If those pass, the project is at a known-good baseline.

## 19. One-Screen Summary

Genome Forge is a local-first DNA/bioinformatics workbench at release `v0.1.17`. It has broad feature coverage, real-data tutorial material, Geneious-inspired annotation transfer and Sanger consensus workflows, NGS-lite FASTQ/read-mapping/variant evidence, import/export compatibility auditing, SBOL conversion, project sharing/review workflows, and a modern browser UI. The latest engineering emphasis has been practical bench-facing workflow depth plus hardening: SVG sanitization, security headers, loopback bind safety, bounded POST reads, audit-backed edge-case fixes, round-trip migration trust, and test-backed replacement-phase reporting. The main remaining work is structural modernization: frontend state isolation, stricter CSP without inline-style dependency, typed API validation, and deeper test-backed decomposition.
