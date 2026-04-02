from __future__ import annotations

import math
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

from genomeforge_toolkit import CODON_TABLE, DNA_ALPHABET, SequenceRecord, find_all_occurrences, sanitize_sequence


RecordGetter = Callable[[], SequenceRecord]


def _parse_plain_sequence(seq: str) -> str:
    return sanitize_sequence(seq)


def _reverse_translate_protein(protein: str, host: str = "ecoli") -> str:
    prefs = {
        "ecoli": {
            "A": "GCG", "R": "CGT", "N": "AAC", "D": "GAT", "C": "TGC",
            "Q": "CAG", "E": "GAA", "G": "GGC", "H": "CAC", "I": "ATC",
            "L": "CTG", "K": "AAA", "M": "ATG", "F": "TTC", "P": "CCG",
            "S": "TCG", "T": "ACC", "W": "TGG", "Y": "TAC", "V": "GTG", "*": "TAA",
        },
        "yeast": {
            "A": "GCT", "R": "AGA", "N": "AAT", "D": "GAT", "C": "TGT",
            "Q": "CAA", "E": "GAA", "G": "GGT", "H": "CAT", "I": "ATT",
            "L": "TTG", "K": "AAA", "M": "ATG", "F": "TTT", "P": "CCA",
            "S": "TCT", "T": "ACT", "W": "TGG", "Y": "TAT", "V": "GTT", "*": "TAA",
        },
    }
    aa_to_codons: Dict[str, List[str]] = {}
    for codon, aa in CODON_TABLE.items():
        aa_to_codons.setdefault(aa, []).append(codon)
    host = host.lower()
    pref = prefs.get(host, prefs["ecoli"])
    aa = protein.strip().upper()
    if not aa:
        raise ValueError("protein is required")
    codons: List[str] = []
    for residue in aa:
        if residue not in pref and residue not in aa_to_codons:
            raise ValueError(f"Unsupported amino acid: {residue}")
        codons.append(pref.get(residue, aa_to_codons[residue][0]))
    return "".join(codons)


def _apply_sequence_edit(
    record: SequenceRecord,
    op: str,
    start_1based: int,
    end_1based: int = 0,
    value: str = "",
) -> SequenceRecord:
    seq = record.sequence
    n = record.length
    if start_1based < 1 or start_1based > n + 1:
        raise ValueError("start out of bounds")
    idx = start_1based - 1

    if op == "insert":
        ins = sanitize_sequence(value)
        new_seq = seq[:idx] + ins + seq[idx:]
    elif op == "delete":
        if end_1based < start_1based or end_1based > n:
            raise ValueError("invalid delete range")
        new_seq = seq[:idx] + seq[end_1based:]
    elif op == "replace":
        if end_1based < start_1based or end_1based > n:
            raise ValueError("invalid replace range")
        rep = sanitize_sequence(value)
        new_seq = seq[:idx] + rep + seq[end_1based:]
    else:
        raise ValueError("Unsupported edit op. Use insert|delete|replace")

    return SequenceRecord(
        name=record.name,
        sequence=new_seq,
        topology=record.topology,
        molecule=record.molecule,
        features=record.features,
    )


def needleman_wunsch(
    seq_a: str,
    seq_b: str,
    match: int = 1,
    mismatch: int = -1,
    gap: int = -2,
) -> Dict[str, Any]:
    a = _parse_plain_sequence(seq_a)
    b = _parse_plain_sequence(seq_b)
    m, n = len(a), len(b)
    score = [[0] * (n + 1) for _ in range(m + 1)]
    trace = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        score[i][0] = i * gap
        trace[i][0] = 2
    for j in range(1, n + 1):
        score[0][j] = j * gap
        trace[0][j] = 3
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            s_diag = score[i - 1][j - 1] + (match if a[i - 1] == b[j - 1] else mismatch)
            s_up = score[i - 1][j] + gap
            s_left = score[i][j - 1] + gap
            best = max(s_diag, s_up, s_left)
            score[i][j] = best
            trace[i][j] = 1 if best == s_diag else (2 if best == s_up else 3)

    i, j = m, n
    aa: List[str] = []
    bb: List[str] = []
    while i > 0 or j > 0:
        t = trace[i][j]
        if t == 1:
            aa.append(a[i - 1])
            bb.append(b[j - 1])
            i -= 1
            j -= 1
        elif t == 2:
            aa.append(a[i - 1])
            bb.append("-")
            i -= 1
        else:
            aa.append("-")
            bb.append(b[j - 1])
            j -= 1
    aln_a = "".join(reversed(aa))
    aln_b = "".join(reversed(bb))
    ident = sum(1 for x, y in zip(aln_a, aln_b) if x == y and x != "-")
    aln_len = max(len(aln_a), 1)
    return {
        "score": score[m][n],
        "identity_pct": round(ident / aln_len * 100.0, 2),
        "aligned_a": aln_a,
        "aligned_b": aln_b,
    }


def needleman_wunsch_protein(
    seq_a: str,
    seq_b: str,
    match: int = 2,
    mismatch: int = -1,
    gap: int = -3,
) -> Dict[str, Any]:
    a = "".join(ch for ch in str(seq_a).upper() if ch.isalpha() or ch in {"*", "-"})
    b = "".join(ch for ch in str(seq_b).upper() if ch.isalpha() or ch in {"*", "-"})
    if not a or not b:
        raise ValueError("Protein sequences are required")
    m, n = len(a), len(b)
    score = [[0] * (n + 1) for _ in range(m + 1)]
    trace = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        score[i][0] = i * gap
        trace[i][0] = 2
    for j in range(1, n + 1):
        score[0][j] = j * gap
        trace[0][j] = 3
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            s_diag = score[i - 1][j - 1] + (match if a[i - 1] == b[j - 1] else mismatch)
            s_up = score[i - 1][j] + gap
            s_left = score[i][j - 1] + gap
            best = max(s_diag, s_up, s_left)
            score[i][j] = best
            trace[i][j] = 1 if best == s_diag else (2 if best == s_up else 3)
    i, j = m, n
    aa: List[str] = []
    bb: List[str] = []
    while i > 0 or j > 0:
        t = trace[i][j]
        if t == 1:
            aa.append(a[i - 1])
            bb.append(b[j - 1])
            i -= 1
            j -= 1
        elif t == 2:
            aa.append(a[i - 1])
            bb.append("-")
            i -= 1
        else:
            aa.append("-")
            bb.append(b[j - 1])
            j -= 1
    aln_a = "".join(reversed(aa))
    aln_b = "".join(reversed(bb))
    ident = sum(1 for x, y in zip(aln_a, aln_b) if x == y and x != "-")
    return {
        "mode": "protein",
        "score": score[m][n],
        "identity_pct": round(ident / max(1, len(aln_a)) * 100.0, 2),
        "aligned_a": aln_a,
        "aligned_b": aln_b,
    }


