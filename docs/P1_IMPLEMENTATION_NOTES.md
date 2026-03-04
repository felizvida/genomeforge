# P1 Implementation Notes (Primer Specificity + CRISPR Helpers)

Date: 2026-03-04

## Delivered

1. New bio modules:
   - `bio/primer_specificity.py`
   - `bio/crispr_design.py`
2. New API endpoints:
   - `/api/primer-specificity`
   - `/api/primer-rank`
   - `/api/grna-design`
   - `/api/crispr-offtarget`
   - `/api/hdr-template`
3. UI updates:
   - Added primer specificity, primer ranking, CRISPR design/off-target, and HDR template controls in `webui/index.html` (Advanced tab).
4. Validation updates:
   - `smoke_test.py` expanded with P1 API checks.
   - `real_world_functional_test.py` expanded with P1 workflow checks.
   - Regenerated real-world test report JSON/Markdown artifacts.

## Scope

1. Primer specificity:
   - Local background scanning with mismatch tolerance.
   - Predicted product/off-target counts.
   - Pair risk scoring and candidate ranking.
2. CRISPR:
   - gRNA candidate generation for PAM model (default `NGG`).
   - Basic efficiency heuristic score.
   - Off-target scan across supplied backgrounds.
3. HDR:
   - Donor template generation with configurable homology arm lengths.
   - PAM-disruption suggestion hints around edit locus.

## Limitations

1. Off-target scoring is heuristic and local (no genome-indexed mapper integration yet).
2. gRNA efficiency model is simplified (not ML-calibrated).
3. HDR silent mutation suggestion is advisory and not codon-context optimized.
