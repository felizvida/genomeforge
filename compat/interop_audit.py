from __future__ import annotations

import base64
from typing import Any, Callable, Dict, Iterable, List

from canonical_schema import canonical_to_record, canonical_to_payload, infer_source_format, record_to_canonical
from compat.dna_format import export_dna_container, import_dna_container
from compat.sbol_format import feature_translation, looks_like_sbol, parse_sbol, to_sbol
from genomeforge_toolkit import (
    Feature,
    SequenceRecord,
    parse_fasta,
    parse_genbank,
    sanitize_sequence,
    to_fasta,
    to_genbank,
)


DEFAULT_AUDIT_FORMATS = ["genbank", "sbol", "genomeforge_dna", "fasta"]

EGFP_CDS = (
    "ATGGTGAGCAAGGGCGAGGAGCTGTTCACCGGGGTGGTGCCCATCCTGGTCGAGCTGGACGGCGACGTAAACGGCCACAAG"
    "TTCAGCGTGTCCGGCGAGGGCGAGGGCGAGGGCGATGCCACCTACGGCAAGCTGACCCTGAAGTTCATCTGCACCACCGGCA"
    "AGCTGCCCGTGCCCTGGCCCACCCTCGTGACCACCCTGACCTACGGCGTGCAGTGCTTCAGCCGCTACCCCGACCACATGA"
    "AGCAGCACGACTTCTTCAAGTCCGCCATGCCCGAAGGCTACGTCCAGGAGCGCACCATCTTCTTCAAGGACGACGGCAACT"
    "ACAAGACCCGCGCCGAGGTGAAGTTCGAGGGCGACACCCTGGTGAACCGCATCGAGCTGAAGGGCATCGACTTCAAGGAGG"
    "ACGGCAACATCCTGGGGCACAAGCTGGAGTACAACTACAACAGCCACAACGTCTATATCATGGCCGACAAGCAGAAGAACG"
    "GCATCAAGGTGAACTTCAAGATCCGCCACAACATCGAGGACGGCAGCGTGCAGCTCGCCGACCACTACCAGCAGAACACCC"
    "CCATCGGCGACGGCCCCGTGCTGCTGCCCGACAACCACTACCTGAGCACCCAGTCCAAGCTGAGCAAAGACCCCAACGAGA"
    "AGCGCGATCACATGGTCCTGCTGGAGTTCGTGACCGCCGCCGGGATCACTCTCGGCATGGACGAGCTGTACAAGTAA"
)
PUC19_MCS = "GAATTCGAGCTCGGTACCCGGGGATCCTCTAGAGTCGACCTGCAGGCATGCAAGCTT"
LAC_PROMOTER = "TTTACACTTTATGCTTCCGGCTCGTATGTTGTGTGGAATTGTGAGCGGATAACAATT"
SYN_TERMINATOR = "GCTAGTTATTGCTCAGCGGTGGCAGCAGCCAACTCAGCTTCCTTTCGGGCTTTGTTAGCAGCCGGATC"


RecordGetter = Callable[[], SequenceRecord]


def _feature_dicts(record: SequenceRecord) -> List[Dict[str, Any]]:
    return [{"key": f.key, "location": f.location, "qualifiers": dict(f.qualifiers)} for f in record.features]


def _payload_to_record(payload: Dict[str, Any]) -> SequenceRecord:
    if isinstance(payload.get("canonical_record"), dict):
        return canonical_to_record(payload["canonical_record"])

    if str(payload.get("dna_base64", "")).strip():
        raw = base64.b64decode(str(payload["dna_base64"]).encode("ascii"), validate=True)
        imported = import_dna_container(raw)
        if isinstance(imported.get("canonical_record"), dict):
            return canonical_to_record(imported["canonical_record"])
        if isinstance(imported.get("payload"), dict):
            return _payload_to_record(imported["payload"])
        raise ValueError("DNA import did not produce a record")

    content = str(payload.get("content", "") or "").strip()
    name = str(payload.get("name", "Untitled") or "Untitled").strip() or "Untitled"
    topology = str(payload.get("topology", "linear") or "linear").strip().lower()
    if topology not in {"linear", "circular"}:
        topology = "linear"

    if looks_like_sbol(content):
        record = parse_sbol(content)
    elif content.startswith(">"):
        record = parse_fasta(content)
    elif content.lstrip().startswith("LOCUS"):
        record = parse_genbank(content)
    elif content:
        record = SequenceRecord(name=name, sequence=sanitize_sequence(content), topology=topology)
    else:
        raise ValueError("Record content is empty")

    if payload.get("name"):
        record.name = name
    if payload.get("topology"):
        record.topology = topology
    if isinstance(payload.get("features"), list):
        record.features = [
            Feature(
                key=str(item.get("key", "misc_feature")),
                location=str(item.get("location", "")),
                qualifiers={str(k): str(v) for k, v in dict(item.get("qualifiers", {})).items()},
            )
            for item in payload["features"]
            if isinstance(item, dict)
        ]
    return record


