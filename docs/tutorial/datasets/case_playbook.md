# Genome Forge Training Case Playbook

## Case A: Restriction Mapping

1. Load `pUC19_MCS`.
2. Run map + digest using `mapping_panel`.
3. Compare standard vs methylation-aware digest output.

Expected:
- Distinct cut map for EcoRI/BamHI/HindIII/XbaI/PstI/KpnI.
- Blocked-cut changes when motifs are marked methylated.

## Case B: Primer + PCR

1. Load `EGFP_CDS`.
2. Use `primer_training.egfp_target` to design primers.
3. Run specificity and ranking against background records.
4. Simulate PCR and gel lanes.

Expected:
- Ranked primer pairs with risk score.
- Dominant expected amplicon in gel lane simulation.

## Case C: Ligation Strategy

1. Use ligation enzymes from `enzyme_panels.ligation_panel`.
2. Run cloning compatibility and ligation simulation.
3. Focus top probability product and inspect junction diagnostics.

Expected:
- At least one desired product candidate with interpretable probability.

## Case D: Interop + Trace

1. Export DNA container and re-import.
2. Import AB1 payload (or synthetic fallback sequence).
3. Run trace summary, align, base edit, and consensus.

Expected:
- Roundtrip preserves sequence identity.
- Consensus reflects edited base and quality thresholding.

## Case E: CRISPR + HDR

1. Load `BRAF_exon15_fragment`.
2. Run gRNA design (`NGG`, 20 nt spacer).
3. Run off-target scan against configured backgrounds.
4. Generate HDR donor using provided edit coordinates.

Expected:
- Candidate list with efficiency scores.
- Off-target report and donor template generated.

## Case F: Collaboration + Review

1. Create workspace and assign roles.
2. Save project and fetch audit log.
3. Submit review and approve with reviewer role.

Expected:
- Audit entries for save/review operations.
- Review transitions to `approved`.
