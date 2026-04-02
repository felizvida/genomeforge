#!/usr/bin/env python3
"""
A Genome Forge DNA utility CLI.

Implemented feature set:
- Parse FASTA and a subset of GenBank (LOCUS/FEATURES/ORIGIN)
- Sequence statistics and transformations
- Translation and ORF discovery
- Restriction digest simulation for linear and circular molecules
- Basic primer design and virtual PCR simulation
- Codon optimization for selected hosts
- SVG plasmid/sequence map export
- Export to FASTA and GenBank
"""

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

IUPAC_DNA_CODES = "ACGTRYSWKMBDHVN"
DNA_ALPHABET = set(IUPAC_DNA_CODES)
IUPAC_BASE_SETS: Dict[str, frozenset[str]] = {
    "A": frozenset("A"),
    "C": frozenset("C"),
    "G": frozenset("G"),
    "T": frozenset("T"),
    "R": frozenset("AG"),
    "Y": frozenset("CT"),
    "S": frozenset("GC"),
    "W": frozenset("AT"),
    "K": frozenset("GT"),
    "M": frozenset("AC"),
    "B": frozenset("CGT"),
    "D": frozenset("AGT"),
    "H": frozenset("ACT"),
    "V": frozenset("ACG"),
    "N": frozenset("ACGT"),
}

CODON_TABLE = {
    "TTT": "F", "TTC": "F", "TTA": "L", "TTG": "L",
    "TCT": "S", "TCC": "S", "TCA": "S", "TCG": "S",
    "TAT": "Y", "TAC": "Y", "TAA": "*", "TAG": "*",
    "TGT": "C", "TGC": "C", "TGA": "*", "TGG": "W",
    "CTT": "L", "CTC": "L", "CTA": "L", "CTG": "L",
    "CCT": "P", "CCC": "P", "CCA": "P", "CCG": "P",
    "CAT": "H", "CAC": "H", "CAA": "Q", "CAG": "Q",
    "CGT": "R", "CGC": "R", "CGA": "R", "CGG": "R",
    "ATT": "I", "ATC": "I", "ATA": "I", "ATG": "M",
    "ACT": "T", "ACC": "T", "ACA": "T", "ACG": "T",
    "AAT": "N", "AAC": "N", "AAA": "K", "AAG": "K",
    "AGT": "S", "AGC": "S", "AGA": "R", "AGG": "R",
    "GTT": "V", "GTC": "V", "GTA": "V", "GTG": "V",
    "GCT": "A", "GCC": "A", "GCA": "A", "GCG": "A",
    "GAT": "D", "GAC": "D", "GAA": "E", "GAG": "E",
    "GGT": "G", "GGC": "G", "GGA": "G", "GGG": "G",
}

AA_TO_CODONS: Dict[str, List[str]] = {}
for codon, aa in CODON_TABLE.items():
    AA_TO_CODONS.setdefault(aa, []).append(codon)

# Enzyme data: recognition site and cut offset from site start.
ENZYMES: Dict[str, Tuple[str, int]] = {
    "EcoRI": ("GAATTC", 1),
    "BamHI": ("GGATCC", 1),
    "HindIII": ("AAGCTT", 1),
    "XhoI": ("CTCGAG", 1),
    "XbaI": ("TCTAGA", 1),
    "SpeI": ("ACTAGT", 1),
    "PstI": ("CTGCAG", 5),
    "NotI": ("GCGGCCGC", 2),
    "NheI": ("GCTAGC", 1),
    "KpnI": ("GGTACC", 5),
}

# Minimal host codon preferences for fast practical optimization.
HOST_PREFERRED_CODONS: Dict[str, Dict[str, str]] = {
    "ecoli": {
        "A": "GCG", "R": "CGT", "N": "AAC", "D": "GAT", "C": "TGC",
        "Q": "CAG", "E": "GAA", "G": "GGC", "H": "CAC", "I": "ATC",
        "L": "CTG", "K": "AAA", "M": "ATG", "F": "TTC", "P": "CCG",
        "S": "TCG", "T": "ACC", "W": "TGG", "Y": "TAC", "V": "GTG",
        "*": "TAA",
    },
    "yeast": {
        "A": "GCT", "R": "AGA", "N": "AAT", "D": "GAT", "C": "TGT",
        "Q": "CAA", "E": "GAA", "G": "GGT", "H": "CAT", "I": "ATT",
        "L": "TTG", "K": "AAA", "M": "ATG", "F": "TTT", "P": "CCA",
        "S": "TCT", "T": "ACT", "W": "TGG", "Y": "TAT", "V": "GTT",
        "*": "TAA",
    },
}

FEATURE_COLORS = {
    "cds": "#3b82f6",
    "gene": "#ef4444",
    "promoter": "#22c55e",
    "terminator": "#f59e0b",
    "misc_feature": "#8b5cf6",
    "default": "#64748b",
}

IUPAC_DNA_COMPLEMENTS = {
    "A": "T",
    "C": "G",
    "G": "C",
    "T": "A",
    "R": "Y",
    "Y": "R",
    "S": "S",
    "W": "W",
    "K": "M",
    "M": "K",
    "B": "V",
    "D": "H",
    "H": "D",
    "V": "B",
    "N": "N",
}
RC_TABLE = str.maketrans(
    "".join(IUPAC_DNA_COMPLEMENTS.keys()) + "".join(base.lower() for base in IUPAC_DNA_COMPLEMENTS),
    "".join(IUPAC_DNA_COMPLEMENTS.values()) + "".join(base.lower() for base in IUPAC_DNA_COMPLEMENTS.values()),
)