def _source_format(item: Dict[str, Any], record: SequenceRecord) -> str:
    explicit = str(item.get("format", "") or item.get("source_format", "")).strip().lower()
    if explicit:
        return explicit
    if str(item.get("dna_base64", "")).strip():
        return "dna"
    content = str(item.get("content", "") or "")
    if looks_like_sbol(content):
        return "sbol"
    inferred = infer_source_format(content)
    if inferred == "unknown" and record.features:
        return "payload"
    return inferred


def records_from_payload(payload: Dict[str, Any], get_record: RecordGetter) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    files = payload.get("files")
    if isinstance(files, list) and files:
        for idx, item in enumerate(files, start=1):
            if not isinstance(item, dict):
                continue
            data = dict(item)
            if data.get("content_base64") and not data.get("content") and not data.get("dna_base64"):
                if str(data.get("format", "")).lower() == "dna" or str(data.get("filename", "")).lower().endswith(".dna"):
                    data["dna_base64"] = str(data["content_base64"])
                else:
                    raw = base64.b64decode(str(data["content_base64"]).encode("ascii"), validate=True)
                    data["content"] = raw.decode("utf-8")
            rec = _payload_to_record(data)
            rows.append({"record": rec, "source_format": _source_format(data, rec), "source_id": str(data.get("filename", "") or idx)})
        if rows:
            return rows

    records = payload.get("records")
    if isinstance(records, list) and records:
        for idx, item in enumerate(records, start=1):
            if not isinstance(item, dict):
                continue
            rec = _payload_to_record(item)
            rows.append({"record": rec, "source_format": _source_format(item, rec), "source_id": str(item.get("record_id", "") or idx)})
        if rows:
            return rows

    rec = get_record()
    return [{"record": rec, "source_format": _source_format(payload, rec), "source_id": str(payload.get("record_id", "") or "current")}]


def _normalize_format(fmt: str) -> str:
    clean = str(fmt or "").strip().lower().replace("-", "_")
    aliases = {"gb": "genbank", "gbk": "genbank", "dna": "genomeforge_dna", "gf_dna": "genomeforge_dna"}
    return aliases.get(clean, clean)


def target_formats(payload: Dict[str, Any]) -> List[str]:
    raw = payload.get("target_formats", payload.get("formats", DEFAULT_AUDIT_FORMATS))
    if isinstance(raw, str):
        items = [item.strip() for item in raw.split(",")]
    elif isinstance(raw, list):
        items = [str(item).strip() for item in raw]
    else:
        items = list(DEFAULT_AUDIT_FORMATS)
    out: List[str] = []
    for item in items:
        fmt = _normalize_format(item)
        if fmt and fmt not in out:
            out.append(fmt)
    return out or list(DEFAULT_AUDIT_FORMATS)


def _export_record(record: SequenceRecord, source_format: str, source_id: str, fmt: str) -> Dict[str, Any]:
    if fmt == "fasta":
        return {"format": "fasta", "content": to_fasta(record)}
    if fmt == "genbank":
        return {"format": "genbank", "content": to_genbank(record)}
    if fmt == "sbol":
        return {"format": "sbol", "content": to_sbol(record)}
    if fmt == "genomeforge_dna":
        canon = record_to_canonical(record, source_format=source_format, source_id=source_id)
        blob = export_dna_container(
            canon,
            metadata={"name": record.name, "topology": record.topology, "created_by": "genomeforge"},
        )
        return {"format": "genomeforge_dna", "content_base64": base64.b64encode(blob).decode("ascii"), "bytes": len(blob)}
    raise ValueError(f"Unsupported compatibility export format: {fmt}")


def _import_exported(exported: Dict[str, Any]) -> SequenceRecord:
    fmt = exported["format"]
    if fmt == "fasta":
        return parse_fasta(str(exported.get("content", "")))
    if fmt == "genbank":
        return parse_genbank(str(exported.get("content", "")))
    if fmt == "sbol":
        return parse_sbol(str(exported.get("content", "")))
    if fmt == "genomeforge_dna":
        raw = base64.b64decode(str(exported.get("content_base64", "")).encode("ascii"), validate=True)
        imported = import_dna_container(raw)
        if isinstance(imported.get("canonical_record"), dict):
            return canonical_to_record(imported["canonical_record"])
    raise ValueError(f"Cannot import exported format: {fmt}")


