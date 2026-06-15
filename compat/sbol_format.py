from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Dict, Iterable

from genomeforge_toolkit import Feature, RC_TABLE, SequenceRecord, parse_feature_interval, sanitize_sequence


RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
SBOL_NS = "http://sbols.org/v2#"
DCTERMS_NS = "http://purl.org/dc/terms/"
GF_NS = "https://genomeforge.local/ns#"

ET.register_namespace("rdf", RDF_NS)
ET.register_namespace("sbol", SBOL_NS)
ET.register_namespace("dcterms", DCTERMS_NS)
ET.register_namespace("gf", GF_NS)


def _q(ns: str, name: str) -> str:
    return f"{{{ns}}}{name}"


def _local(tag: str) -> str:
    return str(tag).rsplit("}", 1)[-1]


def _safe_id(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9_]+", "_", str(value or "record")).strip("_")
    if not clean:
        clean = "record"
    if clean[0].isdigit():
        clean = f"r_{clean}"
    return clean[:80]


def _direct_text(node: ET.Element, local_name: str) -> str:
    for child in list(node):
        if _local(child.tag).lower() == local_name.lower() and child.text:
            return child.text.strip()
    return ""


def _desc_text(node: ET.Element, local_name: str) -> str:
    for child in node.iter():
        if child is node:
            continue
        if _local(child.tag).lower() == local_name.lower() and child.text:
            return child.text.strip()
    return ""


def _children_local(node: ET.Element, local_name: str) -> Iterable[ET.Element]:
    for child in node.iter():
        if child is node:
            continue
        if _local(child.tag).lower() == local_name.lower():
            yield child


def looks_like_sbol(text: str) -> bool:
    clean = str(text or "").lstrip()
    return clean.startswith("<") and ("sbol" in clean[:1000].lower() or "componentdefinition" in clean[:2000].lower())


def to_sbol(record: SequenceRecord) -> str:
    """Export a compact SBOL v2-compatible RDF/XML subset.

    The subset is intentionally conservative: sequence, topology, feature key,
    feature location, and qualifiers are represented so Genome Forge can audit
    round-trip preservation without claiming full SBOL design semantics.
    """

    record_id = _safe_id(record.name)
    base_uri = f"urn:genomeforge:{record_id}"
    root = ET.Element(_q(RDF_NS, "RDF"))

    component = ET.SubElement(root, _q(SBOL_NS, "ComponentDefinition"), {_q(RDF_NS, "about"): base_uri})
    ET.SubElement(component, _q(SBOL_NS, "displayId")).text = record_id
    ET.SubElement(component, _q(DCTERMS_NS, "title")).text = record.name
    ET.SubElement(component, _q(GF_NS, "topology")).text = "circular" if record.topology == "circular" else "linear"
    ET.SubElement(component, _q(SBOL_NS, "sequence"), {_q(RDF_NS, "resource"): f"{base_uri}/sequence"})

    for idx, feature in enumerate(record.features, start=1):
        interval = parse_feature_interval(feature.location)
        start, end = interval if interval else (0, 0)
        strand = "reverseComplement" if "complement" in feature.location.lower() else "inline"
        label = (
            feature.qualifiers.get("label")
            or feature.qualifiers.get("gene")
            or feature.qualifiers.get("product")
            or f"{feature.key}_{idx}"
        )

        wrapper = ET.SubElement(component, _q(SBOL_NS, "sequenceAnnotation"))
        ann = ET.SubElement(wrapper, _q(SBOL_NS, "SequenceAnnotation"), {_q(RDF_NS, "about"): f"{base_uri}/annotation/{idx}"})
        ET.SubElement(ann, _q(SBOL_NS, "displayId")).text = _safe_id(label)
        ET.SubElement(ann, _q(GF_NS, "featureKey")).text = feature.key
        ET.SubElement(ann, _q(GF_NS, "locationString")).text = feature.location
        loc_wrap = ET.SubElement(ann, _q(SBOL_NS, "location"))
        rng = ET.SubElement(loc_wrap, _q(SBOL_NS, "Range"), {_q(RDF_NS, "about"): f"{base_uri}/annotation/{idx}/range"})
        ET.SubElement(rng, _q(SBOL_NS, "start")).text = str(start)
        ET.SubElement(rng, _q(SBOL_NS, "end")).text = str(end)
        ET.SubElement(rng, _q(SBOL_NS, "orientation")).text = strand
        for key, value in sorted(feature.qualifiers.items()):
            q = ET.SubElement(ann, _q(GF_NS, "qualifier"), {"key": str(key)})
            q.text = str(value)

    seq = ET.SubElement(root, _q(SBOL_NS, "Sequence"), {_q(RDF_NS, "about"): f"{base_uri}/sequence"})
    ET.SubElement(seq, _q(SBOL_NS, "displayId")).text = f"{record_id}_sequence"
    ET.SubElement(seq, _q(SBOL_NS, "elements")).text = record.sequence
    ET.SubElement(seq, _q(SBOL_NS, "encoding")).text = "IUPAC DNA"

    return ET.tostring(root, encoding="unicode", xml_declaration=True) + "\n"


