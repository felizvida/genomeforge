from __future__ import annotations

from typing import Any, Dict, List

from genomeforge_toolkit import ENZYMES, find_all_occurrences, sanitize_sequence


RC = str.maketrans("ACGTN", "TGCAN")

# Simplified sticky-end model for common enzymes.
ENZYME_STICKY_ENDS: Dict[str, Dict[str, str]] = {
    "EcoRI": {"overhang": "AATT", "polarity": "5prime"},
    "BamHI": {"overhang": "GATC", "polarity": "5prime"},
    "HindIII": {"overhang": "AGCT", "polarity": "5prime"},
    "XhoI": {"overhang": "TCGA", "polarity": "5prime"},
    "XbaI": {"overhang": "CTAG", "polarity": "5prime"},
    "SpeI": {"overhang": "CTAG", "polarity": "5prime"},
    "NheI": {"overhang": "CTAG", "polarity": "5prime"},
    "KpnI": {"overhang": "GTAC", "polarity": "3prime"},
    "PstI": {"overhang": "TGCA", "polarity": "3prime"},
    "NotI": {"overhang": "CG", "polarity": "5prime"},
}


def _slice_circular(seq: str, start: int, length: int) -> str:
    n = len(seq)
    if n == 0 or length <= 0:
        return ""
    out = []
    for i in range(length):
        out.append(seq[(start + i) % n])
    return "".join(out)


def _parse_plain_sequence(seq: str) -> str:
    return sanitize_sequence(seq)


def _revcomp(seq: str) -> str:
    return _parse_plain_sequence(seq).translate(RC)[::-1]


def _is_complementary(a: str, b: str) -> bool:
    return _parse_plain_sequence(a) == _revcomp(_parse_plain_sequence(b))


def _overlap_len(a: str, b: str, min_overlap: int) -> int:
    max_k = min(len(a), len(b))
    for k in range(max_k, min_overlap - 1, -1):
        if a[-k:] == b[:k]:
            return k
    return 0


def gibson_assemble(fragments: List[str], min_overlap: int = 20, circular: bool = False) -> Dict[str, Any]:
    if len(fragments) < 2:
        raise ValueError("Need at least two fragments")
    frags = [_parse_plain_sequence(fragment) for fragment in fragments]
    overlaps: List[Dict[str, Any]] = []
    assembled = frags[0]
    for index in range(1, len(frags)):
        prev = assembled
        nxt = frags[index]
        max_k = min(len(prev), len(nxt))
        best = 0
        for k in range(max_k, min_overlap - 1, -1):
            if prev[-k:] == nxt[:k]:
                best = k
                break
        if best < min_overlap:
            raise ValueError(f"Insufficient overlap between fragment {index} and {index+1}")
        overlaps.append({"left_fragment": index, "right_fragment": index + 1, "overlap_bp": best, "sequence": nxt[:best]})
        assembled = prev + nxt[best:]

    circular_overlap = 0
    if circular:
        max_k = min(len(assembled), len(frags[0]))
        for k in range(max_k, min_overlap - 1, -1):
            if assembled[-k:] == frags[0][:k]:
                circular_overlap = k
                assembled = assembled[:-k]
                break
        if circular_overlap < min_overlap:
            raise ValueError("Insufficient closing overlap for circular assembly")

    return {
        "fragment_count": len(frags),
        "overlaps": overlaps,
        "circular_overlap_bp": circular_overlap,
        "assembled_length": len(assembled),
        "assembled_sequence": assembled,
        "topology": "circular" if circular else "linear",
    }