# SantaLucia-style nearest-neighbor parameters for DNA duplex formation.
# Values: deltaH (kcal/mol), deltaS (cal/mol*K)
NN_PARAMS: Dict[str, Tuple[float, float]] = {
    "AA": (-7.9, -22.2), "TT": (-7.9, -22.2),
    "AT": (-7.2, -20.4),
    "TA": (-7.2, -21.3),
    "CA": (-8.5, -22.7), "TG": (-8.5, -22.7),
    "GT": (-8.4, -22.4), "AC": (-8.4, -22.4),
    "CT": (-7.8, -21.0), "AG": (-7.8, -21.0),
    "GA": (-8.2, -22.2), "TC": (-8.2, -22.2),
    "CG": (-10.6, -27.2),
    "GC": (-9.8, -24.4),
    "GG": (-8.0, -19.9), "CC": (-8.0, -19.9),
}


@dataclass
class Feature:
    key: str
    location: str
    qualifiers: Dict[str, str] = field(default_factory=dict)


@dataclass
class SequenceRecord:
    name: str
    sequence: str
    molecule: str = "DNA"
    topology: str = "linear"  # linear | circular
    features: List[Feature] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.sequence = sanitize_sequence(self.sequence)

    @property
    def length(self) -> int:
        return len(self.sequence)

    def gc_content(self) -> float:
        if not self.sequence:
            return 0.0
        gc = sum(1 for b in self.sequence if b in "GC")
        return gc / self.length * 100.0

    def reverse_complement(self) -> "SequenceRecord":
        return SequenceRecord(
            name=f"{self.name}_revcomp",
            sequence=self.sequence.translate(RC_TABLE)[::-1],
            molecule=self.molecule,
            topology=self.topology,
            features=[],
        )

    def transcribe(self) -> str:
        return self.sequence.replace("T", "U")

    def translate(self, frame: int = 1, to_stop: bool = False) -> str:
        if frame not in (1, 2, 3):
            raise ValueError("Frame must be 1, 2, or 3")
        seq = self.sequence[frame - 1 :]
        aa: List[str] = []
        for i in range(0, len(seq) - 2, 3):
            codon = seq[i : i + 3]
            residue = CODON_TABLE.get(codon, "X")
            if residue == "*" and to_stop:
                break
            aa.append(residue)
        return "".join(aa)

    def find_orfs(self, min_aa_len: int = 50) -> List[Tuple[int, int, int, str]]:
        """
        Return ORFs on forward strand as tuples:
        (start_1based, end_1based_inclusive, frame, protein)
        """
        results: List[Tuple[int, int, int, str]] = []
        stops = {"TAA", "TAG", "TGA"}
        for frame in (0, 1, 2):
            i = frame
            while i <= len(self.sequence) - 3:
                codon = self.sequence[i : i + 3]
                if codon == "ATG":
                    j = i + 3
                    while j <= len(self.sequence) - 3:
                        stop = self.sequence[j : j + 3]
                        if stop in stops:
                            nt_len = (j + 3) - i
                            aa_len = nt_len // 3 - 1
                            if aa_len >= min_aa_len:
                                start = i + 1
                                end = j + 3
                                protein = self.sequence[i : j + 3]
                                results.append((start, end, frame + 1, translate_nt(protein, to_stop=True)))
                            i = j + 3
                            break
                        j += 3
                    else:
                        i += 3
                else:
                    i += 3
        return results


def sanitize_sequence(seq: str) -> str:
    seq = re.sub(r"\s+", "", seq).upper()
    if not seq:
        return ""
    if any(ch not in DNA_ALPHABET for ch in seq):
        bad = sorted({ch for ch in seq if ch not in DNA_ALPHABET})
        raise ValueError(f"Unsupported nucleotide symbols: {''.join(bad)}")
    return seq


def iupac_symbol_matches(symbol_a: str, symbol_b: str) -> bool:
    bases_a = IUPAC_BASE_SETS.get(symbol_a.upper())
    bases_b = IUPAC_BASE_SETS.get(symbol_b.upper())
    return bool(bases_a and bases_b and bases_a & bases_b)


def iupac_sequence_matches(seq_a: str, seq_b: str) -> bool:
    if len(seq_a) != len(seq_b):
        return False
    return all(iupac_symbol_matches(a, b) for a, b in zip(seq_a, seq_b))


def iupac_hamming_distance(seq_a: str, seq_b: str) -> int:
    if len(seq_a) != len(seq_b):
        raise ValueError("Hamming distance requires equal length strings")
    return sum(1 for a, b in zip(seq_a, seq_b) if not iupac_symbol_matches(a, b))


def translate_nt(seq: str, to_stop: bool = False) -> str:
    aa: List[str] = []
    for i in range(0, len(seq) - 2, 3):
        codon = seq[i : i + 3]
        residue = CODON_TABLE.get(codon, "X")
        if residue == "*" and to_stop:
            break
        aa.append(residue)
    return "".join(aa)


def parse_feature_interval(location: str) -> Optional[Tuple[int, int]]:
    nums = re.findall(r"\d+", location)
    if len(nums) < 2:
        return None
    start = int(nums[0])
    end = int(nums[-1])
    if start <= 0 or end <= 0:
        return None
    if start > end:
        start, end = end, start
    return start, end