def parse_sbol(text: str) -> SequenceRecord:
    try:
        root = ET.fromstring(str(text or "").strip())
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Invalid SBOL/XML payload: {exc}") from exc

    sequence = sanitize_sequence(_desc_text(root, "elements"))
    if not sequence:
        raise ValueError("SBOL payload does not contain a sequence elements field")

    component = None
    for node in root.iter():
        if _local(node.tag) == "ComponentDefinition":
            component = node
            break

    if component is None:
        name = "SBOL_record"
        topology = "linear"
    else:
        name = _direct_text(component, "title") or _direct_text(component, "displayId") or "SBOL_record"
        topology = (_direct_text(component, "topology") or "linear").strip().lower()
        if topology not in {"linear", "circular"}:
            topology = "linear"

    features = []
    for ann in [node for node in root.iter() if _local(node.tag) == "SequenceAnnotation"]:
        key = _desc_text(ann, "featureKey") or "misc_feature"
        location = _desc_text(ann, "locationString")
        if not location:
            start = _desc_text(ann, "start")
            end = _desc_text(ann, "end")
            orientation = _desc_text(ann, "orientation")
            if start and end:
                location = f"{start}..{end}"
                if orientation.lower() == "reversecomplement":
                    location = f"complement({location})"
        qualifiers: Dict[str, str] = {}
        for q in _children_local(ann, "qualifier"):
            qkey = q.attrib.get("key") or q.attrib.get(f"{{{GF_NS}}}key")
            if qkey:
                qualifiers[str(qkey)] = str(q.text or "")
        label = _direct_text(ann, "displayId")
        if label and "label" not in qualifiers:
            qualifiers["label"] = label
        if location:
            features.append(Feature(key=key, location=location, qualifiers=qualifiers))

    return SequenceRecord(name=name, sequence=sequence, topology=topology, features=features)


def feature_translation(record: SequenceRecord, feature: Feature) -> str:
    interval = parse_feature_interval(feature.location)
    if not interval:
        return ""
    start, end = interval
    if start < 1 or end > record.length or start > end:
        return ""
    seq = record.sequence[start - 1 : end]
    if "complement" in feature.location.lower():
        seq = seq.translate(RC_TABLE)[::-1]
    try:
        codon_start = max(1, min(3, int(str(feature.qualifiers.get("codon_start", "1")) or "1")))
    except ValueError:
        codon_start = 1
    seq = seq[codon_start - 1 :]
    seq = seq[: len(seq) - (len(seq) % 3)]
    if not seq:
        return ""
    from genomeforge_toolkit import translate_nt

    return translate_nt(seq, to_stop=False)