def _feature_signature(feature: Feature) -> str:
    return f"{feature.key}|{feature.location}"


def _cds_translations(record: SequenceRecord) -> Dict[str, str]:
    rows: Dict[str, str] = {}
    for feature in record.features:
        if feature.key.lower() != "cds":
            continue
        label = feature.qualifiers.get("label") or feature.qualifiers.get("gene") or _feature_signature(feature)
        rows[f"{label}|{feature.location}"] = feature_translation(record, feature)
    return rows


def compare_records(before: SequenceRecord, after: SequenceRecord, fmt: str) -> Dict[str, Any]:
    before_by_sig = {_feature_signature(feature): feature for feature in before.features}
    after_by_sig = {_feature_signature(feature): feature for feature in after.features}
    missing_feature_sigs = sorted(set(before_by_sig) - set(after_by_sig))

    missing_qualifiers: List[Dict[str, str]] = []
    for sig, before_feature in before_by_sig.items():
        after_feature = after_by_sig.get(sig)
        if not after_feature:
            continue
        for key, value in before_feature.qualifiers.items():
            if after_feature.qualifiers.get(key) != value:
                missing_qualifiers.append({"feature": sig, "qualifier": key, "expected": value, "observed": after_feature.qualifiers.get(key, "")})

    before_translations = _cds_translations(before)
    after_translations = _cds_translations(after)
    translation_mismatches = [
        key for key, value in before_translations.items() if after_translations.get(key) != value
    ]

    checks = {
        "sequence_preserved": before.sequence == after.sequence,
        "length_preserved": before.length == after.length,
        "topology_preserved": before.topology == after.topology,
        "features_survive": not missing_feature_sigs,
        "coordinates_stable": not missing_feature_sigs,
        "qualifiers_preserved": not missing_qualifiers,
        "translations_match": not translation_mismatches,
    }

    warnings: List[str] = []
    lost_metadata: List[Dict[str, Any]] = []
    if fmt == "fasta" and before.features:
        warnings.append("FASTA preserves sequence but does not preserve feature annotations, qualifiers, or topology.")
    if fmt == "genomeforge_dna":
        warnings.append("Portable Genome Forge DNA export is not a proprietary SnapGene .dna writer.")
    if not checks["sequence_preserved"]:
        lost_metadata.append({"field": "sequence", "before": before.length, "after": after.length})
    if not checks["topology_preserved"]:
        lost_metadata.append({"field": "topology", "before": before.topology, "after": after.topology})
    if missing_feature_sigs:
        lost_metadata.append({"field": "features", "missing": missing_feature_sigs[:20], "missing_count": len(missing_feature_sigs)})
    if missing_qualifiers:
        lost_metadata.append({"field": "qualifiers", "missing": missing_qualifiers[:20], "missing_count": len(missing_qualifiers)})
    if translation_mismatches:
        lost_metadata.append({"field": "cds_translations", "mismatches": translation_mismatches[:20], "mismatch_count": len(translation_mismatches)})

    export_safe = all(checks.values())
    return {
        "checks": checks,
        "warnings": warnings,
        "lost_metadata": lost_metadata,
        "imported_cleanly": True,
        "export_safe": export_safe,
        "status": "export_safe" if export_safe else "needs_review",
        "before": {"length": before.length, "topology": before.topology, "feature_count": len(before.features)},
        "after": {"length": after.length, "topology": after.topology, "feature_count": len(after.features)},
        "missing_feature_count": len(missing_feature_sigs),
        "missing_qualifier_count": len(missing_qualifiers),
        "translation_mismatch_count": len(translation_mismatches),
    }