def seq_tm_wallace(seq: str) -> float:
    seq = sanitize_sequence(seq)
    at = seq.count("A") + seq.count("T")
    gc = seq.count("G") + seq.count("C")
    return 2.0 * at + 4.0 * gc


def seq_tm_nn(seq: str, na_mM: float = 50.0, primer_nM: float = 250.0) -> float:
    """
    Approximate nearest-neighbor melting temperature (degC).
    Uses non-self-complementary concentration correction.
    """
    s = sanitize_sequence(seq)
    if len(s) < 2:
        return 0.0

    dh = 0.2  # initiation correction
    ds = -5.7
    for i in range(len(s) - 1):
        pair = s[i : i + 2]
        if pair not in NN_PARAMS:
            return seq_tm_wallace(s)
        p_dh, p_ds = NN_PARAMS[pair]
        dh += p_dh
        ds += p_ds

    r = 1.987  # cal/mol*K
    ct = max(primer_nM * 1e-9, 1e-12)
    na = max(na_mM * 1e-3, 1e-6)
    tm_k = (1000.0 * dh) / (ds + r * math.log(ct / 4.0))
    tm_c = tm_k - 273.15 + 16.6 * math.log10(na)
    return tm_c


def primer_gc_clamp(seq: str) -> bool:
    end = seq[-2:] if len(seq) >= 2 else seq
    gc = sum(1 for b in end if b in "GC")
    return gc >= 1


def max_complement_run(seq_a: str, seq_b: str, min_run: int = 3) -> int:
    """Longest contiguous complementarity between seq_a and reverse-complement(seq_b)."""
    a = sanitize_sequence(seq_a)
    b_rc = sanitize_sequence(seq_b).translate(RC_TABLE)[::-1]
    best = 0
    for offset in range(-len(b_rc) + 1, len(a)):
        run = 0
        for i in range(len(a)):
            j = i - offset
            if 0 <= j < len(b_rc) and iupac_symbol_matches(a[i], b_rc[j]):
                run += 1
                if run > best:
                    best = run
            else:
                run = 0
    return best if best >= min_run else 0


def end_complement_run(seq_a: str, seq_b: str, end_bases: int = 8) -> int:
    """Complementarity between 3' ends of two primers."""
    a_end = sanitize_sequence(seq_a)[-end_bases:]
    b_end = sanitize_sequence(seq_b)[-end_bases:]
    return max_complement_run(a_end, b_end, min_run=2)


def hairpin_risk(seq: str, stem_min: int = 4, loop_min: int = 3) -> int:
    """Simple heuristic hairpin score: max stem length involving 3' region."""
    s = sanitize_sequence(seq)
    if len(s) < stem_min * 2 + loop_min:
        return 0
    tail = s[-10:]
    best = 0
    for stem in range(stem_min, min(8, len(tail)) + 1):
        kmer = tail[-stem:]
        target = kmer.translate(RC_TABLE)[::-1]
        for i in range(0, len(s) - stem - loop_min):
            if iupac_sequence_matches(s[i : i + stem], target):
                best = max(best, stem)
    return best


def primer_quality(seq: str) -> Dict[str, object]:
    p = sanitize_sequence(seq)
    return {
        "length": len(p),
        "gc": gc_percent(p),
        "tm_wallace": seq_tm_wallace(p),
        "tm_nn": seq_tm_nn(p),
        "gc_clamp": primer_gc_clamp(p),
        "self_dimer_max_run": max_complement_run(p, p),
        "self_end_dimer_run": end_complement_run(p, p),
        "hairpin_stem": hairpin_risk(p),
    }


def candidate_primers(
    seq: str,
    around_pos: int,
    direction: str,
    min_len: int,
    max_len: int,
    search_window: int,
    tm_min: float,
    tm_max: float,
    na_mM: float = 50.0,
    primer_nM: float = 250.0,
) -> List[Dict[str, object]]:
    candidates: List[Dict[str, object]] = []
    n = len(seq)

    if direction == "forward":
        left = max(0, around_pos - search_window)
        right = min(n, around_pos + search_window)
        for start in range(left, right):
            for ln in range(min_len, max_len + 1):
                end = start + ln
                if end > n:
                    continue
                p = seq[start:end]
                tm = seq_tm_nn(p, na_mM=na_mM, primer_nM=primer_nM)
                gc = gc_percent(p)
                hairpin = hairpin_risk(p)
                self_end = end_complement_run(p, p)
                if tm_min <= tm <= tm_max and 30 <= gc <= 70 and primer_gc_clamp(p) and hairpin <= 5 and self_end <= 4:
                    candidates.append({
                        "sequence": p,
                        "start_1based": start + 1,
                        "end_1based": end,
                        "tm": tm,
                        "tm_wallace": seq_tm_wallace(p),
                        "gc": gc,
                        "hairpin_stem": hairpin,
                        "self_end_dimer_run": self_end,
                        "direction": "forward",
                    })
    else:
        left = max(0, around_pos - search_window)
        right = min(n, around_pos + search_window)
        for end in range(left + 1, right + 1):
            for ln in range(min_len, max_len + 1):
                start = end - ln
                if start < 0:
                    continue
                template = seq[start:end]
                primer = template.translate(RC_TABLE)[::-1]
                tm = seq_tm_nn(primer, na_mM=na_mM, primer_nM=primer_nM)
                gc = gc_percent(primer)
                hairpin = hairpin_risk(primer)
                self_end = end_complement_run(primer, primer)
                if tm_min <= tm <= tm_max and 30 <= gc <= 70 and primer_gc_clamp(primer) and hairpin <= 5 and self_end <= 4:
                    candidates.append({
                        "sequence": primer,
                        "start_1based": start + 1,
                        "end_1based": end,
                        "tm": tm,
                        "tm_wallace": seq_tm_wallace(primer),
                        "gc": gc,
                        "hairpin_stem": hairpin,
                        "self_end_dimer_run": self_end,
                        "direction": "reverse",
                    })

    # Prefer candidates close to around_pos and with Tm near middle of interval.
    tm_target = (tm_min + tm_max) / 2.0
    candidates.sort(key=lambda c: (abs(c["tm"] - tm_target), abs(c["start_1based"] - (around_pos + 1))))
    return candidates