def golden_gate_assemble(parts: List[Dict[str, Any]], circular: bool = True, enforce_complement: bool = True) -> Dict[str, Any]:
    if len(parts) < 2:
        raise ValueError("Need at least two parts")
    normalized = []
    for index, part in enumerate(parts, start=1):
        seq = _parse_plain_sequence(str(part.get("sequence", "")))
        left = _parse_plain_sequence(str(part.get("left_overhang", "")))
        right = _parse_plain_sequence(str(part.get("right_overhang", "")))
        if len(left) != 4 or len(right) != 4:
            raise ValueError(f"Part {index} must have 4bp left_overhang and right_overhang")
        normalized.append({"sequence": seq, "left": left, "right": right})

    joins = []
    assembled = normalized[0]["sequence"]
    for index in range(len(normalized) - 1):
        left = normalized[index]
        right = normalized[index + 1]
        ok = _is_complementary(left["right"], right["left"]) if enforce_complement else (left["right"] == right["left"])
        if not ok:
            raise ValueError(f"Overhang mismatch between part {index+1} and part {index+2}")
        joins.append(
            {
                "left_part": index + 1,
                "right_part": index + 2,
                "left_overhang": left["right"],
                "right_overhang": right["left"],
            }
        )
        assembled += right["sequence"]

    closing_ok = None
    if circular:
        left = normalized[-1]["right"]
        right = normalized[0]["left"]
        closing_ok = _is_complementary(left, right) if enforce_complement else (left == right)
        if not closing_ok:
            raise ValueError("Closing overhang mismatch for circular Golden Gate assembly")

    return {
        "part_count": len(normalized),
        "joins": joins,
        "closing_join_ok": closing_ok,
        "assembled_length": len(assembled),
        "assembled_sequence": assembled,
        "topology": "circular" if circular else "linear",
    }


def gateway_cloning(
    entry_clone: str,
    destination_vector: str,
    attl: str = "ACAAGTTTGTACAAAAAAGCAGGCT",
    attr: str = "ACCACTTTGTACAAGAAAGCTGGGT",
) -> Dict[str, Any]:
    entry = _parse_plain_sequence(entry_clone)
    destination = _parse_plain_sequence(destination_vector)
    left_index = entry.find(attl)
    right_index = entry.find(attr)
    if left_index < 0 or right_index < 0 or right_index <= left_index:
        raise ValueError("Entry clone missing valid attL/attR sites")
    insert = entry[left_index + len(attl) : right_index]
    dest_left = destination.find("GGGCCC")
    dest_right = destination.find("CCCGGG")
    if dest_left >= 0 and dest_right > dest_left:
        product = destination[: dest_left + 6] + insert + destination[dest_right:]
    else:
        product = destination + insert
    return {"insert_length": len(insert), "product_length": len(product), "product_sequence": product}


def topo_cloning(vector: str, insert: str, mode: str = "TA") -> Dict[str, Any]:
    v = _parse_plain_sequence(vector)
    ins = _parse_plain_sequence(insert)
    mode = mode.upper()
    if mode == "TA":
        if not ins.endswith("A"):
            raise ValueError("TA mode expects insert ending with A-overhang")
    elif mode == "BLUNT":
        pass
    else:
        raise ValueError("Unsupported TOPO mode (use TA or BLUNT)")
    product = v + ins
    return {"mode": mode, "product_length": len(product), "product_sequence": product}


def ta_gc_cloning(vector: str, insert: str, mode: str = "TA") -> Dict[str, Any]:
    v = _parse_plain_sequence(vector)
    ins = _parse_plain_sequence(insert)
    mode = mode.upper()
    if mode == "TA":
        if not (ins.endswith("A") or ins.startswith("T")):
            raise ValueError("TA cloning expects A/T-compatible overhangs")
    elif mode == "GC":
        if not (ins.endswith("G") or ins.startswith("C")):
            raise ValueError("GC cloning expects G/C-compatible overhangs")
    else:
        raise ValueError("Unsupported mode (use TA or GC)")
    product = v + ins
    return {"mode": mode, "product_length": len(product), "product_sequence": product}