def audit_record(record: SequenceRecord, formats: Iterable[str], source_format: str = "payload", source_id: str = "") -> Dict[str, Any]:
    round_trips: List[Dict[str, Any]] = []
    for fmt in formats:
        try:
            exported = _export_record(record, source_format, source_id, fmt)
            imported = _import_exported(exported)
            comparison = compare_records(record, imported, fmt)
            round_trips.append(
                {
                    "format": fmt,
                    "status": comparison["status"],
                    "imported_cleanly": True,
                    "export_safe": comparison["export_safe"],
                    "warnings": comparison["warnings"],
                    "lost_metadata": comparison["lost_metadata"],
                    "checks": comparison["checks"],
                    "before": comparison["before"],
                    "after": comparison["after"],
                    "artifact_bytes": int(exported.get("bytes", len(str(exported.get("content", ""))))),
                    "missing_feature_count": comparison["missing_feature_count"],
                    "missing_qualifier_count": comparison["missing_qualifier_count"],
                    "translation_mismatch_count": comparison["translation_mismatch_count"],
                }
            )
        except Exception as exc:  # noqa: BLE001
            round_trips.append(
                {
                    "format": fmt,
                    "status": "needs_review",
                    "imported_cleanly": False,
                    "export_safe": False,
                    "warnings": [str(exc)],
                    "lost_metadata": [{"field": "round_trip", "error": str(exc)}],
                    "checks": {
                        "sequence_preserved": False,
                        "length_preserved": False,
                        "topology_preserved": False,
                        "features_survive": False,
                        "coordinates_stable": False,
                        "qualifiers_preserved": False,
                        "translations_match": False,
                    },
                }
            )

    return {
        "name": record.name,
        "length": record.length,
        "topology": record.topology,
        "feature_count": len(record.features),
        "source_format": source_format,
        "source_id": source_id,
        "recommended_formats": [row["format"] for row in round_trips if row.get("export_safe")],
        "round_trips": round_trips,
    }


def compatibility_audit(payload: Dict[str, Any], get_record: RecordGetter) -> Dict[str, Any]:
    formats = target_formats(payload)
    records = []
    source_import_errors: List[str] = []
    try:
        source_records = records_from_payload(payload, get_record)
    except Exception as exc:  # noqa: BLE001
        source_records = []
        source_import_errors.append(str(exc))

    for row in source_records:
        records.append(
            audit_record(
                row["record"],
                formats=formats,
                source_format=str(row.get("source_format", "payload")),
                source_id=str(row.get("source_id", "")),
            )
        )

    status_counts: Dict[str, int] = {}
    warning_count = 0
    lost_metadata_count = 0
    warnings: List[Dict[str, Any]] = []
    lost_metadata: List[Dict[str, Any]] = []
    for rec in records:
        for rt in rec["round_trips"]:
            status_counts[rt["status"]] = status_counts.get(rt["status"], 0) + 1
            warning_count += len(rt.get("warnings", []))
            lost_metadata_count += len(rt.get("lost_metadata", []))
            for warning in rt.get("warnings", []):
                warnings.append({"record": rec["name"], "format": rt["format"], "message": warning})
            for item in rt.get("lost_metadata", []):
                lost_metadata.append({"record": rec["name"], "format": rt["format"], **dict(item)})

    imported_cleanly = not source_import_errors and all(rt["imported_cleanly"] for rec in records for rt in rec["round_trips"])
    export_safe = bool(records) and all(any(rt["export_safe"] for rt in rec["round_trips"]) for rec in records)
    needs_review = bool(source_import_errors) or any(rt["status"] != "export_safe" for rec in records for rt in rec["round_trips"])
    status = "needs_review" if needs_review else "export_safe"

    return {
        "status": status,
        "imported_cleanly": imported_cleanly,
        "export_safe": export_safe,
        "needs_review": needs_review,
        "warnings": [{"record": "", "format": "source_import", "message": msg} for msg in source_import_errors] + warnings,
        "lost_metadata": lost_metadata,
        "formats": formats,
        "record_count": len(records),
        "records": records,
        "summary": {
            "record_count": len(records),
            "round_trip_count": sum(len(rec["round_trips"]) for rec in records),
            "status_counts": status_counts,
            "warning_count": warning_count + len(source_import_errors),
            "lost_metadata_count": lost_metadata_count,
            "records_with_export_safe_path": sum(1 for rec in records if rec.get("recommended_formats")),
        },
    }


def _feature(key: str, start: int, end: int, **qualifiers: str) -> Feature:
    return Feature(key=key, location=f"{start}..{end}", qualifiers={k: str(v) for k, v in qualifiers.items()})


def _with_offset(offset: int, key: str, start: int, end: int, **qualifiers: str) -> Feature:
    return _feature(key, offset + start, offset + end, **qualifiers)


def _mutate(seq: str, pos_1based: int, base: str) -> str:
    return seq[: pos_1based - 1] + base + seq[pos_1based:]


