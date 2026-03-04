# P0 Implementation Notes (Interop + Trace Core)

Date: 2026-03-04

## Delivered

1. `compat/` package:
   - `compat/dna_format.py`
   - `compat/ab1_format.py`
2. `bio/` package:
   - `bio/trace_tools.py`
3. New API endpoints in `web_ui.py`:
   - `/api/import-dna`
   - `/api/export-dna`
   - `/api/import-ab1`
   - `/api/trace-summary`
   - `/api/trace-align`
   - `/api/trace-edit-base`
   - `/api/trace-consensus`
4. Web UI tab:
   - `Trace/Interop` panel in `webui/index.html`
5. Test coverage:
   - `smoke_test.py` now exercises DNA container roundtrip + trace workflow.
   - `real_world_functional_test.py` includes DNA + trace checks.

## Current Scope

1. DNA container:
   - Implements Genome Forge binary container format `genomeforge.dna/1`.
   - Supports import/export via base64 API payloads.
   - Supports JSON-canonical fallback import path for portability/testing.
2. AB1:
   - ABIF reader supports core fields (basecalls, quality, positions, traces).
   - Synthetic trace generation path supported for deterministic tests/demo.
3. Trace editing/alignment:
   - In-memory trace cache with ID-based workflow.
   - Global alignment for trace-to-reference mapping.
   - Consensus generation with quality threshold masking.

## Known Limitation

1. Native proprietary SnapGene binary `.dna` parsing is still limited.
   - Parser explicitly returns clear error for unsupported SnapGene-native binary payload.