def cloning_compatibility_check(
    mode: str,
    vector: str = "",
    insert: str = "",
    enzymes: List[str] | None = None,
    left_overhang: str = "",
    right_overhang: str = "",
    min_overlap: int = 15,
) -> Dict[str, Any]:
    mode = mode.lower().strip()
    messages: List[str] = []
    ok = True

    if mode == "restriction":
        if not enzymes:
            return {"mode": mode, "ok": False, "messages": ["No enzymes provided"], "checks": {}}
        vector_seq = sanitize_sequence(vector)
        insert_seq = sanitize_sequence(insert)
        checks = {}
        for enzyme in enzymes:
            if enzyme not in ENZYMES:
                ok = False
                messages.append(f"Unknown enzyme {enzyme}")
                continue
            site = ENZYMES[enzyme][0]
            vector_count = len(find_all_occurrences(vector_seq, site, circular=True))
            insert_count = len(find_all_occurrences(insert_seq, site, circular=False))
            checks[enzyme] = {"site": site, "vector_sites": vector_count, "insert_sites": insert_count}
            if vector_count == 0:
                ok = False
                messages.append(f"{enzyme}: no site in vector")
            if insert_count == 0:
                ok = False
                messages.append(f"{enzyme}: no site in insert")
        if ok:
            messages.append("Restriction compatibility check passed")
        return {"mode": mode, "ok": ok, "messages": messages, "checks": checks}

    if mode in {"golden_gate", "golden-gate"}:
        left = sanitize_sequence(left_overhang) if left_overhang else ""
        right = sanitize_sequence(right_overhang) if right_overhang else ""
        if len(left) != 4 or len(right) != 4:
            return {"mode": mode, "ok": False, "messages": ["Provide 4bp left/right overhangs"], "checks": {}}
        comp = _is_complementary(left, right)
        if not comp:
            ok = False
            messages.append("Overhangs are not complementary")
        else:
            messages.append("Overhangs are complementary")
        return {"mode": mode, "ok": ok, "messages": messages, "checks": {"left_overhang": left, "right_overhang": right}}

    if mode in {"gibson", "in-fusion", "infusion"}:
        vector_seq = sanitize_sequence(vector)
        insert_seq = sanitize_sequence(insert)
        overlap = _overlap_len(vector_seq, insert_seq, min_overlap=min_overlap)
        if overlap < min_overlap:
            ok = False
            messages.append(f"Insufficient overlap: found {overlap}bp, need >= {min_overlap}bp")
        else:
            messages.append(f"Overlap OK: {overlap}bp")
        return {"mode": mode, "ok": ok, "messages": messages, "checks": {"overlap_bp": overlap, "required_overlap_bp": min_overlap}}

    return {"mode": mode, "ok": False, "messages": ["Unsupported mode"], "checks": {}}


def _end_object(enzyme: str) -> Dict[str, str]:
    if enzyme not in ENZYME_STICKY_ENDS:
        raise ValueError(f"No sticky-end model for enzyme {enzyme}")
    meta = ENZYME_STICKY_ENDS[enzyme]
    return {"enzyme": enzyme, "overhang": meta["overhang"], "polarity": meta["polarity"]}


def _end_from_sequence(seq: str, enzyme: str, side: str = "left") -> Dict[str, Any]:
    if enzyme not in ENZYMES or enzyme not in ENZYME_STICKY_ENDS:
        raise ValueError(f"Unsupported enzyme for sequence-derived ends: {enzyme}")
    sequence = sanitize_sequence(seq)
    site, cut_offset = ENZYMES[enzyme]
    starts = find_all_occurrences(sequence, site, circular=True)
    if not starts:
        raise ValueError(f"Enzyme site {enzyme}/{site} not found in sequence")
    site_start = starts[0] if side == "left" else starts[-1]
    cut = (site_start + cut_offset) % len(sequence)
    model = ENZYME_STICKY_ENDS[enzyme]
    overhang_len = len(model["overhang"])
    if model["polarity"] == "5prime":
        overhang = _slice_circular(sequence, cut, overhang_len)
    else:
        overhang = _slice_circular(sequence, cut - overhang_len, overhang_len)
    return {
        "enzyme": enzyme,
        "overhang": overhang,
        "polarity": model["polarity"],
        "cut_index_0based": cut,
        "site_start_0based": site_start,
    }


def _window_circular(seq: str, boundary: int, left: int = 12, right: int = 12) -> str:
    n = len(seq)
    if n == 0:
        return ""
    out = []
    for i in range(left + right):
        out.append(seq[(boundary - left + i) % n])
    return "".join(out)


