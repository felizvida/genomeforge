from __future__ import annotations

import uuid
from typing import Any, Dict, Tuple

from genomeforge_toolkit import DNA_ALPHABET


def _u16be(raw: bytes) -> list[int]:
    if len(raw) % 2:
        raw = raw[:-1]
    return [int.from_bytes(raw[i : i + 2], "big") for i in range(0, len(raw), 2)]


def _dir_entry(data: bytes, off: int) -> Dict[str, Any]:
    b = data[off : off + 28]
    if len(b) < 28:
        raise ValueError("Corrupt AB1: truncated directory entry")
    return {
        "tag": b[0:4].decode("ascii", errors="replace"),
        "num": int.from_bytes(b[4:8], "big"),
        "etype": int.from_bytes(b[8:10], "big"),
        "esize": int.from_bytes(b[10:12], "big"),
        "count": int.from_bytes(b[12:16], "big"),
        "size": int.from_bytes(b[16:20], "big"),
        "offset": int.from_bytes(b[20:24], "big"),
    }


def _entry_payload(data: bytes, e: Dict[str, Any]) -> bytes:
    size = int(e["size"])
    off = int(e["offset"])
    if size <= 4:
        return off.to_bytes(4, "big")[:size]
    if off + size > len(data):
        raise ValueError("Corrupt AB1: entry payload out of bounds")
    return data[off : off + size]


def _find(entries: Dict[Tuple[str, int], Dict[str, Any]], tag: str, num_prefer: Tuple[int, ...]) -> Dict[str, Any] | None:
    for n in num_prefer:
        if (tag, n) in entries:
            return entries[(tag, n)]
    # fallback any number
    for (t, _n), v in entries.items():
        if t == tag:
            return v
    return None


def parse_ab1_bytes(data: bytes) -> Dict[str, Any]:
    if len(data) < 34 or data[0:4] != b"ABIF":
        raise ValueError("Invalid AB1/ABIF payload")
    root = _dir_entry(data, 6)
    root_count = int(root["count"])
    root_off = int(root["offset"])
    entries: Dict[Tuple[str, int], Dict[str, Any]] = {}
    for i in range(root_count):
        off = root_off + i * 28
        e = _dir_entry(data, off)
        entries[(e["tag"], e["num"])] = e

    fwo = _find(entries, "FWO_", (1,))
    pbas = _find(entries, "PBAS", (2, 1))
    pcon = _find(entries, "PCON", (2, 1))
    ploc = _find(entries, "PLOC", (2, 1))
    if not pbas:
        raise ValueError("AB1 payload missing PBAS base calls")

    base_order = "GATC"
    if fwo:
        try:
            base_order = _entry_payload(data, fwo).decode("ascii", errors="ignore").strip("\x00") or "GATC"
        except Exception:  # noqa: BLE001
            base_order = "GATC"
    base_order = "".join(ch for ch in base_order if ch in "ACGT")[:4] or "GATC"

    seq = _entry_payload(data, pbas).decode("ascii", errors="ignore").strip("\x00").upper()
    seq = "".join(ch for ch in seq if ch in DNA_ALPHABET)
    qualities = [30] * len(seq)
    if pcon:
        q = list(_entry_payload(data, pcon))
        if q:
            qualities = q[: len(seq)] + [q[-1]] * max(0, len(seq) - len(q))
    positions = list(range(1, len(seq) + 1))
    if ploc:
        p = _u16be(_entry_payload(data, ploc))
        if p:
            positions = p[: len(seq)] + [p[-1]] * max(0, len(seq) - len(p))

    channel_indices = [9, 10, 11, 12]
    traces: Dict[str, list[int]] = {"A": [], "C": [], "G": [], "T": []}
    for idx, base in zip(channel_indices, base_order):
        e = _find(entries, "DATA", (idx,))
        if e:
            traces[base] = _u16be(_entry_payload(data, e))

    return {
        "trace_id": "trace_" + uuid.uuid4().hex[:12],
        "source": "ab1",
        "base_order": base_order,
        "sequence": seq,
        "quality": qualities,
        "positions": positions,
        "traces": traces,
        "length": len(seq),
    }


def synthetic_trace_from_sequence(sequence: str) -> Dict[str, Any]:
    seq = "".join(ch for ch in str(sequence).upper() if ch in DNA_ALPHABET)
    if not seq:
        raise ValueError("synthetic trace requires non-empty IUPAC DNA sequence")
    traces = {"A": [], "C": [], "G": [], "T": []}
    ambiguity_map = {
        "A": {"A"},
        "C": {"C"},
        "G": {"G"},
        "T": {"T"},
        "R": {"A", "G"},
        "Y": {"C", "T"},
        "S": {"G", "C"},
        "W": {"A", "T"},
        "K": {"G", "T"},
        "M": {"A", "C"},
        "B": {"C", "G", "T"},
        "D": {"A", "G", "T"},
        "H": {"A", "C", "T"},
        "V": {"A", "C", "G"},
        "N": {"A", "C", "G", "T"},
    }
    for i, b in enumerate(seq):
        supported = ambiguity_map.get(b, {"A", "C", "G", "T"})
        for base in "ACGT":
            if base in supported:
                amp = 950 if len(supported) == 1 else max(350, int(900 / len(supported)))
            else:
                amp = 120 + ((i * 19) % 80)
            traces[base].append(amp)
    return {
        "trace_id": "trace_" + uuid.uuid4().hex[:12],
        "source": "synthetic",
        "base_order": "GATC",
        "sequence": seq,
        "quality": [35] * len(seq),
        "positions": list(range(1, len(seq) + 1)),
        "traces": traces,
        "length": len(seq),
    }
