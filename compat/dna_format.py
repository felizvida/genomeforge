from __future__ import annotations

import json
import struct
import zlib
from typing import Any, Dict


MAGIC = b"GFORGEDNA\x00"
FORMAT = "genomeforge.dna/1"


def _pack_document(doc: Dict[str, Any]) -> bytes:
    raw = json.dumps(doc, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    compressed = zlib.compress(raw, level=9)
    return MAGIC + struct.pack(">I", len(compressed)) + compressed


def _unpack_document(data: bytes) -> Dict[str, Any]:
    if not data.startswith(MAGIC):
        raise ValueError("Not a Genome Forge DNA container (magic mismatch)")
    if len(data) < len(MAGIC) + 4:
        raise ValueError("Corrupt DNA container: truncated header")
    n = struct.unpack(">I", data[len(MAGIC) : len(MAGIC) + 4])[0]
    payload = data[len(MAGIC) + 4 :]
    if n != len(payload):
        raise ValueError("Corrupt DNA container: size mismatch")
    try:
        text = zlib.decompress(payload).decode("utf-8")
        doc = json.loads(text)
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"Corrupt DNA container payload: {e}") from e
    if not isinstance(doc, dict):
        raise ValueError("Invalid DNA container: top-level document must be object")
    return doc


def export_dna_container(canonical_record: Dict[str, Any], metadata: Dict[str, Any] | None = None) -> bytes:
    if not isinstance(canonical_record, dict):
        raise ValueError("canonical_record must be an object")
    doc: Dict[str, Any] = {
        "format": FORMAT,
        "canonical_record": canonical_record,
        "metadata": metadata or {},
    }
    return _pack_document(doc)


def import_dna_container(data: bytes) -> Dict[str, Any]:
    # Genome Forge DNA container
    if data.startswith(MAGIC):
        doc = _unpack_document(data)
        if doc.get("format") != FORMAT:
            raise ValueError(f"Unsupported DNA container format: {doc.get('format')}")
        canon = doc.get("canonical_record")
        if not isinstance(canon, dict):
            raise ValueError("DNA container missing canonical_record object")
        return {"source": "genomeforge_dna", "canonical_record": canon, "metadata": doc.get("metadata", {})}

    # JSON fallback for portability in tests/tooling
    if data[:1] in {b"{", b"["}:
        try:
            doc = json.loads(data.decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            raise ValueError(f"Invalid JSON DNA payload: {e}") from e
        if isinstance(doc, dict) and isinstance(doc.get("canonical_record"), dict):
            return {"source": "json_canonical", "canonical_record": doc["canonical_record"], "metadata": doc.get("metadata", {})}
        if isinstance(doc, dict) and isinstance(doc.get("sequence"), str):
            # Very small fallback shape
            return {"source": "json_sequence", "payload": doc}
        raise ValueError("JSON payload must include canonical_record or sequence")

    # Real SnapGene .dna binaries are proprietary and not fully documented.
    # We fail explicitly instead of returning misleading results.
    if data.startswith(b"SnapGene"):
        raise ValueError("Native SnapGene binary .dna is not yet supported by this parser")

    raise ValueError("Unrecognized DNA container payload")