def _junction_integrity(
    sequence: str,
    boundary: int,
    enzyme_a: str,
    enzyme_b: str,
    label: str,
) -> Dict[str, Any]:
    window = _window_circular(sequence, boundary, left=16, right=16)
    scar = _window_circular(sequence, boundary, left=4, right=4)
    sites = []
    for enzyme in (enzyme_a, enzyme_b):
        site = ENZYMES.get(enzyme, ("", 0))[0]
        if site:
            sites.append({"enzyme": enzyme, "site": site, "recreated": site in window})
    recreated = [site["enzyme"] for site in sites if site["recreated"]]
    return {
        "label": label,
        "boundary_index_0based": boundary,
        "scar_8bp": scar,
        "window_32bp": window,
        "expected_sites": sites,
        "recreated_sites": recreated,
    }


def _annotate_ligation_products(
    products: List[Dict[str, Any]],
    vector_len: int,
    insert_len: int,
    vector_left_enzyme: str,
    vector_right_enzyme: str,
    insert_left_enzyme: str,
    insert_right_enzyme: str,
) -> None:
    for product in products:
        product_class = str(product.get("class", ""))
        sequence = str(product.get("sequence", ""))
        if not sequence:
            continue
        if product_class == "desired_insert":
            orientation = str(product.get("orientation", "forward"))
            if orientation == "forward":
                junction_a = _junction_integrity(sequence, vector_len, vector_left_enzyme, insert_right_enzyme, "vector->insert")
                junction_b = _junction_integrity(sequence, vector_len + insert_len, insert_left_enzyme, vector_right_enzyme, "insert->vector")
            else:
                junction_a = _junction_integrity(sequence, vector_len, vector_left_enzyme, insert_left_enzyme, "vector->insert(rev)")
                junction_b = _junction_integrity(sequence, vector_len + insert_len, insert_right_enzyme, vector_right_enzyme, "insert->vector(rev)")
            product["junction_integrity"] = [junction_a, junction_b]
            mod3 = insert_len % 3
            product["fusion_frame"] = {
                "insert_len_mod3": mod3,
                "status": "in_frame" if mod3 == 0 else "frameshift_risk",
            }
        elif product_class == "vector_self_ligation":
            product["junction_integrity"] = [
                _junction_integrity(sequence, vector_len, vector_left_enzyme, vector_right_enzyme, "vector_religation")
            ]
        elif product_class in {"insert_self_ligation", "insert_concatemer"}:
            product["junction_integrity"] = [
                _junction_integrity(sequence, insert_len, insert_left_enzyme, insert_right_enzyme, "insert_religation")
            ]