def _overlap_len(a: str, b: str, min_overlap: int) -> int:
    max_k = min(len(a), len(b))
    for k in range(max_k, min_overlap - 1, -1):
        if a[-k:] == b[:k]:
            return k
    return 0


def contig_assemble(reads: List[str], min_overlap: int = 20) -> Dict[str, Any]:
    seqs = [_parse_plain_sequence(read) for read in reads if str(read).strip()]
    if len(seqs) < 2:
        raise ValueError("Need at least two reads")
    merged_steps: List[Dict[str, Any]] = []
    while len(seqs) > 1:
        best_i = best_j = -1
        best_k = 0
        for i in range(len(seqs)):
            for j in range(len(seqs)):
                if i == j:
                    continue
                k = _overlap_len(seqs[i], seqs[j], min_overlap=min_overlap)
                if k > best_k:
                    best_i, best_j, best_k = i, j, k
        if best_k < min_overlap:
            break
        left = seqs[best_i]
        right = seqs[best_j]
        merged = left + right[best_k:]
        merged_steps.append({"left_idx": best_i, "right_idx": best_j, "overlap_bp": best_k, "merged_length": len(merged)})
        for idx in sorted([best_i, best_j], reverse=True):
            del seqs[idx]
        seqs.append(merged)
    seqs.sort(key=len, reverse=True)
    return {
        "input_reads": len(reads),
        "contig_count": len(seqs),
        "largest_contig_length": len(seqs[0]) if seqs else 0,
        "steps": merged_steps,
        "contigs": seqs,
    }


def multi_align_to_reference(sequences: List[str]) -> Dict[str, Any]:
    seqs = [_parse_plain_sequence(seq) for seq in sequences if str(seq).strip()]
    if len(seqs) < 2:
        raise ValueError("Need at least two sequences")
    ref = seqs[0]
    results = []
    for idx, seq in enumerate(seqs[1:], start=2):
        aln = needleman_wunsch(ref, seq)
        results.append(
            {
                "sequence_index": idx,
                "score": aln["score"],
                "identity_pct": aln["identity_pct"],
                "aligned_ref": aln["aligned_a"],
                "aligned_query": aln["aligned_b"],
            }
        )
    return {"reference_length": len(ref), "sequence_count": len(seqs), "pairwise_to_reference": results}


def _merge_gapped_reference(
    old_ref: str,
    old_rows: List[str],
    new_ref: str,
    new_row: str,
) -> Tuple[List[str], str]:
    i = j = 0
    merged_rows = ["" for _ in old_rows]
    merged_new = ""
    while i < len(old_ref) or j < len(new_ref):
        co = old_ref[i] if i < len(old_ref) else None
        cn = new_ref[j] if j < len(new_ref) else None
        if co is None:
            for k in range(len(merged_rows)):
                merged_rows[k] += "-"
            merged_new += new_row[j]
            j += 1
            continue
        if cn is None:
            for k in range(len(merged_rows)):
                merged_rows[k] += old_rows[k][i]
            merged_new += "-"
            i += 1
            continue
        if co == cn:
            for k in range(len(merged_rows)):
                merged_rows[k] += old_rows[k][i]
            merged_new += new_row[j]
            i += 1
            j += 1
        elif co == "-":
            for k in range(len(merged_rows)):
                merged_rows[k] += old_rows[k][i]
            merged_new += "-"
            i += 1
        elif cn == "-":
            for k in range(len(merged_rows)):
                merged_rows[k] += "-"
            merged_new += new_row[j]
            j += 1
        else:
            for k in range(len(merged_rows)):
                merged_rows[k] += old_rows[k][i]
            merged_new += new_row[j]
            i += 1
            j += 1
    return merged_rows, merged_new


def progressive_msa(sequences: List[str]) -> Dict[str, Any]:
    seqs = [_parse_plain_sequence(seq) for seq in sequences if str(seq).strip()]
    if len(seqs) < 2:
        raise ValueError("Need at least two sequences")
    ref = seqs[0]
    aligned_rows = [ref]
    ref_gapped = ref
    for seq in seqs[1:]:
        aln = needleman_wunsch(ref, seq)
        new_ref = aln["aligned_a"]
        new_seq = aln["aligned_b"]
        aligned_rows, merged_new = _merge_gapped_reference(ref_gapped, aligned_rows, new_ref, new_seq)
        aligned_rows.append(merged_new)
        ref_gapped = aligned_rows[0]
    col_count = len(aligned_rows[0]) if aligned_rows else 0
    return {"method": "progressive", "sequence_count": len(aligned_rows), "columns": col_count, "alignment": aligned_rows}