def design_primer_pair(
    record: SequenceRecord,
    target_start_1based: int,
    target_end_1based: int,
    min_len: int,
    max_len: int,
    window: int,
    tm_min: float,
    tm_max: float,
    na_mM: float = 50.0,
    primer_nM: float = 250.0,
) -> Dict[str, object]:
    if target_start_1based < 1 or target_end_1based > record.length or target_start_1based >= target_end_1based:
        raise ValueError("Invalid target coordinates")

    seq = record.sequence
    fwd_candidates = candidate_primers(
        seq,
        around_pos=target_start_1based - 1,
        direction="forward",
        min_len=min_len,
        max_len=max_len,
        search_window=window,
        tm_min=tm_min,
        tm_max=tm_max,
        na_mM=na_mM,
        primer_nM=primer_nM,
    )
    rev_candidates = candidate_primers(
        seq,
        around_pos=target_end_1based - 1,
        direction="reverse",
        min_len=min_len,
        max_len=max_len,
        search_window=window,
        tm_min=tm_min,
        tm_max=tm_max,
        na_mM=na_mM,
        primer_nM=primer_nM,
    )
    if not fwd_candidates or not rev_candidates:
        raise ValueError("Could not find primers that satisfy constraints")

    best_pair = None
    best_score = float("inf")
    for f in fwd_candidates[:60]:
        for r in rev_candidates[:60]:
            amplicon = r["end_1based"] - f["start_1based"] + 1
            if amplicon <= 0:
                continue
            tm_delta = abs(f["tm"] - r["tm"])
            center_penalty = abs((f["start_1based"] - target_start_1based)) + abs((r["end_1based"] - target_end_1based))
            hetero_end = end_complement_run(f["sequence"], r["sequence"])
            score = tm_delta * 2.0 + center_penalty / 10.0 + hetero_end * 1.8 + f["hairpin_stem"] + r["hairpin_stem"]
            if score < best_score:
                best_score = score
                best_pair = (f, r, amplicon, hetero_end)

    if not best_pair:
        raise ValueError("No compatible primer pair found")

    f, r, amplicon, hetero_end = best_pair
    return {
        "forward": f,
        "reverse": r,
        "hetero_end_dimer_run": hetero_end,
        "amplicon_bp": amplicon,
        "target_start_1based": target_start_1based,
        "target_end_1based": target_end_1based,
    }


def find_all_occurrences(seq: str, motif: str, circular: bool = False) -> List[int]:
    seq = sanitize_sequence(seq)
    motif = sanitize_sequence(motif)
    if not motif:
        return []
    positions: List[int] = []
    m = len(motif)
    n = len(seq)
    if n == 0 or m > (n + m - 1 if circular else n):
        return positions
    search = seq + (seq[: m - 1] if circular else "")
    limit = n if circular else n - m + 1
    for i in range(limit):
        if iupac_sequence_matches(search[i : i + m], motif):
            positions.append(i)
    return positions


def simulate_pcr(record: SequenceRecord, forward_primer: str, reverse_primer: str) -> Dict[str, object]:
    forward_primer = sanitize_sequence(forward_primer)
    reverse_primer = sanitize_sequence(reverse_primer)

    f_sites = find_all_occurrences(record.sequence, forward_primer, circular=record.topology == "circular")
    rev_binding = reverse_primer.translate(RC_TABLE)[::-1]
    r_sites = find_all_occurrences(record.sequence, rev_binding, circular=record.topology == "circular")

    products: List[Dict[str, object]] = []
    n = record.length

    for fs in f_sites:
        for rs in r_sites:
            if record.topology == "linear":
                if rs < fs:
                    continue
                product_start = fs
                product_end_excl = rs + len(rev_binding)
                if product_end_excl > n:
                    continue
                product_seq = record.sequence[product_start:product_end_excl]
            else:
                product_start = fs
                product_end_excl = (rs + len(rev_binding)) % n
                if product_start < product_end_excl:
                    product_seq = record.sequence[product_start:product_end_excl]
                else:
                    product_seq = record.sequence[product_start:] + record.sequence[:product_end_excl]

            if not product_seq:
                continue
            products.append({
                "forward_site_1based": fs + 1,
                "reverse_site_1based": rs + 1,
                "size_bp": len(product_seq),
                "sequence": product_seq,
            })

    products.sort(key=lambda p: p["size_bp"])
    return {
        "forward_hits": [x + 1 for x in f_sites],
        "reverse_hits": [x + 1 for x in r_sites],
        "products": products,
    }