def ligation_simulate(
    vector_sequence: str,
    insert_sequence: str,
    vector_left_enzyme: str,
    vector_right_enzyme: str,
    insert_left_enzyme: str,
    insert_right_enzyme: str,
    derive_from_sequence: bool = False,
    include_byproducts: bool = True,
    temp_c: float = 16.0,
    ligase_units: float = 1.0,
    vector_insert_ratio: float = 1.0,
    dna_ng: float = 100.0,
    phosphatase_treated_vector: bool = False,
    star_activity_level: float = 0.0,
) -> Dict[str, Any]:
    vector = sanitize_sequence(vector_sequence)
    insert = sanitize_sequence(insert_sequence)

    if derive_from_sequence:
        vector_left = _end_from_sequence(vector, vector_left_enzyme, "left")
        vector_right = _end_from_sequence(vector, vector_right_enzyme, "right")
        insert_left = _end_from_sequence(insert, insert_left_enzyme, "left")
        insert_right = _end_from_sequence(insert, insert_right_enzyme, "right")
    else:
        vector_left = _end_object(vector_left_enzyme)
        vector_right = _end_object(vector_right_enzyme)
        insert_left = _end_object(insert_left_enzyme)
        insert_right = _end_object(insert_right_enzyme)

    forward_ok = _is_complementary(vector_left["overhang"], insert_right["overhang"]) and _is_complementary(insert_left["overhang"], vector_right["overhang"])
    reverse_ok = _is_complementary(vector_left["overhang"], insert_left["overhang"]) and _is_complementary(insert_right["overhang"], vector_right["overhang"])

    products = []
    if forward_ok:
        products.append(
            {
                "class": "desired_insert",
                "orientation": "forward",
                "length": len(vector) + len(insert),
                "junctions": [
                    {"left": vector_left["overhang"], "right": insert_right["overhang"]},
                    {"left": insert_left["overhang"], "right": vector_right["overhang"]},
                ],
                "sequence": vector + insert,
                "rank_score": 100,
            }
        )
    if reverse_ok:
        insert_rev = _revcomp(insert)
        products.append(
            {
                "class": "desired_insert",
                "orientation": "reverse",
                "length": len(vector) + len(insert),
                "junctions": [
                    {"left": vector_left["overhang"], "right": insert_left["overhang"]},
                    {"left": insert_right["overhang"], "right": vector_right["overhang"]},
                ],
                "sequence": vector + insert_rev,
                "rank_score": 95,
            }
        )

    if include_byproducts:
        if (not phosphatase_treated_vector) and _is_complementary(vector_left["overhang"], vector_right["overhang"]):
            products.append(
                {
                    "class": "vector_self_ligation",
                    "orientation": "vector_only",
                    "length": len(vector),
                    "junctions": [{"left": vector_left["overhang"], "right": vector_right["overhang"]}],
                    "sequence": vector,
                    "rank_score": 70,
                }
            )
        if _is_complementary(insert_left["overhang"], insert_right["overhang"]):
            products.append(
                {
                    "class": "insert_self_ligation",
                    "orientation": "insert_only",
                    "length": len(insert),
                    "junctions": [{"left": insert_left["overhang"], "right": insert_right["overhang"]}],
                    "sequence": insert,
                    "rank_score": 60,
                }
            )
            products.append(
                {
                    "class": "insert_concatemer",
                    "orientation": "concatemer_forward",
                    "length": len(insert) * 2,
                    "junctions": [{"left": insert_left["overhang"], "right": insert_right["overhang"]}],
                    "sequence": insert + insert,
                    "rank_score": 50,
                }
            )

    _annotate_ligation_products(
        products,
        vector_len=len(vector),
        insert_len=len(insert),
        vector_left_enzyme=vector_left_enzyme,
        vector_right_enzyme=vector_right_enzyme,
        insert_left_enzyme=insert_left_enzyme,
        insert_right_enzyme=insert_right_enzyme,
    )

    messages = []
    risk_flags = []
    if not products:
        messages.append("No compatible ligation orientation found with provided ends")
    else:
        messages.append(f"Found {len(products)} compatible ligation product(s)")
    if phosphatase_treated_vector:
        messages.append("Vector phosphatase treatment enabled: vector self-ligation suppressed")
    if float(star_activity_level) > 0.25:
        risk_flags.append("star_activity_risk")
        messages.append("Elevated star-activity risk may increase undesired byproducts")

    def condition_factor(product: Dict[str, Any]) -> float:
        product_class = str(product.get("class", ""))
        temp_opt = max(0.2, 1.0 - abs(float(temp_c) - 16.0) / 28.0)
        ligase_factor = max(0.2, min(2.0, float(ligase_units) / 1.0))
        dna_factor = max(0.3, min(1.7, float(dna_ng) / 100.0))
        ratio = max(0.05, float(vector_insert_ratio))
        star = max(0.0, min(1.0, float(star_activity_level)))
        if product_class == "desired_insert":
            if str(product.get("orientation")) == "forward":
                polarities = [(vector_left["polarity"], insert_right["polarity"]), (insert_left["polarity"], vector_right["polarity"])]
            elif str(product.get("orientation")) == "reverse":
                polarities = [(vector_left["polarity"], insert_left["polarity"]), (insert_right["polarity"], vector_right["polarity"])]
            else:
                polarities = []
            if polarities:
                matches = sum(1 for left, right in polarities if left == right)
                polarity_factor = 0.65 + 0.35 * (matches / len(polarities))
            else:
                polarity_factor = 1.0
        else:
            polarity_factor = 1.0
        if product_class == "desired_insert":
            ratio_factor = max(0.3, min(1.8, ratio))
            base = 1.0 * (1.0 - 0.35 * star)
        elif product_class == "vector_self_ligation":
            ratio_factor = max(0.2, min(2.2, 1.0 / ratio))
            base = 0.55 * (1.0 + 0.8 * star)
        elif product_class == "insert_self_ligation":
            ratio_factor = max(0.3, min(2.0, ratio * 0.8))
            base = 0.45 * (1.0 + 0.7 * star)
        else:
            ratio_factor = max(0.3, min(2.5, ratio * 1.1))
            base = 0.35 * (1.0 + 0.9 * star)
        return base * temp_opt * ligase_factor * dna_factor * ratio_factor * polarity_factor

    raw_scores = []
    for product in products:
        score = float(product.get("rank_score", 0)) * condition_factor(product)
        product["condition_adjusted_score"] = round(score, 3)
        raw_scores.append(max(0.0, score))
    score_sum = sum(raw_scores)
    if score_sum > 0:
        for product, score in zip(products, raw_scores):
            product["predicted_probability"] = round(score / score_sum, 4)
    else:
        for product in products:
            product["predicted_probability"] = 0.0

    products.sort(
        key=lambda product: (
            -float(product.get("predicted_probability", 0.0)),
            -float(product.get("condition_adjusted_score", 0.0)),
            int(product.get("length", 0)),
        )
    )
    return {
        "vector_ends": {"left": vector_left, "right": vector_right},
        "insert_ends": {"left": insert_left, "right": insert_right},
        "derive_from_sequence": derive_from_sequence,
        "include_byproducts": include_byproducts,
        "reaction_conditions": {
            "temp_c": float(temp_c),
            "ligase_units": float(ligase_units),
            "vector_insert_ratio": float(vector_insert_ratio),
            "dna_ng": float(dna_ng),
            "phosphatase_treated_vector": bool(phosphatase_treated_vector),
            "star_activity_level": float(star_activity_level),
        },
        "risk_flags": risk_flags,
        "forward_compatible": forward_ok,
        "reverse_compatible": reverse_ok,
        "products": products,
        "messages": messages,
    }