def golden_project_records() -> List[SequenceRecord]:
    plasmid_seq = LAC_PROMOTER + PUC19_MCS + EGFP_CDS + SYN_TERMINATOR
    mcs_start = len(LAC_PROMOTER) + 1
    cds_start = len(LAC_PROMOTER) + len(PUC19_MCS) + 1
    term_start = cds_start + len(EGFP_CDS)
    plasmid = SequenceRecord(
        name="pGF_EGFP_expression",
        sequence=plasmid_seq,
        topology="circular",
        features=[
            _feature("promoter", 1, len(LAC_PROMOTER), label="lac promoter", note="bench plasmid promoter"),
            _feature("misc_feature", mcs_start, mcs_start + len(PUC19_MCS) - 1, label="pUC19 MCS", note="EcoRI/BamHI/HindIII cloning cassette"),
            _feature("CDS", cds_start, cds_start + len(EGFP_CDS) - 1, label="EGFP reporter CDS", gene="egfp", codon_start="1", product="enhanced GFP"),
            _feature("terminator", term_start, term_start + len(SYN_TERMINATOR) - 1, label="synthetic terminator"),
            _with_offset(cds_start - 1, "primer_bind", 1, 22, label="EGFP_F_seq_primer"),
            _with_offset(cds_start - 1, "primer_bind", len(EGFP_CDS) - 24, len(EGFP_CDS), label="EGFP_R_seq_primer"),
        ],
    )

    cloning_insert = "GAATTC" + EGFP_CDS[:240] + "GGATCC"
    cloning = SequenceRecord(
        name="EcoRI_BamHI_EGFP_cloning_design",
        sequence=PUC19_MCS + cloning_insert,
        topology="circular",
        features=[
            _feature("misc_feature", 1, len(PUC19_MCS), label="recipient MCS", note="pUC19-style cloning window"),
            _feature("misc_feature", len(PUC19_MCS) + 1, len(PUC19_MCS) + 6, label="EcoRI overhang"),
            _feature("CDS", len(PUC19_MCS) + 7, len(PUC19_MCS) + 246, label="EGFP N-terminal insert", codon_start="1"),
            _feature("misc_feature", len(PUC19_MCS) + 247, len(PUC19_MCS) + 252, label="BamHI overhang"),
        ],
    )

    variant_pos = 199
    edited = SequenceRecord(
        name="EGFP_Y67H_expected_edit",
        sequence=_mutate(EGFP_CDS, variant_pos, "C" if EGFP_CDS[variant_pos - 1] != "C" else "A"),
        topology="linear",
        features=[
            _feature("CDS", 1, len(EGFP_CDS), label="EGFP edited CDS", gene="egfp", codon_start="1", expected_variant=f"{variant_pos}:{EGFP_CDS[variant_pos - 1]}>C"),
            _feature("misc_feature", variant_pos, variant_pos, label="expected Y67H edit", note="training mutation used for compatibility audit"),
        ],
    )

    amplicon = EGFP_CDS[:360]
    confirmed = SequenceRecord(
        name="EGFP_amplicon_sequence_confirmed",
        sequence=amplicon,
        topology="linear",
        features=[
            _feature("CDS", 1, 360, label="EGFP amplicon CDS", codon_start="1"),
            _feature("misc_feature", 1, 320, label="Sanger high-quality span", note="Q30 clean trace review"),
            _feature("misc_feature", 42, 180, label="NGS covered window", note="amplicon depth >= 20x"),
        ],
    )

    bundle_marker = SequenceRecord(
        name="Geneious_style_project_bundle_index",
        sequence=PUC19_MCS + EGFP_CDS[:180],
        topology="circular",
        features=[
            _feature("misc_feature", 1, len(PUC19_MCS), label="shared backbone feature"),
            _feature("CDS", len(PUC19_MCS) + 1, len(PUC19_MCS) + 180, label="bundle insert preview", codon_start="1"),
            _feature("misc_feature", 1, len(PUC19_MCS) + 180, label="multi-record project member", note="represents a Geneious-style project bundle audit"),
        ],
    )

    return [plasmid, cloning, edited, confirmed, bundle_marker]


def golden_project_payload() -> List[Dict[str, Any]]:
    return [
        {
            "name": rec.name,
            "topology": rec.topology,
            "content": rec.sequence,
            "features": _feature_dicts(rec),
        }
        for rec in golden_project_records()
    ]


def golden_project_compatibility_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    audit_payload = dict(payload)
    audit_payload["records"] = golden_project_payload()
    report = compatibility_audit(audit_payload, lambda: golden_project_records()[0])
    report["golden_project"] = {
        "case_count": 5,
        "cases": [
            "plasmid_with_promoter_cds_terminator_primers",
            "restriction_cloning_design",
            "edited_construct_expected_mutation",
            "sequencing_confirmed_construct",
            "multi_record_geneious_style_bundle",
        ],
    }
    report["records_payload"] = audit_payload["records"]
    return report


def payload_from_record(record: SequenceRecord) -> Dict[str, Any]:
    return canonical_to_payload(record_to_canonical(record, source_format="payload"))