def optimize_coding_sequence(seq: str, host: str, frame: int = 1, keep_stop: bool = True) -> Dict[str, str]:
    if host not in HOST_PREFERRED_CODONS:
        raise ValueError(f"Unsupported host '{host}'. Supported: {', '.join(sorted(HOST_PREFERRED_CODONS))}")
    if frame not in (1, 2, 3):
        raise ValueError("Frame must be 1, 2, or 3")

    prefs = HOST_PREFERRED_CODONS[host]
    coding = seq[frame - 1 :]
    trim = len(coding) - (len(coding) // 3) * 3
    coding = coding[: len(coding) - trim]

    aa = translate_nt(coding, to_stop=False)
    out_codons: List[str] = []
    for residue in aa:
        if residue == "*" and not keep_stop:
            break
        out_codons.append(prefs.get(residue, AA_TO_CODONS.get(residue, ["NNN"])[0]))

    optimized = "".join(out_codons)
    return {
        "protein": aa,
        "optimized_nt": optimized,
        "gc_original": f"{gc_percent(coding):.2f}",
        "gc_optimized": f"{gc_percent(optimized):.2f}",
    }


def gc_percent(seq: str) -> float:
    if not seq:
        return 0.0
    return (seq.count("G") + seq.count("C")) / len(seq) * 100.0


def parse_fasta(text: str) -> SequenceRecord:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines or not lines[0].startswith(">"):
        raise ValueError("Invalid FASTA: missing header")
    name = lines[0][1:].strip() or "unnamed"
    seq = "".join(lines[1:])
    return SequenceRecord(name=name, sequence=seq)


def parse_genbank(text: str) -> SequenceRecord:
    name = "unnamed"
    topology = "linear"
    features: List[Feature] = []
    seq_lines: List[str] = []

    in_features = False
    in_origin = False
    current_feature: Optional[Feature] = None

    for raw in text.splitlines():
        line = raw.rstrip("\n")
        if line.startswith("LOCUS"):
            parts = line.split()
            if len(parts) > 1:
                name = parts[1]
            if "circular" in line.lower():
                topology = "circular"
        elif line.startswith("FEATURES"):
            in_features = True
            in_origin = False
        elif line.startswith("ORIGIN"):
            in_origin = True
            in_features = False
            if current_feature:
                features.append(current_feature)
                current_feature = None
        elif line.startswith("//"):
            break
        elif in_origin:
            chunk = re.sub(r"[^acgtryswkmbdhvnACGTRYSWKMBDHVN]", "", line)
            if chunk:
                seq_lines.append(chunk)
        elif in_features:
            if re.match(r"^\s{5}\S", line):
                if current_feature:
                    features.append(current_feature)
                key = line[5:21].strip()
                location = line[21:].strip()
                current_feature = Feature(key=key, location=location, qualifiers={})
            elif re.match(r"^\s{21}/", line) and current_feature:
                q = line.strip()[1:]
                if "=" in q:
                    k, v = q.split("=", 1)
                    current_feature.qualifiers[k] = v.strip('"')
                else:
                    current_feature.qualifiers[q] = ""

    if current_feature:
        features.append(current_feature)

    sequence = "".join(seq_lines)
    if not sequence:
        raise ValueError("Invalid GenBank: ORIGIN sequence not found")

    return SequenceRecord(name=name, sequence=sequence, topology=topology, features=features)


def load_record(path: Path) -> SequenceRecord:
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix in {".fa", ".fasta", ".fna"}:
        return parse_fasta(text)
    if suffix in {".gb", ".gbk", ".genbank"}:
        return parse_genbank(text)

    stripped = text.lstrip()
    if stripped.startswith(">"):
        return parse_fasta(text)
    if stripped.startswith("LOCUS"):
        return parse_genbank(text)
    raise ValueError(f"Unsupported file format: {path}")


def to_fasta(record: SequenceRecord, width: int = 70) -> str:
    chunks = [record.sequence[i : i + width] for i in range(0, record.length, width)]
    return f">{record.name}\n" + "\n".join(chunks) + "\n"


def to_genbank(record: SequenceRecord) -> str:
    lines: List[str] = []
    topology = "circular" if record.topology == "circular" else "linear"
    lines.append(f"LOCUS       {record.name:<16}{record.length:>11} bp    DNA     {topology}")
    lines.append("FEATURES             Location/Qualifiers")
    for feat in record.features:
        lines.append(f"     {feat.key:<15}{feat.location}")
        for k, v in feat.qualifiers.items():
            if v:
                lines.append(f"                     /{k}=\"{v}\"")
            else:
                lines.append(f"                     /{k}")
    lines.append("ORIGIN")

    idx = 1
    for i in range(0, record.length, 60):
        block = record.sequence[i : i + 60].lower()
        grouped = " ".join(block[j : j + 10] for j in range(0, len(block), 10))
        lines.append(f"{idx:>9} {grouped}")
        idx += 60
    lines.append("//")
    return "\n".join(lines) + "\n"


def to_embl(record: SequenceRecord) -> str:
    lines: List[str] = []
    topo = "circular" if record.topology == "circular" else "linear"
    lines.append(f"ID   {record.name}; SV 1; {topo}; DNA; UNC; {record.length} BP.")
    lines.append("XX")
    lines.append("FH   Key             Location/Qualifiers")
    lines.append("FH")
    for feat in record.features:
        lines.append(f"FT   {feat.key:<15}{feat.location}")
        for k, v in feat.qualifiers.items():
            if v:
                lines.append(f'FT                   /{k}=\"{v}\"')
            else:
                lines.append(f"FT                   /{k}")
    lines.append("XX")
    lines.append("SQ   Sequence")
    for i in range(0, record.length, 60):
        block = record.sequence[i : i + 60].lower()
        grouped = " ".join(block[j : j + 10] for j in range(0, len(block), 10))
        lines.append(f"     {grouped}")
    lines.append("//")
    return "\n".join(lines) + "\n"


def find_cut_sites(seq: str, site: str, circular: bool = False) -> List[int]:
    positions: List[int] = []
    n = len(seq)
    m = len(site)
    if m == 0 or n == 0 or m > n + (m - 1 if circular else 0):
        return positions

    search_seq = seq + (seq[: m - 1] if circular else "")
    limit = n if circular else n - m + 1
    for i in range(limit):
        if search_seq[i : i + m] == site:
            positions.append(i)
    return positions


def simulate_digest(record: SequenceRecord, enzyme_names: Sequence[str]) -> Dict[str, object]:
    missing = [e for e in enzyme_names if e not in ENZYMES]
    if missing:
        raise ValueError(f"Unknown enzymes: {', '.join(missing)}")

    circular = record.topology == "circular"
    cut_points: List[Tuple[str, int]] = []

    for enzyme in enzyme_names:
        site, offset = ENZYMES[enzyme]
        starts = find_cut_sites(record.sequence, site, circular=circular)
        for s in starts:
            cut = (s + offset) % record.length if circular else s + offset
            if 0 <= cut <= record.length:
                cut_points.append((enzyme, cut))

    unique_cuts = sorted({cp for _, cp in cut_points})

    fragments: List[int] = []
    if not unique_cuts:
        fragments = [record.length]
    elif circular:
        for i in range(len(unique_cuts)):
            a = unique_cuts[i]
            b = unique_cuts[(i + 1) % len(unique_cuts)]
            size = (b - a) % record.length
            fragments.append(size)
    else:
        bounds = [0] + unique_cuts + [record.length]
        for i in range(len(bounds) - 1):
            fragments.append(bounds[i + 1] - bounds[i])

    return {
        "topology": record.topology,
        "cuts": [{"enzyme": e, "position_1based": p + 1} for e, p in sorted(cut_points, key=lambda x: x[1])],
        "unique_cut_positions_1based": [p + 1 for p in unique_cuts],
        "fragments_bp": sorted([f for f in fragments if f > 0], reverse=True),
    }


def angle_for_pos(pos_1based: int, length: int) -> float:
    frac = (pos_1based - 1) / max(length, 1)
    return 2.0 * math.pi * frac - math.pi / 2.0


def polar(cx: float, cy: float, r: float, angle: float) -> Tuple[float, float]:
    return cx + r * math.cos(angle), cy + r * math.sin(angle)


def arc_path(cx: float, cy: float, r: float, start_angle: float, end_angle: float) -> str:
    sx, sy = polar(cx, cy, r, start_angle)
    ex, ey = polar(cx, cy, r, end_angle)
    delta = (end_angle - start_angle) % (2 * math.pi)
    large = 1 if delta > math.pi else 0
    return f"M {sx:.2f} {sy:.2f} A {r:.2f} {r:.2f} 0 {large} 1 {ex:.2f} {ey:.2f}"


def build_svg_map(record: SequenceRecord, enzyme_names: Optional[Sequence[str]] = None) -> str:
    w = h = 900
    cx = cy = 450
    radius = 300
    ring_stroke = 30

    lines: List[str] = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">')
    lines.append('<rect width="100%" height="100%" fill="#f8fafc"/>')
    lines.append(f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="#1f2937" stroke-width="{ring_stroke}"/>')

    if record.topology == "linear":
        x1, x2, y = 100, 800, 450
        lines.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="#1f2937" stroke-width="16"/>')
        for i, feat in enumerate(record.features):
            interval = parse_feature_interval(feat.location)
            if not interval:
                continue
            start, end = interval
            color = FEATURE_COLORS.get(feat.key.lower(), FEATURE_COLORS["default"])
            fx1 = x1 + (start - 1) / record.length * (x2 - x1)
            fx2 = x1 + (end - 1) / record.length * (x2 - x1)
            lines.append(
                f'<line x1="{fx1:.2f}" y1="{y}" x2="{fx2:.2f}" y2="{y}" stroke="{color}" '
                f'stroke-width="10" data-feature-index="{i}" class="feature-segment"/>'
            )
        lines.append(f'<text x="{cx}" y="{cy - 50}" text-anchor="middle" font-family="Menlo, monospace" font-size="26" fill="#111827">{record.name} ({record.length} bp, linear)</text>')
    else:
        for i, feat in enumerate(record.features):
            interval = parse_feature_interval(feat.location)
            if not interval:
                continue
            start, end = interval
            color = FEATURE_COLORS.get(feat.key.lower(), FEATURE_COLORS["default"])
            a1 = angle_for_pos(start, record.length)
            a2 = angle_for_pos(end, record.length)
            if end < start:
                a2 += 2 * math.pi
            path = arc_path(cx, cy, radius, a1, a2)
            lines.append(
                f'<path d="{path}" stroke="{color}" stroke-width="22" fill="none" stroke-linecap="round" '
                f'data-feature-index="{i}" class="feature-segment"/>'
            )
            label = feat.qualifiers.get("label") or feat.qualifiers.get("gene") or feat.key
            lx, ly = polar(cx, cy, radius + 50, (a1 + a2) / 2)
            lines.append(
                f'<text x="{lx:.2f}" y="{ly:.2f}" text-anchor="middle" font-family="Menlo, monospace" '
                f'font-size="16" fill="#111827" data-feature-index="{i}" class="feature-label">{label}</text>'
            )

        if enzyme_names:
            digest = simulate_digest(record, enzyme_names)
            for cut in digest["cuts"]:
                pos = int(cut["position_1based"])
                ang = angle_for_pos(pos, record.length)
                x1, y1 = polar(cx, cy, radius - 20, ang)
                x2, y2 = polar(cx, cy, radius + 30, ang)
                tx, ty = polar(cx, cy, radius + 52, ang)
                lines.append(
                    f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="#0f172a" stroke-width="3" '
                    f'data-cut-enzyme="{cut["enzyme"]}" data-cut-position="{pos}" class="cut-marker"/>'
                )
                lines.append(
                    f'<text x="{tx:.2f}" y="{ty:.2f}" text-anchor="middle" font-family="Menlo, monospace" font-size="12" '
                    f'fill="#0f172a" data-cut-enzyme="{cut["enzyme"]}" data-cut-position="{pos}" class="cut-label">{cut["enzyme"]}</text>'
                )

        lines.append(f'<text x="{cx}" y="{cy - 10}" text-anchor="middle" font-family="Menlo, monospace" font-size="30" fill="#111827">{record.name}</text>')
        lines.append(f'<text x="{cx}" y="{cy + 24}" text-anchor="middle" font-family="Menlo, monospace" font-size="22" fill="#334155">{record.length} bp</text>')
        lines.append(f'<text x="{cx}" y="{cy + 54}" text-anchor="middle" font-family="Menlo, monospace" font-size="18" fill="#475569">circular</text>')

    lines.append('</svg>')
    return "\n".join(lines) + "\n"


def cmd_info(record: SequenceRecord) -> None:
    print(f"Name: {record.name}")
    print(f"Length: {record.length} bp")
    print(f"Molecule: {record.molecule}")
    print(f"Topology: {record.topology}")
    print(f"GC%: {record.gc_content():.2f}")
    print(f"Feature count: {len(record.features)}")


def cmd_features(record: SequenceRecord) -> None:
    if not record.features:
        print("No features found.")
        return
    for i, feat in enumerate(record.features, start=1):
        label = feat.qualifiers.get("label") or feat.qualifiers.get("gene") or feat.qualifiers.get("product") or ""
        if label:
            print(f"{i}. {feat.key} {feat.location} [{label}]")
        else:
            print(f"{i}. {feat.key} {feat.location}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Genome Forge DNA sequence toolkit")
    p.add_argument("input", help="Input sequence file (.fasta/.fa/.gb/.gbk)")

    sp = p.add_subparsers(dest="command", required=True)

    sp.add_parser("info", help="Show sequence summary")

    rev = sp.add_parser("revcomp", help="Print reverse-complement sequence")
    rev.add_argument("--format", choices=["fasta", "raw"], default="fasta")

    tr = sp.add_parser("translate", help="Translate sequence")
    tr.add_argument("--frame", type=int, choices=[1, 2, 3], default=1)
    tr.add_argument("--to-stop", action="store_true", help="Stop at first stop codon")

    orf = sp.add_parser("orfs", help="Find ORFs on forward strand")
    orf.add_argument("--min-aa", type=int, default=50)

    dg = sp.add_parser("digest", help="Simulate restriction digest")
    dg.add_argument("enzymes", nargs="+", help="Enzyme names (e.g., EcoRI BamHI)")

    pcr = sp.add_parser("pcr", help="Simulate virtual PCR with explicit primers")
    pcr.add_argument("--forward", required=True, help="Forward primer 5'->3'")
    pcr.add_argument("--reverse", required=True, help="Reverse primer 5'->3'")
    pcr.add_argument("--max-products", type=int, default=5)

    pd = sp.add_parser("primers", help="Design a primer pair around a target region")
    pd.add_argument("--target-start", type=int, required=True)
    pd.add_argument("--target-end", type=int, required=True)
    pd.add_argument("--min-len", type=int, default=18)
    pd.add_argument("--max-len", type=int, default=25)
    pd.add_argument("--window", type=int, default=80)
    pd.add_argument("--tm-min", type=float, default=55.0)
    pd.add_argument("--tm-max", type=float, default=68.0)
    pd.add_argument("--na-mM", type=float, default=50.0, help="Monovalent salt concentration for NN Tm")
    pd.add_argument("--primer-nM", type=float, default=250.0, help="Primer concentration for NN Tm")

    pc = sp.add_parser("primer-check", help="QC one or two primer sequences")
    pc.add_argument("--primer", required=True, help="Primer sequence 5'->3'")
    pc.add_argument("--with-primer", help="Optional second primer for heterodimer checks")

    co = sp.add_parser("codon-optimize", help="Codon optimize coding sequence")
    co.add_argument("--host", choices=sorted(HOST_PREFERRED_CODONS), default="ecoli")
    co.add_argument("--frame", type=int, choices=[1, 2, 3], default=1)
    co.add_argument("--drop-stop", action="store_true", help="Stop optimization at first stop codon")
    co.add_argument("--output", help="Write optimized sequence to FASTA")

    mp = sp.add_parser("map", help="Render sequence map as SVG")
    mp.add_argument("--output", required=True, help="Output SVG file")
    mp.add_argument("--enzymes", nargs="*", default=[], help="Optional enzyme names to plot cut marks")

    exp = sp.add_parser("export", help="Export sequence")
    exp.add_argument("--format", choices=["fasta", "genbank", "embl", "json"], required=True)
    exp.add_argument("--output", required=True)

    sp.add_parser("features", help="List annotated features")

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    record = load_record(Path(args.input))

    if args.command == "info":
        cmd_info(record)
    elif args.command == "features":
        cmd_features(record)
    elif args.command == "revcomp":
        rc = record.reverse_complement()
        if args.format == "raw":
            print(rc.sequence)
        else:
            print(to_fasta(rc), end="")
    elif args.command == "translate":
        print(record.translate(frame=args.frame, to_stop=args.to_stop))
    elif args.command == "orfs":
        orfs = record.find_orfs(min_aa_len=args.min_aa)
        if not orfs:
            print("No ORFs found.")
        else:
            for idx, (start, end, frame, protein) in enumerate(orfs, start=1):
                print(f"{idx}. start={start} end={end} frame={frame} aa_len={len(protein)}")
    elif args.command == "digest":
        out = simulate_digest(record, args.enzymes)
        print(f"Topology: {out['topology']}")
        print("Cuts:")
        cuts = out["cuts"]
        if cuts:
            for c in cuts:
                print(f"  - {c['enzyme']}: {c['position_1based']}")
        else:
            print("  - none")
        print("Fragments (bp):")
        print("  " + ", ".join(str(x) for x in out["fragments_bp"]))
    elif args.command == "pcr":
        out = simulate_pcr(record, args.forward, args.reverse)
        print(f"Forward primer hits (1-based): {out['forward_hits']}")
        print(f"Reverse primer hits (1-based): {out['reverse_hits']}")
        products = out["products"]
        if not products:
            print("No products predicted.")
        else:
            print("Products:")
            for i, p in enumerate(products[: args.max_products], start=1):
                print(
                    f"  {i}. size={p['size_bp']} bp fwd={p['forward_site_1based']} rev={p['reverse_site_1based']}"
                )
    elif args.command == "primers":
        out = design_primer_pair(
            record,
            target_start_1based=args.target_start,
            target_end_1based=args.target_end,
            min_len=args.min_len,
            max_len=args.max_len,
            window=args.window,
            tm_min=args.tm_min,
            tm_max=args.tm_max,
            na_mM=args.na_mM,
            primer_nM=args.primer_nM,
        )
        f = out["forward"]
        r = out["reverse"]
        print("Primer pair:")
        print(
            f"  Forward: {f['sequence']}  pos={f['start_1based']}-{f['end_1based']}  "
            f"TmNN={f['tm']:.1f}C  TmWallace={f['tm_wallace']:.1f}C  GC={f['gc']:.1f}%"
        )
        print(
            f"  Reverse: {r['sequence']}  pos={r['start_1based']}-{r['end_1based']}  "
            f"TmNN={r['tm']:.1f}C  TmWallace={r['tm_wallace']:.1f}C  GC={r['gc']:.1f}%"
        )
        print(
            f"  Structure risk: fwd_hairpin={f['hairpin_stem']} rev_hairpin={r['hairpin_stem']} "
            f"hetero_end_dimer={out['hetero_end_dimer_run']}"
        )
        print(f"  Amplicon: {out['amplicon_bp']} bp")
    elif args.command == "primer-check":
        p1 = primer_quality(args.primer)
        print("Primer QC:")
        print(f"  Primer: {sanitize_sequence(args.primer)}")
        print(
            f"  len={p1['length']} GC={p1['gc']:.1f}% TmNN={p1['tm_nn']:.1f}C "
            f"TmWallace={p1['tm_wallace']:.1f}C gc_clamp={p1['gc_clamp']}"
        )
        print(
            f"  self_dimer_run={p1['self_dimer_max_run']} "
            f"self_end_dimer_run={p1['self_end_dimer_run']} hairpin_stem={p1['hairpin_stem']}"
        )
        if args.with_primer:
            p2 = sanitize_sequence(args.with_primer)
            hetero = max_complement_run(args.primer, p2)
            hetero_end = end_complement_run(args.primer, p2)
            print(f"  With primer: {p2}")
            print(f"  hetero_dimer_run={hetero} hetero_end_dimer_run={hetero_end}")
    elif args.command == "codon-optimize":
        out = optimize_coding_sequence(record.sequence, host=args.host, frame=args.frame, keep_stop=not args.drop_stop)
        print(f"Host: {args.host}")
        print(f"Optimized length: {len(out['optimized_nt'])} bp")
        print(f"GC original: {out['gc_original']}%")
        print(f"GC optimized: {out['gc_optimized']}%")
        print("Optimized sequence:")
        print(out["optimized_nt"])
        if args.output:
            out_record = SequenceRecord(name=f"{record.name}_{args.host}_optimized", sequence=out["optimized_nt"], topology=record.topology)
            Path(args.output).write_text(to_fasta(out_record), encoding="utf-8")
            print(f"Wrote {args.output}")
    elif args.command == "map":
        svg = build_svg_map(record, enzyme_names=args.enzymes)
        Path(args.output).write_text(svg, encoding="utf-8")
        print(f"Wrote {args.output}")
    elif args.command == "export":
        out_path = Path(args.output)
        if args.format == "fasta":
            out_path.write_text(to_fasta(record), encoding="utf-8")
        elif args.format == "genbank":
            out_path.write_text(to_genbank(record), encoding="utf-8")
        elif args.format == "embl":
            out_path.write_text(to_embl(record), encoding="utf-8")
        else:
            payload = {
                "name": record.name,
                "topology": record.topology,
                "content": record.sequence,
                "features": [{"key": f.key, "location": f.location, "qualifiers": dict(f.qualifiers)} for f in record.features],
            }
            out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