def in_fusion_assemble(fragments: List[str], min_overlap: int = 15, circular: bool = False) -> Dict[str, Any]:
    if len(fragments) < 2:
        raise ValueError("Need at least two fragments")
    frags = [_parse_plain_sequence(fragment) for fragment in fragments]
    assembled = frags[0]
    joins: List[Dict[str, Any]] = []
    for index in range(1, len(frags)):
        left = assembled
        right = frags[index]
        max_k = min(len(left), len(right))
        best = 0
        for k in range(max_k, min_overlap - 1, -1):
            if left[-k:] == right[:k]:
                best = k
                break
        if best < min_overlap:
            raise ValueError(f"Insufficient homology arm between fragment {index} and {index+1}")
        joins.append({"left_fragment": index, "right_fragment": index + 1, "homology_bp": best})
        assembled = left + right[best:]

    circular_join = 0
    if circular:
        max_k = min(len(assembled), len(frags[0]))
        for k in range(max_k, min_overlap - 1, -1):
            if assembled[-k:] == frags[0][:k]:
                circular_join = k
                assembled = assembled[:-k]
                break
        if circular_join < min_overlap:
            raise ValueError("Insufficient closing homology arm for circular In-Fusion")

    return {
        "fragment_count": len(frags),
        "joins": joins,
        "closing_homology_bp": circular_join,
        "assembled_length": len(assembled),
        "assembled_sequence": assembled,
        "topology": "circular" if circular else "linear",
    }


def overlap_extension_pcr(fragment_a: str, fragment_b: str, min_overlap: int = 18) -> Dict[str, Any]:
    left = _parse_plain_sequence(fragment_a)
    right = _parse_plain_sequence(fragment_b)
    max_k = min(len(left), len(right))
    best = 0
    for k in range(max_k, min_overlap - 1, -1):
        if left[-k:] == right[:k]:
            best = k
            break
    if best < min_overlap:
        raise ValueError("No sufficient overlap for overlap-extension PCR")
    product = left + right[best:]
    return {
        "overlap_bp": best,
        "product_length": len(product),
        "product_sequence": product,
    }


