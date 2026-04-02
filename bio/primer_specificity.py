from __future__ import annotations

from typing import Any, Dict, List

from genomeforge_toolkit import DNA_ALPHABET, RC_TABLE, iupac_hamming_distance


def _clean(seq: str) -> str:
    return "".join(ch for ch in str(seq).upper() if ch in DNA_ALPHABET)


def _revcomp(seq: str) -> str:
    return _clean(seq).translate(RC_TABLE)[::-1]


def _hamming(a: str, b: str) -> int:
    return iupac_hamming_distance(a, b)


def _scan_hits(sequence: str, query: str, max_mismatch: int = 0) -> List[Dict[str, Any]]:
    s = _clean(sequence)
    q = _clean(query)
    if not s or not q or len(q) > len(s):
        return []
    out: List[Dict[str, Any]] = []
    L = len(q)
    for i in range(len(s) - L + 1):
        mm = _hamming(s[i : i + L], q)
        if mm <= max_mismatch:
            out.append({"start_1based": i + 1, "end_1based": i + L, "mismatches": mm})
    return out


def _normalize_backgrounds(background_sequences: List[Any]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for i, item in enumerate(background_sequences or []):
        if isinstance(item, dict):
            name = str(item.get("name", f"bg_{i+1}")).strip() or f"bg_{i+1}"
            seq = _clean(str(item.get("sequence", "")))
        else:
            name = f"bg_{i+1}"
            seq = _clean(str(item))
        if seq:
            rows.append({"name": name, "sequence": seq})
    return rows


def primer_specificity_report(
    forward: str,
    reverse: str,
    background_sequences: List[Any],
    max_mismatch: int = 1,
    min_amplicon_bp: int = 80,
    max_amplicon_bp: int = 3000,
) -> Dict[str, Any]:
    fwd = _clean(forward)
    rev = _clean(reverse)
    if len(fwd) < 12 or len(rev) < 12:
        raise ValueError("forward and reverse primers must be >= 12 nt")
    rev_bind = _revcomp(rev)
    bgs = _normalize_backgrounds(background_sequences)
    if not bgs:
        raise ValueError("background_sequences is required")

    reports = []
    total_pair_products = 0
    total_offtarget_products = 0
    for bg in bgs:
        seq = bg["sequence"]
        f_hits = _scan_hits(seq, fwd, max_mismatch=max_mismatch)
        r_hits = _scan_hits(seq, rev_bind, max_mismatch=max_mismatch)
        products = []
        for fh in f_hits:
            for rh in r_hits:
                if rh["start_1based"] <= fh["start_1based"]:
                    continue
                size = rh["end_1based"] - fh["start_1based"] + 1
                if min_amplicon_bp <= size <= max_amplicon_bp:
                    mm = fh["mismatches"] + rh["mismatches"]
                    products.append(
                        {
                            "start_1based": fh["start_1based"],
                            "end_1based": rh["end_1based"],
                            "size_bp": size,
                            "mismatch_sum": mm,
                            "perfect": mm == 0,
                        }
                    )
        products.sort(key=lambda x: (x["mismatch_sum"], x["size_bp"]))
        perfect = sum(1 for p in products if p["perfect"])
        total_pair_products += len(products)
        total_offtarget_products += max(0, len(products) - (1 if perfect else 0))
        reports.append(
            {
                "background": bg["name"],
                "length": len(seq),
                "forward_hits": len(f_hits),
                "reverse_hits": len(r_hits),
                "predicted_products": len(products),
                "perfect_products": perfect,
                "products": products[:60],
            }
        )

    risk = min(100.0, round(total_offtarget_products * 8 + max(0, total_pair_products - len(bgs)) * 2, 2))
    return {
        "forward": fwd,
        "reverse": rev,
        "max_mismatch": int(max_mismatch),
        "background_count": len(bgs),
        "total_predicted_products": total_pair_products,
        "offtarget_product_count": total_offtarget_products,
        "specificity_risk_score": risk,
        "reports": reports,
    }


def rank_primer_pairs(
    candidates: List[Dict[str, Any]],
    background_sequences: List[Any],
    max_mismatch: int = 1,
) -> Dict[str, Any]:
    rows = []
    for i, c in enumerate(candidates or []):
        if not isinstance(c, dict):
            continue
        f = _clean(str(c.get("forward", "")))
        r = _clean(str(c.get("reverse", "")))
        if len(f) < 12 or len(r) < 12:
            continue
        rep = primer_specificity_report(f, r, background_sequences, max_mismatch=max_mismatch)
        rows.append(
            {
                "rank_input_index": i,
                "forward": f,
                "reverse": r,
                "specificity_risk_score": rep["specificity_risk_score"],
                "offtarget_product_count": rep["offtarget_product_count"],
                "total_predicted_products": rep["total_predicted_products"],
            }
        )
    rows.sort(key=lambda x: (x["specificity_risk_score"], x["offtarget_product_count"], x["total_predicted_products"]))
    for i, row in enumerate(rows, start=1):
        row["rank"] = i
    return {"count": len(rows), "ranked_pairs": rows}
