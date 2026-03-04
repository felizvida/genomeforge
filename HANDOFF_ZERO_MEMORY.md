# Genome Forge Zero-Memory Handoff

This document is designed so a new engineer can resume work with no prior context.

## 1. What This Project Is

Genome Forge is a local DNA/plasmid workbench implemented as:

- `genomeforge_toolkit.py`: core sequence engine + CLI utilities
- `web_ui.py`: HTTP server exposing JSON APIs and serving web UI
- `webui/index.html`: single-page frontend
- `smoke_test.py`: extensive automated regression test suite

Current state: broad feature-complete implementation with all coverage rows marked `Implemented` in `FEATURE_COVERAGE.md`.

## 2. Current Repo State

Key files:

- `/Users/liux17/Documents/Playground/genomeforge_toolkit.py`
- `/Users/liux17/Documents/Playground/web_ui.py`
- `/Users/liux17/Documents/Playground/webui/index.html`
- `/Users/liux17/Documents/Playground/README.md`
- `/Users/liux17/Documents/Playground/FEATURE_COVERAGE.md`
- `/Users/liux17/Documents/Playground/smoke_test.py`

Git:

- Branch: `master`
- Remote: `origin -> git@github.com:felizvida/genomeforge.git`
- Latest known pushed commit: `3b91271`

## 3. How to Run

Start server:

```bash
python3 web_ui.py --host 127.0.0.1 --port 8080
```

Open UI:

- `http://127.0.0.1:8080`

Run full regression:

```bash
python3 smoke_test.py
```

Verbose regression:

```bash
python3 smoke_test.py --verbose
```

Expected regression output shape:

```json
{
  "total_tests": 72,
  "passed": 72,
  "failed": 0,
  "failures": []
}
```

## 4. High-Level Architecture

### 4.1 Backend (`web_ui.py`)

- Uses Python stdlib `ThreadingHTTPServer`.
- `Handler.do_GET` serves:
  - `/` and `/index.html` -> SPA
  - `/share/<share_id>` -> rendered share viewer HTML
- `Handler.do_POST` routes all API endpoints.
- `parse_record(payload)` interprets sequence input as:
  - FASTA
  - GenBank
  - EMBL
  - raw sequence

### 4.2 Core Sequence Engine (`genomeforge_toolkit.py`)

- Sequence parsing/sanitization
- restriction digest
- map SVG generation
- translation/ORF
- PCR/primers/codon optimization
- feature management structures

### 4.3 Frontend (`webui/index.html`)

- Single file HTML/CSS/JS
- Tabbed controls for editing, analysis, cloning, advanced workflows
- Interactive SVG views:
  - map zoom/pan
  - sequence track + minimap brush/handles
  - star activity risk panel
  - ligation pathway graph
  - history graph
- Inspector panel for click selections
- Local persisted undo/redo via `localStorage`

## 5. API Surface (Backend)

All APIs are POST JSON unless noted.

Core:

- `/api/info`
- `/api/translate`
- `/api/translated-features`
- `/api/translated-feature-edit`
- `/api/protein-edit`
- `/api/sequence-edit`
- `/api/reverse-translate`

Restriction/enzymes:

- `/api/digest`
- `/api/digest-advanced`
- `/api/star-activity-scan`
- `/api/enzyme-scan`
- `/api/enzyme-info`
- `/api/enzyme-set-save`
- `/api/enzyme-set-list`
- `/api/enzyme-set-predefined`
- `/api/enzyme-set-load`
- `/api/enzyme-set-delete`

Primers/PCR:

- `/api/primers`
- `/api/primer-diagnostics`
- `/api/pcr`
- `/api/pcr-gel-lanes`

Alignment/assembly:

- `/api/pairwise-align` (DNA + protein mode)
- `/api/multi-align`
- `/api/msa` (progressive + adapters for MAFFT/MUSCLE/ClustalW/T-Coffee)
- `/api/alignment-consensus`
- `/api/alignment-heatmap-svg`
- `/api/phylo-tree`
- `/api/contig-assemble`
- `/api/cdna-map`