def handle_assembly_endpoint(path: str, payload: Dict[str, Any]) -> Dict[str, Any] | None:
    if path == "/api/gibson-assemble":
        fragments = payload.get("fragments", [])
        return gibson_assemble(
            [str(fragment) for fragment in fragments],
            min_overlap=int(payload.get("min_overlap", 20)),
            circular=bool(payload.get("circular", False)),
        )
    if path == "/api/golden-gate":
        return golden_gate_assemble(
            payload.get("parts", []),
            circular=bool(payload.get("circular", True)),
            enforce_complement=bool(payload.get("enforce_complement", True)),
        )
    if path == "/api/gateway-cloning":
        return gateway_cloning(
            entry_clone=str(payload.get("entry_clone", "")),
            destination_vector=str(payload.get("destination_vector", "")),
            attl=str(payload.get("attl", "ACAAGTTTGTACAAAAAAGCAGGCT")),
            attr=str(payload.get("attr", "ACCACTTTGTACAAGAAAGCTGGGT")),
        )
    if path == "/api/topo-cloning":
        return topo_cloning(
            vector=str(payload.get("vector", "")),
            insert=str(payload.get("insert", "")),
            mode=str(payload.get("mode", "TA")),
        )
    if path == "/api/ta-gc-cloning":
        return ta_gc_cloning(
            vector=str(payload.get("vector", "")),
            insert=str(payload.get("insert", "")),
            mode=str(payload.get("mode", "TA")),
        )
    if path == "/api/cloning-compatibility":
        enzymes = payload.get("enzymes", [])
        if isinstance(enzymes, str):
            enzymes = [item.strip() for item in enzymes.split(",") if item.strip()]
        return cloning_compatibility_check(
            mode=str(payload.get("mode", "restriction")),
            vector=str(payload.get("vector", "")),
            insert=str(payload.get("insert", "")),
            enzymes=[str(item) for item in enzymes],
            left_overhang=str(payload.get("left_overhang", "")),
            right_overhang=str(payload.get("right_overhang", "")),
            min_overlap=int(payload.get("min_overlap", 15)),
        )
    if path == "/api/ligation-sim":
        return ligation_simulate(
            vector_sequence=str(payload.get("vector_sequence", "")),
            insert_sequence=str(payload.get("insert_sequence", "")),
            vector_left_enzyme=str(payload.get("vector_left_enzyme", "")),
            vector_right_enzyme=str(payload.get("vector_right_enzyme", "")),
            insert_left_enzyme=str(payload.get("insert_left_enzyme", "")),
            insert_right_enzyme=str(payload.get("insert_right_enzyme", "")),
            derive_from_sequence=bool(payload.get("derive_from_sequence", False)),
            include_byproducts=bool(payload.get("include_byproducts", True)),
            temp_c=float(payload.get("temp_c", 16.0)),
            ligase_units=float(payload.get("ligase_units", 1.0)),
            vector_insert_ratio=float(payload.get("vector_insert_ratio", 1.0)),
            dna_ng=float(payload.get("dna_ng", 100.0)),
            phosphatase_treated_vector=bool(payload.get("phosphatase_treated_vector", False)),
            star_activity_level=float(payload.get("star_activity_level", 0.0)),
        )
    if path == "/api/in-fusion":
        fragments = payload.get("fragments", [])
        return in_fusion_assemble(
            fragments=[str(fragment) for fragment in fragments],
            min_overlap=int(payload.get("min_overlap", 15)),
            circular=bool(payload.get("circular", False)),
        )
    if path == "/api/overlap-extension-pcr":
        return overlap_extension_pcr(
            fragment_a=str(payload.get("fragment_a", "")),
            fragment_b=str(payload.get("fragment_b", "")),
            min_overlap=int(payload.get("min_overlap", 18)),
        )
    return None
