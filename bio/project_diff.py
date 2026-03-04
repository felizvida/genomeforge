from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any, Dict, List


def _clean_seq(content: str) -> str:
    txt = str(content or "")
    if txt.startswith(">"):
        txt = "\n".join(txt.splitlines()[1:])
    return "".join(ch for ch in txt.upper() if ch in "ACGTN")


def _feature_key_rows(features: List[Dict[str, Any]]) -> List[str]:
    rows = []
    for f in features or []:
        if not isinstance(f, dict):
            continue
        key = str(f.get("key", "misc_feature"))
        loc = str(f.get("location", ""))
        label = str((f.get("qualifiers") or {}).get("label", ""))
        rows.append(f"{key}|{loc}|{label}")
    return rows


def diff_projects(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    seq_a = _clean_seq(str(a.get("content", "")))
    seq_b = _clean_seq(str(b.get("content", "")))
    fa = _feature_key_rows(list(a.get("features", [])))
    fb = _feature_key_rows(list(b.get("features", [])))

    sm = SequenceMatcher(None, seq_a, seq_b)
    opcodes = sm.get_opcodes()
    seq_changes = []
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "equal":
            continue
        seq_changes.append(
            {
                "op": tag,
                "a_start_1based": i1 + 1,
                "a_end_1based": i2,
                "b_start_1based": j1 + 1,
                "b_end_1based": j2,
                "a_len": i2 - i1,
                "b_len": j2 - j1,
            }
        )
        if len(seq_changes) >= 300:
            break

    set_a = set(fa)
    set_b = set(fb)
    added_features = sorted(list(set_b - set_a))
    removed_features = sorted(list(set_a - set_b))

    return {
        "name_a": str(a.get("project_name", a.get("name", "A"))),
        "name_b": str(b.get("project_name", b.get("name", "B"))),
        "seq_len_a": len(seq_a),
        "seq_len_b": len(seq_b),
        "sequence_identity_pct": round(sm.ratio() * 100, 3),
        "sequence_change_count": len(seq_changes),
        "sequence_changes": seq_changes,
        "feature_count_a": len(fa),
        "feature_count_b": len(fb),
        "feature_added_count": len(added_features),
        "feature_removed_count": len(removed_features),
        "features_added": added_features[:200],
        "features_removed": removed_features[:200],
    }