Map/tracks:

- `/api/map`
- `/api/sequence-tracks`

Annotation/features/search:

- `/api/orfs`
- `/api/motif`
- `/api/search-entities`
- `/api/annotate-auto`
- `/api/annot-db-save`
- `/api/annot-db-list`
- `/api/annot-db-load`
- `/api/annot-db-apply`
- `/api/features-list`
- `/api/features-add`
- `/api/features-update`
- `/api/features-delete`

Cloning workflows:

- `/api/gibson-assemble`
- `/api/golden-gate`
- `/api/gateway-cloning`
- `/api/topo-cloning`
- `/api/ta-gc-cloning`
- `/api/cloning-compatibility`
- `/api/ligation-sim`
- `/api/in-fusion`
- `/api/overlap-extension-pcr`

Gel:

- `/api/gel-sim`
- `/api/gel-marker-sets`

Data/project/share:

- `/api/project-save`
- `/api/project-load`
- `/api/project-list`
- `/api/project-delete`
- `/api/project-history-graph`
- `/api/project-history-svg`
- `/api/collection-save`
- `/api/collection-load`
- `/api/collection-list`
- `/api/collection-delete`
- `/api/collection-add-project`
- `/api/share-create`
- `/api/share-load`
- `GET /share/<share_id>`

## 6. Data Storage Layout (Generated at Runtime)

Directories created in project root:

- `projects/`
- `collections/`
- `shares/`
- `annotation_db/`
- `enzyme_sets/`

Each stores JSON files keyed by safe names/ids.

Note: `smoke_test.py` removes these directories after test runs.

## 7. UI Interaction Features to Know

Map/track:

- wheel zoom + drag pan
- reset controls
- click feature/cut/codon to inspect

Track minimap:

- drag brush to move window
- drag left/right handles to resize window
- click minimap to recenter

Ligation graph:

- probability-weighted edges
- filter modes (all/desired/byproducts)
- click nodes for diagnostics

Star activity:

- summary + enzyme burden table
- click hit to center sequence track on cut

## 8. Test Strategy and Expectations

### 8.1 Fast sanity checks

```bash
python3 -m py_compile web_ui.py genomeforge_toolkit.py
python3 smoke_test.py
```

### 8.2 What smoke test covers

- 72 checks across endpoint families and lifecycle chains.
- Ensures:
  - valid JSON schemas/keys
  - API behavior across cloning/alignment/editing/data persistence
  - share page rendering works
  - no regression in broad surface area

### 8.3 If smoke fails

1. Re-run verbose:

```bash
python3 smoke_test.py --verbose
```

2. Reproduce failing API with curl/json payload from script.
3. Fix backend first, then re-run full suite.

## 9. Known Constraints / Caveats

- Many biological algorithms are simplified approximations, not full proprietary parity.
- External aligners (MAFFT/MUSCLE/ClustalW/T-Coffee) are optional; code falls back when binaries missing.
- Some workflows depend on realistic payload constraints (e.g., TA/TOPO overhang assumptions).

## 10. Next Work Suggestions (if continuing)

Potential high-value follow-ups:

1. Add formal unit tests in `pytest` alongside `smoke_test.py`.
2. Split `web_ui.py` into modules (routing, services, renderers) to reduce monolith size.
3. Add OpenAPI schema generation for API contracts.
4. Add import/export adapters for additional real-world sequence formats.
5. Add authentication/access control if deploying beyond local usage.

## 11. Quick Restart Checklist

When resuming later:

1. `git pull`
2. `python3 -m py_compile web_ui.py genomeforge_toolkit.py`
3. `python3 smoke_test.py`
4. `python3 web_ui.py --port 8080`
5. Open UI and validate:
   - map/track interactions
   - ligation graph
   - star activity panel
   - share page flow

If all pass, you are at a stable baseline.
