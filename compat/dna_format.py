from __future__ import annotations

import json
import os
import struct
import tempfile
import zlib
from typing import Any, Dict


MAGIC = b"GFORGEDNA\x00"
FORMAT = "genomeforge.dna/1"
NATIVE_DNA_MAGIC = bytes.fromhex("536e617047656e65")


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


def _import_native_dna_biopython(data: bytes) -> Dict[str, Any]:
    try:
        from Bio import SeqIO  # type: ignore
    except Exception as e:  # noqa: BLE001
        raise ValueError(
            "Native proprietary .dna import requires Biopython. Install with: python3 -m pip install biopython"
        ) from e

    tmp_path: str | None = None
    try:
        # Use delete=False to avoid Windows file-lock issues when Biopython reopens by path.
        with tempfile.NamedTemporaryFile(suffix=".dna", delete=False) as tmp:
            tmp.write(data)
            tmp.flush()
            tmp_path = tmp.name
        rec = SeqIO.read(tmp_path, "snapgene")
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"Failed to parse native proprietary .dna payload: {e}") from e
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:  # noqa: BLE001
                pass

    seq = str(rec.seq or "").upper()
    if not seq:
        raise ValueError("Native proprietary .dna parser returned empty sequence")

    topology = str(rec.annotations.get("topology", "circular")).lower()
    if topology not in {"linear", "circular"}:
        topology = "circular"

    features = []
    for feat in list(getattr(rec, "features", []) or []):
        quals: Dict[str, str] = {}
        for k, v in dict(getattr(feat, "qualifiers", {}) or {}).items():
            if isinstance(v, list):
                quals[str(k)] = str(v[0]) if v else ""
            else:
                quals[str(k)] = str(v)
        features.append(
            {
                "key": str(getattr(feat, "type", "misc_feature") or "misc_feature"),
                "location": str(getattr(feat, "location", "")),
                "qualifiers": quals,
            }
        )

    payload = {
        "name": str(getattr(rec, "name", "") or getattr(rec, "id", "") or "Untitled"),
        "topology": topology,
        "content": seq,
        "features": features,
    }
    return {"source": "native_dna", "payload": payload, "metadata": {"parser": "biopython_snapgene"}}


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

    # Native proprietary .dna binary.
    if data.startswith(NATIVE_DNA_MAGIC):
        return _import_native_dna_biopython(data)

    raise ValueError("Unrecognized DNA container payload")
