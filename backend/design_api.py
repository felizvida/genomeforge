from __future__ import annotations

import json
from typing import Any, Callable, Dict

from bio.crispr_design import crispr_offtarget_scan, design_grna_candidates, design_hdr_template
from bio.primer_specificity import primer_specificity_report, rank_primer_pairs
from genomeforge_toolkit import SequenceRecord


RecordGetter = Callable[[], SequenceRecord]


def _background_sequences(payload: Dict[str, Any], get_record: RecordGetter) -> list[dict[str, str]]:
    backgrounds = payload.get("background_sequences", [])
    if isinstance(backgrounds, str):
        backgrounds = [item.strip() for item in backgrounds.splitlines() if item.strip()]
    if not backgrounds:
        rec = get_record()
        return [{"name": rec.name, "sequence": rec.sequence}]
    return backgrounds


def handle_design_endpoint(path: str, payload: Dict[str, Any], get_record: RecordGetter) -> Dict[str, Any] | None:
    if path == "/api/primer-specificity":
        return primer_specificity_report(
            forward=str(payload.get("forward", "")),
            reverse=str(payload.get("reverse", "")),
            background_sequences=_background_sequences(payload, get_record),
            max_mismatch=int(payload.get("max_mismatch", 1)),
            min_amplicon_bp=int(payload.get("min_amplicon_bp", 80)),
            max_amplicon_bp=int(payload.get("max_amplicon_bp", 3000)),
        )

    if path == "/api/primer-rank":
        candidates = payload.get("candidates", [])
        if isinstance(candidates, str):
            candidates = json.loads(candidates)
        return rank_primer_pairs(
            candidates=[dict(item) for item in candidates if isinstance(item, dict)],
            background_sequences=_background_sequences(payload, get_record),
            max_mismatch=int(payload.get("max_mismatch", 1)),
        )

    if path == "/api/grna-design":
        sequence = str(payload.get("sequence", ""))
        if not sequence.strip():
            sequence = get_record().sequence
        return design_grna_candidates(
            sequence=sequence,
            pam=str(payload.get("pam", "NGG")),
            spacer_len=int(payload.get("spacer_len", 20)),
            max_candidates=int(payload.get("max_candidates", 200)),
        )

    if path == "/api/crispr-offtarget":
        return crispr_offtarget_scan(
            guide=str(payload.get("guide", "")),
            background_sequences=_background_sequences(payload, get_record),
            max_mismatch=int(payload.get("max_mismatch", 3)),
        )

    if path == "/api/hdr-template":
        sequence = str(payload.get("sequence", ""))
        if not sequence.strip():
            sequence = get_record().sequence
        return design_hdr_template(
            sequence=sequence,
            edit_start_1based=int(payload.get("edit_start_1based", 1)),
            edit_end_1based=int(payload.get("edit_end_1based", 1)),
            edit_sequence=str(payload.get("edit_sequence", "")),
            left_arm_bp=int(payload.get("left_arm_bp", 60)),
            right_arm_bp=int(payload.get("right_arm_bp", 60)),
        )

    return None