def _parse_fasta_text(text: str) -> List[str]:
    rows: List[str] = []
    cur: List[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(">"):
            if cur:
                rows.append("".join(cur))
                cur = []
        else:
            cur.append(stripped)
    if cur:
        rows.append("".join(cur))
    return rows


def external_msa(method: str, sequences: List[str]) -> Dict[str, Any]:
    seqs = [_parse_plain_sequence(seq) for seq in sequences if str(seq).strip()]
    if len(seqs) < 2:
        raise ValueError("Need at least two sequences")
    bin_map = {
        "clustalw": "clustalw2",
        "clustalw2": "clustalw2",
        "mafft": "mafft",
        "muscle": "muscle",
        "tcoffee": "t_coffee",
        "t-coffee": "t_coffee",
    }
    method = method.lower()
    bin_name = bin_map.get(method, method)
    if not shutil.which(bin_name):
        return {"fallback": True, "reason": f"{bin_name} not found", **progressive_msa(seqs)}

    with tempfile.TemporaryDirectory() as td:
        inp = Path(td) / "in.fa"
        inp.write_text("\n".join([f">seq{i+1}\n{seq}" for i, seq in enumerate(seqs)]) + "\n", encoding="utf-8")
        if method.startswith("clustalw"):
            out = Path(td) / "out.aln"
            cmd = [bin_name, f"-INFILE={inp}", "-OUTPUT=FASTA", f"-OUTFILE={out}"]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            aligned = _parse_fasta_text(out.read_text(encoding="utf-8"))
        elif method == "mafft":
            cmd = [bin_name, "--auto", str(inp)]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            aligned = _parse_fasta_text(result.stdout)
        elif method == "muscle":
            out = Path(td) / "out.fa"
            cmd = [bin_name, "-align", str(inp), "-output", str(out)]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            aligned = _parse_fasta_text(out.read_text(encoding="utf-8"))
        elif method in {"tcoffee", "t-coffee"}:
            cmd = [bin_name, "-in", str(inp), "-output=fasta_aln"]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            aligned = _parse_fasta_text(result.stdout)
            if not aligned:
                fallback_out = Path(td) / "in.fa.aln"
                if fallback_out.exists():
                    aligned = _parse_fasta_text(fallback_out.read_text(encoding="utf-8"))
            if not aligned:
                raise ValueError("t_coffee produced no FASTA alignment output")
        else:
            raise ValueError(f"Unsupported MSA method: {method}")
    return {"method": method, "sequence_count": len(aligned), "columns": len(aligned[0]) if aligned else 0, "alignment": aligned}


def alignment_consensus(alignment: List[str]) -> Dict[str, Any]:
    rows = [str(row) for row in alignment if str(row)]
    if not rows:
        raise ValueError("Alignment is empty")
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("Alignment rows must have equal length")
    consensus_chars = []
    conservation = []
    for col in range(width):
        counts: Dict[str, int] = {}
        for row in rows:
            ch = row[col]
            counts[ch] = counts.get(ch, 0) + 1
        counts_nogap = {k: v for k, v in counts.items() if k != "-"}
        if counts_nogap:
            best = max(sorted(counts_nogap), key=lambda k: counts_nogap[k])
            consensus_chars.append(best)
            conservation.append(round(counts_nogap[best] / len(rows), 3))
        else:
            consensus_chars.append("-")
            conservation.append(0.0)
    identity_matrix = []
    for i in range(len(rows)):
        matrix_row = []
        for j in range(len(rows)):
            same = sum(1 for a, b in zip(rows[i], rows[j]) if a == b)
            matrix_row.append(round(same / width * 100.0, 2))
        identity_matrix.append(matrix_row)
    return {
        "row_count": len(rows),
        "columns": width,
        "consensus": "".join(consensus_chars),
        "conservation": conservation,
        "identity_matrix_pct": identity_matrix,
    }


def sequence_track_svg(
    record: SequenceRecord,
    start_1based: int = 1,
    end_1based: int | None = None,
    frame: int = 1,
) -> Dict[str, Any]:
    if end_1based is None:
        end_1based = min(record.length, start_1based + 299)
    if start_1based < 1 or end_1based > record.length or start_1based > end_1based:
        raise ValueError("Invalid track window")
    if frame not in (1, 2, 3):
        raise ValueError("Frame must be 1,2,3")

    width = 1200
    left = 40
    usable = width - 2 * left
    height = 260
    y_axis = 90

    def x_for_pos(pos_1based: int) -> float:
        frac = (pos_1based - start_1based) / max(1, (end_1based - start_1based))
        return left + frac * usable

    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    lines.append('<rect width="100%" height="100%" fill="#f8fafc"/>')
    lines.append(f'<text x="{left}" y="24" font-size="14" font-family="Menlo, monospace" fill="#0f172a">{record.name}  {start_1based}..{end_1based}</text>')
    lines.append(f'<line x1="{left}" y1="{y_axis}" x2="{width-left}" y2="{y_axis}" stroke="#0f172a" stroke-width="2"/>')

    feature_colors = {
        "cds": "#2563eb",
        "gene": "#dc2626",
        "promoter": "#16a34a",
        "rbs": "#0d9488",
        "terminator": "#d97706",
        "misc_feature": "#7c3aed",
    }

    def parse_loc(loc: str) -> Tuple[int, int, int]:
        loc_s = loc.strip()
        strand = -1 if "complement" in loc_s.lower() else 1
        nums = [int(x) for x in "".join(ch if ch.isdigit() else " " for ch in loc_s).split()]
        if len(nums) < 2:
            return 0, 0, strand
        a, b = nums[0], nums[-1]
        if a > b:
            a, b = b, a
        return a, b, strand

    for idx, feature in enumerate(record.features):
        a, b, strand = parse_loc(feature.location)
        if a <= 0 or b <= 0:
            continue
        if b < start_1based or a > end_1based:
            continue
        fa = max(a, start_1based)
        fb = min(b, end_1based)
        x1 = x_for_pos(fa)
        x2 = x_for_pos(fb)
        color = feature_colors.get(feature.key.lower(), "#475569")
        width_f = max(2.0, x2 - x1)
        lines.append(
            f'<rect x="{x1:.2f}" y="{y_axis-22}" width="{width_f:.2f}" height="14" rx="3" fill="{color}" opacity="0.9" '
            f'data-feature-index="{idx}" data-feature-start="{fa}" data-feature-end="{fb}" class="feature-segment"/>'
        )
        if width_f >= 10:
            if strand > 0:
                ax = x2
                pts = f"{ax-8:.2f},{y_axis-22:.2f} {ax:.2f},{y_axis-15:.2f} {ax-8:.2f},{y_axis-8:.2f}"
            else:
                ax = x1
                pts = f"{ax+8:.2f},{y_axis-22:.2f} {ax:.2f},{y_axis-15:.2f} {ax+8:.2f},{y_axis-8:.2f}"
            lines.append(
                f'<polygon points="{pts}" fill="#0f172a" opacity="0.75" '
                f'data-feature-index="{idx}" class="feature-arrow"/>'
            )
        label = feature.qualifiers.get("label") or feature.qualifiers.get("gene") or feature.key
        extra = ""
        if feature.key.lower() == "cds":
            phase = (a - 1) % 3
            extra = f" phase={phase}"
        lines.append(
            f'<text x="{x1:.2f}" y="{y_axis-28}" font-size="10" font-family="Menlo, monospace" fill="#111827" '
            f'data-feature-index="{idx}" class="feature-label">{label}{extra}</text>'
        )

    frame_offset = frame - 1
    cds_seq = record.sequence[start_1based - 1 + frame_offset : end_1based]
    aa = record.translate(frame=frame, to_stop=False)
    local_aa = []
    start_codon_index = (start_1based - 1 + frame_offset) // 3
    aa_count = len(cds_seq) // 3
    for i in range(aa_count):
        aa_idx = start_codon_index + i
        local_aa.append(aa[aa_idx] if aa_idx < len(aa) else "X")

    y_aa = 150
    lines.append(f'<text x="{left}" y="{y_aa-12}" font-size="12" font-family="Menlo, monospace" fill="#334155">Translation frame {frame}</text>')
    for i, residue in enumerate(local_aa):
        codon_start = start_1based + frame_offset + i * 3
        codon_end = codon_start + 2
        if codon_end > end_1based:
            break
        x1 = x_for_pos(codon_start)
        x2 = x_for_pos(codon_end)
        mid = (x1 + x2) / 2
        fill = "#fca5a5" if residue == "*" else "#dbeafe"
        codon = record.sequence[codon_start - 1 : codon_end]
        lines.append(
            f'<rect x="{x1:.2f}" y="{y_aa}" width="{max(4.0, x2-x1):.2f}" height="18" rx="2" fill="{fill}" stroke="#93c5fd" stroke-width="0.5" '
            f'data-codon-start="{codon_start}" data-codon-end="{codon_end}" data-residue="{residue}" class="codon-cell">'
            f'<title>codon {codon_start}-{codon_end}: {codon} -> {residue}</title></rect>'
        )
        lines.append(f'<text x="{mid:.2f}" y="{y_aa+13}" text-anchor="middle" font-size="10" font-family="Menlo, monospace" fill="#0f172a">{residue}</text>')

    y_nt = 210
    step = max(10, (end_1based - start_1based + 1) // 12)
    for pos in range(start_1based, end_1based + 1, step):
        x = x_for_pos(pos)
        lines.append(f'<line x1="{x:.2f}" y1="{y_nt-12}" x2="{x:.2f}" y2="{y_nt-6}" stroke="#334155" stroke-width="1"/>')
        lines.append(f'<text x="{x:.2f}" y="{y_nt}" text-anchor="middle" font-size="10" font-family="Menlo, monospace" fill="#334155">{pos}</text>')

    lines.append("</svg>")
    return {"start_1based": start_1based, "end_1based": end_1based, "frame": frame, "svg": "\n".join(lines)}


def alignment_heatmap_svg(alignment: List[str]) -> Dict[str, Any]:
    consensus = alignment_consensus(alignment)
    matrix = consensus["identity_matrix_pct"]
    n = len(matrix)
    if n == 0:
        raise ValueError("Empty alignment")
    cell = 28
    margin = 70
    width = margin + n * cell + 30
    height = margin + n * cell + 30
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    lines.append('<rect width="100%" height="100%" fill="#f8fafc"/>')
    for i in range(n):
        x = margin + i * cell + cell / 2
        y = margin - 10
        lines.append(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" font-size="10" font-family="Menlo, monospace" fill="#334155">S{i+1}</text>')
        x2 = margin - 12
        y2 = margin + i * cell + cell / 2 + 3
        lines.append(f'<text x="{x2:.1f}" y="{y2:.1f}" text-anchor="end" font-size="10" font-family="Menlo, monospace" fill="#334155">S{i+1}</text>')
    for i in range(n):
        for j in range(n):
            val = float(matrix[i][j])
            t = max(0.0, min(1.0, val / 100.0))
            r = int(240 - 170 * t)
            g = int(248 - 40 * t)
            b = int(255 - 120 * t)
            fill = f"rgb({r},{g},{b})"
            x = margin + j * cell
            y = margin + i * cell
            lines.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{fill}" stroke="#cbd5e1" stroke-width="1"><title>S{i+1} vs S{j+1}: {val:.2f}%</title></rect>')
            if n <= 12:
                lines.append(f'<text x="{x+cell/2:.1f}" y="{y+cell/2+3:.1f}" text-anchor="middle" font-size="9" font-family="Menlo, monospace" fill="#0f172a">{val:.0f}</text>')
    lines.append("</svg>")
    return {"row_count": n, "svg": "\n".join(lines), "identity_matrix_pct": matrix}


def sequence_analytics_svg(
    record: SequenceRecord,
    start_1based: int = 1,
    end_1based: int | None = None,
    window: int = 120,
    step: int = 20,
) -> Dict[str, Any]:
    if end_1based is None:
        end_1based = record.length
    start_1based = max(1, int(start_1based))
    end_1based = min(record.length, int(end_1based))
    if start_1based > end_1based:
        raise ValueError("Invalid window range")
    window = max(30, int(window))
    step = max(5, int(step))
    seq = record.sequence[start_1based - 1 : end_1based]
    if len(seq) < 30:
        raise ValueError("Sequence range too short for analytics")

    xs: List[float] = []
    gc_pct: List[float] = []
    gc_skew: List[float] = []
    complexity: List[float] = []
    stop_density: List[float] = []
    points = 0
    for i in range(0, max(1, len(seq) - window + 1), step):
        wseq = seq[i : i + window]
        if len(wseq) < 20:
            continue
        center = start_1based + i + len(wseq) / 2.0
        points += 1
        g = wseq.count("G")
        c = wseq.count("C")
        gc = 100.0 * (g + c) / max(1, len(wseq))
        skew = (g - c) / max(1, g + c)
        kmers: Dict[str, int] = {}
        for j in range(len(wseq) - 1):
            kmer = wseq[j : j + 2]
            kmers[kmer] = kmers.get(kmer, 0) + 1
        total_k = max(1, sum(kmers.values()))
        ent = 0.0
        for value in kmers.values():
            p = value / total_k
            ent -= p * math.log2(p)
        comp = min(1.0, max(0.0, ent / 4.0))
        stops = 0
        codons = max(1, len(wseq) // 3)
        for j in range(0, len(wseq) - 2, 3):
            if wseq[j : j + 3] in {"TAA", "TAG", "TGA"}:
                stops += 1
        stop_density_value = stops / codons

        xs.append(center)
        gc_pct.append(gc)
        gc_skew.append(skew)
        complexity.append(comp)
        stop_density.append(stop_density_value)

    if not xs:
        raise ValueError("No analytics points generated")

    width = 1200
    height = 420
    margin_l = 70
    margin_r = 24
    margin_t = 26
    panel_h = 82
    panel_gap = 12
    plot_w = width - margin_l - margin_r

    x_min = float(start_1based)
    x_max = float(end_1based)

    def x_for(p: float) -> float:
        return margin_l + (p - x_min) * plot_w / max(1.0, x_max - x_min)

    def to_poly(y_top: float, vals: List[float], vmin: float, vmax: float) -> str:
        pts = []
        rng = max(1e-9, vmax - vmin)
        for x, value in zip(xs, vals):
            y = y_top + panel_h - ((value - vmin) / rng) * panel_h
            pts.append(f"{x_for(x):.2f},{y:.2f}")
        return " ".join(pts)

    panels = [
        ("GC %", gc_pct, 0.0, 100.0, "#0ea5e9"),
        ("GC skew", gc_skew, -1.0, 1.0, "#f97316"),
        ("Complexity (entropy)", complexity, 0.0, 1.0, "#22c55e"),
        ("Stop codon density", stop_density, 0.0, max(0.25, max(stop_density) * 1.1), "#a855f7"),
    ]

    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    lines.append('<rect width="100%" height="100%" fill="#f8fafc"/>')
    lines.append(
        f'<text x="{margin_l}" y="18" font-size="13" font-family="Menlo, monospace" fill="#0f172a">'
        f'Sequence analytics: {record.name}  {start_1based}..{end_1based}</text>'
    )
    for idx, (label, vals, vmin, vmax, color) in enumerate(panels):
        y_top = margin_t + idx * (panel_h + panel_gap)
        lines.append(f'<rect x="{margin_l}" y="{y_top}" width="{plot_w}" height="{panel_h}" fill="#ffffff" stroke="#dbe5f3"/>')
        lines.append(f'<text x="8" y="{y_top + 16}" font-size="11" font-family="Menlo, monospace" fill="#334155">{label}</text>')
        for tick in range(5):
            gx = margin_l + tick * (plot_w / 4)
            lines.append(f'<line x1="{gx:.2f}" y1="{y_top}" x2="{gx:.2f}" y2="{y_top + panel_h}" stroke="#eef2f7" stroke-width="1"/>')
        lines.append(
            f'<polyline points="{to_poly(y_top, vals, vmin, vmax)}" fill="none" stroke="{color}" stroke-width="2">'
            f'<title>{label}</title></polyline>'
        )

    tick_y = margin_t + len(panels) * (panel_h + panel_gap) - panel_gap + 16
    for tick in range(6):
        pos = int(round(x_min + tick * (x_max - x_min) / 5))
        x = x_for(float(pos))
        lines.append(f'<line x1="{x:.2f}" y1="{tick_y-10}" x2="{x:.2f}" y2="{tick_y-4}" stroke="#334155"/>')
        lines.append(f'<text x="{x:.2f}" y="{tick_y+8}" text-anchor="middle" font-size="10" font-family="Menlo, monospace" fill="#334155">{pos}</text>')
    lines.append("</svg>")

    return {
        "start_1based": start_1based,
        "end_1based": end_1based,
        "window": window,
        "step": step,
        "point_count": points,
        "gc_mean": round(sum(gc_pct) / len(gc_pct), 3),
        "gc_min": round(min(gc_pct), 3),
        "gc_max": round(max(gc_pct), 3),
        "svg": "\n".join(lines),
    }


def comparison_lens_svg(seq_a: str, seq_b: str, window: int = 60) -> Dict[str, Any]:
    a = sanitize_sequence(seq_a)
    b = sanitize_sequence(seq_b)
    if not a or not b:
        raise ValueError("seq_a and seq_b are required")
    window = max(20, int(window))
    aln = needleman_wunsch(a, b)
    aligned_a = aln["aligned_a"]
    aligned_b = aln["aligned_b"]
    n = len(aligned_a)
    if n == 0:
        raise ValueError("Alignment empty")

    centers: List[int] = []
    divergence: List[float] = []
    confidence: List[float] = []
    for i in range(0, max(1, n - window + 1), max(5, window // 3)):
        wa = aligned_a[i : i + window]
        wb = aligned_b[i : i + window]
        if len(wa) < 10:
            continue
        mismatches = 0
        gaps = 0
        for ca, cb in zip(wa, wb):
            if ca == "-" or cb == "-":
                gaps += 1
            elif ca != cb:
                mismatches += 1
        total = max(1, len(wa))
        div = (mismatches + gaps) / total
        conf = max(0.0, min(1.0, 1.0 - div))
        centers.append(i + len(wa) // 2 + 1)
        divergence.append(div)
        confidence.append(conf)

    width = 1200
    height = 260
    margin_l = 70
    margin_r = 30
    margin_t = 26
    plot_h = 170
    plot_w = width - margin_l - margin_r

    def x_for(pos: float) -> float:
        return margin_l + (pos - 1.0) * plot_w / max(1.0, n - 1.0)

    def y_for(value: float) -> float:
        return margin_t + plot_h - value * plot_h

    div_pts = " ".join(f"{x_for(center):.2f},{y_for(div):.2f}" for center, div in zip(centers, divergence))
    conf_pts = " ".join(f"{x_for(center):.2f},{y_for(conf):.2f}" for center, conf in zip(centers, confidence))

    idx_sorted = sorted(range(len(divergence)), key=lambda i: divergence[i], reverse=True)
    hotspots = []
    for idx in idx_sorted[:5]:
        center = centers[idx]
        start = max(1, center - window // 2)
        end = min(n, center + window // 2)
        hotspots.append({"start_aln_1based": start, "end_aln_1based": end, "divergence": round(divergence[idx], 4)})

    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    lines.append('<rect width="100%" height="100%" fill="#f8fafc"/>')
    lines.append(f'<text x="{margin_l}" y="18" font-size="13" font-family="Menlo, monospace" fill="#0f172a">Comparison lens (alignment length={n})</text>')
    lines.append(f'<rect x="{margin_l}" y="{margin_t}" width="{plot_w}" height="{plot_h}" fill="#ffffff" stroke="#dbe5f3"/>')
    for tick in range(5):
        gy = margin_t + tick * (plot_h / 4)
        lines.append(f'<line x1="{margin_l}" y1="{gy:.2f}" x2="{margin_l+plot_w}" y2="{gy:.2f}" stroke="#eef2f7"/>')
    lines.append(f'<polyline points="{div_pts}" fill="none" stroke="#ef4444" stroke-width="2"><title>Divergence</title></polyline>')
    lines.append(f'<polyline points="{conf_pts}" fill="none" stroke="#22c55e" stroke-width="2"><title>Confidence proxy</title></polyline>')
    for hotspot in hotspots:
        x1 = x_for(hotspot["start_aln_1based"])
        x2 = x_for(hotspot["end_aln_1based"])
        lines.append(
            f'<rect x="{x1:.2f}" y="{margin_t}" width="{max(1.0, x2-x1):.2f}" height="{plot_h}" fill="#fecaca" opacity="0.22">'
            f'<title>Hotspot {hotspot["start_aln_1based"]}-{hotspot["end_aln_1based"]}: div={hotspot["divergence"]}</title></rect>'
        )
    lines.append(f'<text x="{margin_l}" y="{margin_t+plot_h+18}" font-size="11" font-family="Menlo, monospace" fill="#334155">Red: divergence, Green: confidence proxy</text>')
    lines.append("</svg>")
    return {
        "alignment_length": n,
        "identity_pct": aln.get("identity_pct", 0.0),
        "window": window,
        "hotspots": hotspots,
        "svg": "\n".join(lines),
    }


def _pairwise_distance(a: str, b: str) -> float:
    aln = needleman_wunsch(a, b)
    return max(0.0, 100.0 - float(aln["identity_pct"]))


def phylo_upgma(sequences: List[str]) -> Dict[str, Any]:
    seqs = [_parse_plain_sequence(seq) for seq in sequences if str(seq).strip()]
    if len(seqs) < 2:
        raise ValueError("Need at least two sequences")
    clusters: Dict[int, Dict[str, Any]] = {i: {"members": [i], "label": f"S{i+1}"} for i in range(len(seqs))}
    dist: Dict[Tuple[int, int], float] = {}
    for i in range(len(seqs)):
        for j in range(i + 1, len(seqs)):
            dist[(i, j)] = _pairwise_distance(seqs[i], seqs[j])
    next_id = len(seqs)
    merges = []
    while len(clusters) > 1:
        ids = sorted(clusters.keys())
        best = None
        best_d = float("inf")
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a, b = ids[i], ids[j]
                key = (a, b) if a < b else (b, a)
                d = dist.get(key, float("inf"))
                if d < best_d:
                    best_d = d
                    best = (a, b)
        if best is None:
            break
        a, b = best
        new_members = clusters[a]["members"] + clusters[b]["members"]
        new_label = f"({clusters[a]['label']}:{best_d/2:.2f},{clusters[b]['label']}:{best_d/2:.2f})"
        merges.append({"left": a, "right": b, "distance": round(best_d, 3), "new_id": next_id, "newick_partial": new_label})
        clusters[next_id] = {"members": new_members, "label": new_label}
        for k in list(clusters.keys()):
            if k in (a, b, next_id):
                continue
            vals = []
            for x in clusters[k]["members"]:
                for y in new_members:
                    key = (x, y) if x < y else (y, x)
                    if key in dist:
                        vals.append(dist[key])
            if vals:
                key = (k, next_id) if k < next_id else (next_id, k)
                dist[key] = sum(vals) / len(vals)
        del clusters[a]
        del clusters[b]
        next_id += 1
    root = next(iter(clusters.values()))
    return {"sequence_count": len(seqs), "merges": merges, "newick": root["label"] + ";"}


def _parse_feature_bounds(loc: str) -> Tuple[int, int]:
    nums = [int(x) for x in "".join(ch if ch.isdigit() else " " for ch in str(loc)).split()]
    if len(nums) < 2:
        return 0, 0
    a, b = nums[0], nums[-1]
    if a > b:
        a, b = b, a
    return a, b


def translated_feature_report(
    record: SequenceRecord,
    include_slippage: bool = False,
    slip_pos_1based: int = 0,
    slip_type: str = "-1",
) -> Dict[str, Any]:
    rows = []
    for idx, feature in enumerate(record.features):
        if feature.key.lower() != "cds":
            continue
        a, b = _parse_feature_bounds(feature.location)
        if a <= 0 or b <= 0:
            continue
        region = record.sequence[a - 1 : b]
        codon_start = int(str(feature.qualifiers.get("codon_start", "1")) or "1")
        codon_start = max(1, min(3, codon_start))
        seq = region[codon_start - 1 :]
        slippage_applied = None
        if include_slippage and slip_pos_1based >= a and slip_pos_1based <= b and seq:
            rel = slip_pos_1based - a
            if slip_type == "-1" and 0 <= rel < len(seq):
                seq = seq[:rel] + seq[rel + 1 :]
                slippage_applied = {"type": "-1", "position_1based": slip_pos_1based}
            elif slip_type == "+1" and 0 <= rel < len(seq):
                seq = seq[: rel + 1] + seq[rel] + seq[rel + 1 :]
                slippage_applied = {"type": "+1", "position_1based": slip_pos_1based}
        aa = []
        numbering = []
        for i in range(0, len(seq) - 2, 3):
            codon = seq[i : i + 3]
            residue = CODON_TABLE.get(codon, "X")
            aa.append(residue)
            numbering.append(
                {
                    "aa_index_1based": len(aa),
                    "codon": codon,
                    "residue": residue,
                    "genomic_codon_start_1based": a + codon_start - 1 + i,
                    "genomic_codon_end_1based": a + codon_start - 1 + i + 2,
                }
            )
        rows.append(
            {
                "feature_index": idx,
                "label": feature.qualifiers.get("label") or feature.qualifiers.get("gene") or f"CDS_{idx+1}",
                "location": feature.location,
                "codon_start": codon_start,
                "translation_length_aa": len(aa),
                "translation": "".join(aa),
                "numbering": numbering,
                "slippage_applied": slippage_applied,
            }
        )
    return {"count": len(rows), "translated_features": rows}


def translated_feature_edit(
    record: SequenceRecord,
    feature_index: int,
    aa_index_1based: int,
    new_residue: str,
    host: str = "ecoli",
) -> Dict[str, Any]:
    if feature_index < 0 or feature_index >= len(record.features):
        raise ValueError("Invalid feature index")
    feature = record.features[feature_index]
    if feature.key.lower() != "cds":
        raise ValueError("Selected feature is not CDS")
    a, b = _parse_feature_bounds(feature.location)
    if a <= 0 or b <= 0:
        raise ValueError("Invalid CDS location")
    codon_start = int(str(feature.qualifiers.get("codon_start", "1")) or "1")
    codon_start = max(1, min(3, codon_start))
    cds_len = max(0, b - a + 1 - (codon_start - 1))
    aa_len = cds_len // 3
    if aa_index_1based < 1 or aa_index_1based > aa_len:
        raise ValueError("AA index out of range")
    residue = str(new_residue).strip().upper()
    if len(residue) != 1:
        raise ValueError("new_residue must be a single amino acid code")
    new_codon = _reverse_translate_protein(residue, host=host)[:3]
    codon_genomic_start = a + codon_start - 1 + (aa_index_1based - 1) * 3
    codon_genomic_end = codon_genomic_start + 2
    old_codon = record.sequence[codon_genomic_start - 1 : codon_genomic_end]
    edited = _apply_sequence_edit(
        record,
        op="replace",
        start_1based=codon_genomic_start,
        end_1based=codon_genomic_end,
        value=new_codon,
    )
    return {
        "edited": True,
        "feature_index": feature_index,
        "aa_index_1based": aa_index_1based,
        "old_codon": old_codon,
        "new_codon": new_codon,
        "new_residue": residue,
        "codon_genomic_start_1based": codon_genomic_start,
        "codon_genomic_end_1based": codon_genomic_end,
        "name": edited.name,
        "length": edited.length,
        "gc": round(edited.gc_content(), 2),
        "sequence": edited.sequence,
    }


def protein_edit_sequence(
    record: SequenceRecord,
    aa_index_1based: int,
    new_residue: str,
    frame: int = 1,
    host: str = "ecoli",
) -> Dict[str, Any]:
    if frame not in {1, 2, 3}:
        raise ValueError("frame must be 1,2,3")
    if aa_index_1based < 1:
        raise ValueError("aa_index_1based must be >= 1")
    residue = str(new_residue).strip().upper()
    if len(residue) != 1:
        raise ValueError("new_residue must be one amino acid letter")
    codon_start = frame + (aa_index_1based - 1) * 3
    codon_end = codon_start + 2
    if codon_end > record.length:
        raise ValueError("AA index exceeds translated range")
    old_codon = record.sequence[codon_start - 1 : codon_end]
    new_codon = _reverse_translate_protein(residue, host=host)[:3]
    edited = _apply_sequence_edit(
        record,
        op="replace",
        start_1based=codon_start,
        end_1based=codon_end,
        value=new_codon,
    )
    return {
        "edited": True,
        "mode": "protein_edit",
        "frame": frame,
        "aa_index_1based": aa_index_1based,
        "old_codon": old_codon,
        "new_codon": new_codon,
        "new_residue": residue,
        "codon_start_1based": codon_start,
        "codon_end_1based": codon_end,
        "name": edited.name,
        "sequence": edited.sequence,
        "length": edited.length,
        "gc": round(edited.gc_content(), 2),
    }


def search_entities(
    record: SequenceRecord,
    query: str,
    primers: List[str] | None = None,
) -> Dict[str, Any]:
    q = str(query or "").strip().upper()
    if not q:
        raise ValueError("query is required")
    seq = record.sequence
    is_dna_query = all(ch in DNA_ALPHABET for ch in q)
    motif_hits = find_all_occurrences(seq, q, circular=record.topology == "circular") if is_dna_query else []
    motif_rows = [{"start_1based": pos + 1, "end_1based": pos + len(q)} for pos in motif_hits]
    feature_rows = []
    for i, feature in enumerate(record.features):
        label = (feature.qualifiers.get("label") or feature.qualifiers.get("gene") or feature.key).upper()
        if q in label or q in feature.key.upper() or q in feature.location.upper():
            feature_rows.append({"feature_index": i, "key": feature.key, "location": feature.location, "label": label})
    primer_rows = []
    for idx, primer in enumerate(primers or [], start=1):
        primer_seq = sanitize_sequence(str(primer))
        if not primer_seq:
            continue
        starts = find_all_occurrences(seq, primer_seq, circular=record.topology == "circular")
        if starts:
            primer_rows.append(
                {
                    "primer_index": idx,
                    "primer": primer_seq,
                    "match_count": len(starts),
                    "positions_1based": [start + 1 for start in starts[:50]],
                }
            )
        elif q in primer_seq:
            primer_rows.append({"primer_index": idx, "primer": primer_seq, "match_count": 0, "positions_1based": []})
    return {
        "query": q,
        "motif_hit_count": len(motif_rows),
        "motif_hits": motif_rows,
        "feature_hit_count": len(feature_rows),
        "feature_hits": feature_rows,
        "primer_hit_count": len(primer_rows),
        "primer_hits": primer_rows,
    }


def cdna_to_genome_map(
    cdna_sequence: str,
    genome_sequence: str,
    min_exon_bp: int = 14,
    max_intron_bp: int = 200000,
) -> Dict[str, Any]:
    cdna = sanitize_sequence(cdna_sequence)
    genome = sanitize_sequence(genome_sequence)
    if not cdna or not genome:
        raise ValueError("cdna and genome sequences are required")
    i = 0
    g_cursor = 0
    exons: List[Dict[str, int]] = []
    while i < len(cdna):
        best = None
        max_len = min(len(cdna) - i, 300)
        for ln in range(max_len, min_exon_bp - 1, -1):
            frag = cdna[i : i + ln]
            search_start = g_cursor
            search_end = min(len(genome), g_cursor + max_intron_bp + ln)
            hit = genome.find(frag, search_start, search_end)
            if hit != -1:
                best = (hit, ln)
                break
        if not best:
            break
        hit, ln = best
        exons.append(
            {
                "cdna_start_1based": i + 1,
                "cdna_end_1based": i + ln,
                "genome_start_1based": hit + 1,
                "genome_end_1based": hit + ln,
                "length_bp": ln,
            }
        )
        i += ln
        g_cursor = hit + ln
    introns = []
    for k in range(len(exons) - 1):
        introns.append(
            {
                "from_exon": k + 1,
                "to_exon": k + 2,
                "genome_intron_start_1based": exons[k]["genome_end_1based"] + 1,
                "genome_intron_end_1based": exons[k + 1]["genome_start_1based"] - 1,
                "length_bp": max(0, exons[k + 1]["genome_start_1based"] - exons[k]["genome_end_1based"] - 1),
            }
        )
    aligned_bp = sum(exon["length_bp"] for exon in exons)
    return {
        "cdna_length": len(cdna),
        "genome_length": len(genome),
        "aligned_bp": aligned_bp,
        "coverage_pct": round(100.0 * aligned_bp / max(1, len(cdna)), 2),
        "exon_count": len(exons),
        "exons": exons,
        "introns": introns,
        "unmapped_cdna_tail_bp": max(0, len(cdna) - aligned_bp),
    }


def anneal_oligos(forward: str, reverse: str, min_overlap: int = 10) -> Dict[str, Any]:
    fwd = _parse_plain_sequence(forward)
    rev = _parse_plain_sequence(reverse)
    rev_rc = rev.translate(str.maketrans("ACGTN", "TGCAN"))[::-1]
    best = 0
    best_pos = -1
    max_k = min(len(fwd), len(rev_rc))
    for k in range(max_k, min_overlap - 1, -1):
        if fwd[-k:] == rev_rc[:k]:
            best = k
            best_pos = len(fwd) - k
            break
    assembled = fwd + (rev_rc[best:] if best > 0 else "")
    return {
        "forward_len": len(fwd),
        "reverse_len": len(rev),
        "reverse_rc": rev_rc,
        "overlap_bp": best,
        "overlap_start_in_forward_1based": best_pos + 1 if best_pos >= 0 else None,
        "assembled_sequence": assembled if best > 0 else None,
    }


def handle_analysis_endpoint(path: str, payload: Dict[str, Any], get_record: RecordGetter) -> Dict[str, Any] | None:
    if path == "/api/translate":
        record = get_record()
        frame = int(payload.get("frame", 1))
        to_stop = bool(payload.get("to_stop", False))
        return {"protein": record.translate(frame=frame, to_stop=to_stop)}
    if path == "/api/translated-features":
        return translated_feature_report(
            get_record(),
            include_slippage=bool(payload.get("include_slippage", False)),
            slip_pos_1based=int(payload.get("slip_pos_1based", 0)),
            slip_type=str(payload.get("slip_type", "-1")),
        )
    if path == "/api/sequence-tracks":
        record = get_record()
        return sequence_track_svg(
            record,
            start_1based=int(payload.get("start", 1)),
            end_1based=int(payload.get("end", min(record.length, 300))),
            frame=int(payload.get("frame", 1)),
        )
    if path == "/api/sequence-analytics-svg":
        record = get_record()
        return sequence_analytics_svg(
            record,
            start_1based=int(payload.get("start", 1)),
            end_1based=int(payload.get("end", record.length)),
            window=int(payload.get("window", 120)),
            step=int(payload.get("step", 20)),
        )
    if path == "/api/reverse-translate":
        protein = str(payload.get("protein", "")).strip().upper()
        host = str(payload.get("host", "ecoli")).lower()
        dna = _reverse_translate_protein(protein, host=host)
        return {"protein": protein, "host": host, "dna": dna, "length": len(dna)}
    if path == "/api/pairwise-align":
        seq_a = str(payload.get("seq_a", ""))
        seq_b = str(payload.get("seq_b", ""))
        mode = str(payload.get("mode", "dna")).lower()
        if mode == "protein":
            return needleman_wunsch_protein(seq_a, seq_b)
        out = needleman_wunsch(seq_a, seq_b)
        out["mode"] = "dna"
        return out
    if path == "/api/comparison-lens-svg":
        seq_a = str(payload.get("seq_a", ""))
        seq_b = str(payload.get("seq_b", ""))
        if not seq_a.strip():
            seq_a = get_record().sequence
        return comparison_lens_svg(seq_a=seq_a, seq_b=seq_b, window=int(payload.get("window", 60)))
    if path == "/api/multi-align":
        sequences = payload.get("sequences", [])
        if isinstance(sequences, str):
            sequences = [item.strip() for item in sequences.splitlines() if item.strip()]
        return multi_align_to_reference([str(item) for item in sequences])
    if path == "/api/contig-assemble":
        reads = payload.get("reads", [])
        if isinstance(reads, str):
            reads = [item.strip() for item in reads.splitlines() if item.strip()]
        return contig_assemble([str(item) for item in reads], min_overlap=int(payload.get("min_overlap", 20)))
    if path == "/api/msa":
        sequences = payload.get("sequences", [])
        if isinstance(sequences, str):
            sequences = [item.strip() for item in sequences.splitlines() if item.strip()]
        method = str(payload.get("method", "progressive")).lower()
        if method == "progressive":
            return progressive_msa([str(item) for item in sequences])
        return external_msa(method, [str(item) for item in sequences])
    if path == "/api/alignment-consensus":
        alignment = payload.get("alignment", [])
        if isinstance(alignment, str):
            alignment = [item.strip() for item in alignment.splitlines() if item.strip()]
        return alignment_consensus([str(item) for item in alignment])
    if path == "/api/alignment-heatmap-svg":
        alignment = payload.get("alignment", [])
        if isinstance(alignment, str):
            alignment = [item.strip() for item in alignment.splitlines() if item.strip()]
        return alignment_heatmap_svg([str(item) for item in alignment])
    if path == "/api/phylo-tree":
        sequences = payload.get("sequences", [])
        if isinstance(sequences, str):
            sequences = [item.strip() for item in sequences.splitlines() if item.strip()]
        return phylo_upgma([str(item) for item in sequences])
    if path == "/api/anneal-oligos":
        return anneal_oligos(
            str(payload.get("forward", "")),
            str(payload.get("reverse", "")),
            min_overlap=int(payload.get("min_overlap", 10)),
        )
    if path == "/api/protein-edit":
        return protein_edit_sequence(
            get_record(),
            aa_index_1based=int(payload.get("aa_index_1based", 1)),
            new_residue=str(payload.get("new_residue", "A")),
            frame=int(payload.get("frame", 1)),
            host=str(payload.get("host", "ecoli")),
        )
    if path == "/api/translated-feature-edit":
        return translated_feature_edit(
            get_record(),
            feature_index=int(payload.get("feature_index", 0)),
            aa_index_1based=int(payload.get("aa_index_1based", 1)),
            new_residue=str(payload.get("new_residue", "A")),
            host=str(payload.get("host", "ecoli")),
        )
    if path == "/api/cdna-map":
        return cdna_to_genome_map(
            cdna_sequence=str(payload.get("cdna_sequence", "")),
            genome_sequence=str(payload.get("genome_sequence", "")),
            min_exon_bp=int(payload.get("min_exon_bp", 14)),
            max_intron_bp=int(payload.get("max_intron_bp", 200000)),
        )
    if path == "/api/search-entities":
        primers = payload.get("primers", [])
        if isinstance(primers, str):
            primers = [item.strip() for item in primers.split(",") if item.strip()]
        return search_entities(
            get_record(),
            query=str(payload.get("query", "")),
            primers=[str(item) for item in primers],
        )
    return None
