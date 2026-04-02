from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List

from bio.project_diff import diff_projects
from canonical_schema import infer_source_format, record_to_canonical
from collab.review import approve_review, load_review, submit_review
from collab.store import (
    append_audit_event,
    get_audit_log,
    get_project_permissions,
    role_for_user,
    set_project_permissions,
)
from genomeforge_toolkit import Feature, SequenceRecord, parse_fasta, parse_genbank, sanitize_sequence


ROOT = Path(__file__).resolve().parents[1]
PROJECTS_DIR = ROOT / "projects"
COLLECTIONS_DIR = ROOT / "collections"
SHARES_DIR = ROOT / "shares"
COLLAB_ROOT = ROOT / "collab_data"
RecordGetter = Callable[[], SequenceRecord]


def _parse_embl(text: str) -> SequenceRecord:
    name = "Untitled"
    topology = "linear"
    in_features = False
    in_seq = False
    seq_chunks: List[str] = []
    feats: List[Feature] = []
    cur_feat: Feature | None = None
    for raw in text.splitlines():
        line = raw.rstrip("\n")
        if line.startswith("ID"):
            parts = line.split()
            if len(parts) >= 2:
                name = parts[1].strip(";")
            low = line.lower()
            if "circular" in low:
                topology = "circular"
            elif "linear" in low:
                topology = "linear"
        if line.startswith("FH"):
            in_features = True
            continue
        if line.startswith("SQ"):
            in_seq = True
            in_features = False
            continue
        if line.startswith("//"):
            break
        if in_features and line.startswith("FT"):
            body = line[2:].rstrip()
            if not body.strip():
                continue
            if body[:6].strip():
                key = body[:15].strip() or "misc_feature"
                loc = body[15:].strip()
                cur_feat = Feature(key=key, location=loc, qualifiers={})
                feats.append(cur_feat)
            else:
                q = body[15:].strip()
                if cur_feat and q.startswith("/") and "=" in q:
                    k, v = q[1:].split("=", 1)
                    cur_feat.qualifiers[k.strip()] = v.strip().strip('"')
            continue
        if in_seq:
            seq_chunks.append("".join(ch for ch in line if ch.isalpha()))
    seq = sanitize_sequence("".join(seq_chunks))
    rec = SequenceRecord(name=name, sequence=seq, topology=topology)
    rec.features = feats
    return rec


def _features_to_dict(features: List[Feature]) -> List[Dict[str, Any]]:
    return [{"key": f.key, "location": f.location, "qualifiers": dict(f.qualifiers)} for f in features]


def _record_from_document(doc: Dict[str, Any]) -> SequenceRecord:
    content = str(doc.get("content", "")).strip()
    name = str(doc.get("name", doc.get("project_name", "Untitled"))).strip() or "Untitled"
    topology = str(doc.get("topology", "linear")).strip().lower()
    if topology not in {"linear", "circular"}:
        topology = "linear"
    if not content:
        raise ValueError("Project content is empty")
    if content.startswith(">"):
        record = parse_fasta(content)
    elif content.lstrip().startswith("LOCUS"):
        record = parse_genbank(content)
    elif content.lstrip().startswith("ID"):
        record = _parse_embl(content)
    else:
        record = SequenceRecord(name=name, sequence=sanitize_sequence(content), topology=topology)
    record.name = name
    record.topology = topology
    if isinstance(doc.get("features"), list):
        feats: List[Feature] = []
        for feature in doc["features"]:
            if not isinstance(feature, dict):
                continue
            feats.append(
                Feature(
                    key=str(feature.get("key", "misc_feature")),
                    location=str(feature.get("location", "")),
                    qualifiers={k: str(v) for k, v in dict(feature.get("qualifiers", {})).items()},
                )
            )
        record.features = feats
    return record


def project_path(name: str) -> Path:
    safe = "".join(ch for ch in name if ch.isalnum() or ch in ("-", "_")).strip("_-")
    if not safe:
        raise ValueError("Invalid project name")
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    return PROJECTS_DIR / f"{safe}.json"


def save_project(payload: Dict[str, Any], get_record: RecordGetter) -> Dict[str, Any]:
    rec = get_record()
    name = str(payload.get("project_name") or rec.name).strip()
    path = project_path(name)
    src_format = infer_source_format(str(payload.get("content", "")))
    canonical = record_to_canonical(rec, source_format=src_format, source_id=name)
    doc = {
        "project_name": name,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "name": rec.name,
        "topology": rec.topology,
        "content": f">{rec.name}\n{rec.sequence}",
        "notes": str(payload.get("notes", "")),
        "history": payload.get("history", []),
        "features": _features_to_dict(rec.features),
        "canonical_record": canonical,
    }
    path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    append_audit_event(
        COLLAB_ROOT,
        project_name=name,
        action="project_save",
        actor=str(payload.get("actor", "system")),
        details={"path": str(path), "length": rec.length, "feature_count": len(rec.features)},
    )
    return {"saved": True, "project_name": name, "path": str(path)}


def load_project(name: str) -> Dict[str, Any]:
    path = project_path(name)
    if not path.exists():
        raise ValueError("Project not found")
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc.get("canonical_record"), dict):
        try:
            record = _record_from_document(doc)
            doc["canonical_record"] = record_to_canonical(
                record,
                source_format=infer_source_format(str(doc.get("content", ""))),
                source_id=str(doc.get("project_name", name)),
            )
        except Exception:
            pass
    return doc


def list_projects() -> Dict[str, Any]:
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in sorted(PROJECTS_DIR.glob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
            rows.append(
                {
                    "project_name": doc.get("project_name", path.stem),
                    "updated_at": doc.get("updated_at", ""),
                    "path": str(path),
                }
            )
        except Exception:
            rows.append({"project_name": path.stem, "updated_at": "", "path": str(path)})
    return {"count": len(rows), "projects": rows}


def delete_project(name: str) -> Dict[str, Any]:
    path = project_path(name)
    if not path.exists():
        raise ValueError("Project not found")
    path.unlink()
    append_audit_event(COLLAB_ROOT, project_name=name, action="project_delete", actor="system", details={})
    return {"deleted": True, "project_name": name}


def collection_path(name: str) -> Path:
    safe = "".join(ch for ch in name if ch.isalnum() or ch in ("-", "_")).strip("_-")
    if not safe:
        raise ValueError("Invalid collection name")
    COLLECTIONS_DIR.mkdir(parents=True, exist_ok=True)
    return COLLECTIONS_DIR / f"{safe}.json"


def save_collection(name: str, project_names: List[str], notes: str = "") -> Dict[str, Any]:
    clean = sorted(set(str(item).strip() for item in project_names if str(item).strip()))
    doc = {
        "collection_name": name,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "projects": clean,
        "notes": notes,
    }
    path = collection_path(name)
    path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return {"saved": True, "collection_name": name, "count": len(clean), "path": str(path)}


def load_collection(name: str) -> Dict[str, Any]:
    path = collection_path(name)
    if not path.exists():
        raise ValueError("Collection not found")
    return json.loads(path.read_text(encoding="utf-8"))


def list_collections() -> Dict[str, Any]:
    COLLECTIONS_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in sorted(COLLECTIONS_DIR.glob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
            rows.append(
                {
                    "collection_name": doc.get("collection_name", path.stem),
                    "updated_at": doc.get("updated_at", ""),
                    "count": len(doc.get("projects", [])),
                    "path": str(path),
                }
            )
        except Exception:
            rows.append({"collection_name": path.stem, "updated_at": "", "count": 0, "path": str(path)})
    return {"count": len(rows), "collections": rows}


def delete_collection(name: str) -> Dict[str, Any]:
    path = collection_path(name)
    if not path.exists():
        raise ValueError("Collection not found")
    path.unlink()
    return {"deleted": True, "collection_name": name}


def add_project_to_collection(name: str, project_name: str) -> Dict[str, Any]:
    doc = load_collection(name)
    projects = sorted(set([str(item) for item in doc.get("projects", [])] + [project_name]))
    return save_collection(name, projects, notes=str(doc.get("notes", "")))


def share_bundle_path(share_id: str) -> Path:
    safe = "".join(ch for ch in share_id if ch.isalnum() or ch in ("-", "_")).strip("_-")
    if not safe:
        raise ValueError("Invalid share id")
    SHARES_DIR.mkdir(parents=True, exist_ok=True)
    return SHARES_DIR / f"{safe}.json"


def create_share_bundle(project_names: List[str], collection_name: str = "", include_content: bool = True) -> Dict[str, Any]:
    names = sorted(set(str(item).strip() for item in project_names if str(item).strip()))
    if not names and collection_name:
        collection = load_collection(collection_name)
        names = [str(item) for item in collection.get("projects", [])]
    if not names:
        raise ValueError("No projects selected for sharing")
    snapshot = []
    for name in names:
        doc = load_project(name)
        row = {
            "project_name": doc.get("project_name", name),
            "updated_at": doc.get("updated_at", ""),
            "name": doc.get("name", ""),
            "topology": doc.get("topology", ""),
        }
        if include_content:
            row["content"] = doc.get("content", "")
            row["features"] = doc.get("features", [])
        snapshot.append(row)
    share_id = uuid.uuid4().hex[:12]
    bundle = {
        "share_id": share_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "collection_name": collection_name,
        "project_count": len(snapshot),
        "projects": snapshot,
        "share_url_hint": f"/share/{share_id}",
    }
    path = share_bundle_path(share_id)
    path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    return {
        "created": True,
        "share_id": share_id,
        "path": str(path),
        "project_count": len(snapshot),
        "share_url_hint": bundle["share_url_hint"],
    }


def load_share_bundle(share_id: str) -> Dict[str, Any]:
    path = share_bundle_path(share_id)
    if not path.exists():
        raise ValueError("Share bundle not found")
    return json.loads(path.read_text(encoding="utf-8"))


def render_share_view_html(share_id: str) -> str:
    doc = load_share_bundle(share_id)
    projects = doc.get("projects", [])
    cards = []
    for project in projects:
        name = str(project.get("project_name", "unnamed"))
        topology = str(project.get("topology", ""))
        content = str(project.get("content", ""))
        sequence = ""
        try:
            if content.startswith(">"):
                sequence = parse_fasta(content).sequence
            elif content.lstrip().startswith("LOCUS"):
                sequence = parse_genbank(content).sequence
            elif content.lstrip().startswith("ID"):
                sequence = _parse_embl(content).sequence
            else:
                sequence = "".join(ch for ch in content.upper() if ch in {"A", "C", "G", "T", "N"})
        except Exception:
            sequence = "".join(ch for ch in content.upper() if ch in {"A", "C", "G", "T", "N"})
        cards.append(
            f"""
            <article style="border:1px solid #d4d4d8;border-radius:10px;padding:10px;background:#fff">
              <h3 style="margin:0 0 6px 0;font-family:Menlo,monospace">{name}</h3>
              <div style="font-size:12px;color:#334155">topology: {topology} | length: {len(sequence)} bp</div>
              <pre style="font-size:11px;background:#0f172a;color:#e2e8f0;padding:8px;border-radius:8px;overflow:auto">{sequence[:500]}</pre>
            </article>
            """
        )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Genome Forge Share {share_id}</title></head>
<body style="margin:0;background:#f8fafc;color:#0f172a;font-family:system-ui,sans-serif">
<main style="max-width:1000px;margin:24px auto;padding:0 14px">
<h1 style="margin:0 0 8px 0">Shared Bundle {share_id}</h1>
<p style="margin:0 0 16px 0;color:#475569">Projects: {doc.get('project_count', len(projects))} | Created: {doc.get('created_at', '')}</p>
<section style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:10px">
{''.join(cards)}
</section>
</main>
</body></html>"""


def project_history_graph(name: str) -> Dict[str, Any]:
    doc = load_project(name)
    history = doc.get("history", [])
    nodes = []
    edges = []
    prev = None
    for index, snapshot in enumerate(history):
        nodes.append({"id": index, "label": f"v{index+1}", "size": len(str(snapshot))})
        if prev is not None:
            edges.append({"from": prev, "to": index})
        prev = index
    return {"project_name": name, "node_count": len(nodes), "nodes": nodes, "edges": edges}


def project_history_svg(name: str) -> Dict[str, Any]:
    graph = project_history_graph(name)
    nodes = graph["nodes"]
    edges = graph["edges"]
    width = max(480, 140 * max(1, len(nodes)))
    height = 180
    y = 90
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    lines.append('<rect width="100%" height="100%" fill="#f8fafc"/>')
    if nodes:
        gap = width // (len(nodes) + 1)
        coords = {}
        for index, node in enumerate(nodes, start=1):
            coords[node["id"]] = index * gap
        for edge in edges:
            x1 = coords[edge["from"]]
            x2 = coords[edge["to"]]
            lines.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="#64748b" stroke-width="2"/>')
        for node in nodes:
            x = coords[node["id"]]
            radius = max(12, min(26, int(8 + (node["size"] ** 0.5))))
            t = 0.0 if len(nodes) <= 1 else (node["id"] / max(1, len(nodes) - 1))
            red = int(16 + 180 * t)
            green = int(118 - 48 * t)
            blue = int(110 - 30 * t)
            fill = f"rgb({red},{green},{blue})"
            lines.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{fill}" opacity="0.9"/>')
            lines.append(f'<text x="{x}" y="{y+4}" text-anchor="middle" font-size="11" fill="white">{node["label"]}</text>')
    lines.append("</svg>")
    return {"project_name": name, "svg": "\n".join(lines), **graph}


def handle_project_endpoint(path: str, payload: Dict[str, Any], get_record: RecordGetter) -> Dict[str, Any] | None:
    if path == "/api/project-permissions":
        project_name = str(payload.get("project_name", "")).strip()
        if not project_name:
            raise ValueError("project_name is required")
        if isinstance(payload.get("roles"), dict):
            return set_project_permissions(
                COLLAB_ROOT,
                project_name=project_name,
                roles={str(k): str(v) for k, v in dict(payload.get("roles", {})).items()},
            )
        return get_project_permissions(COLLAB_ROOT, project_name)
    if path == "/api/project-audit-log":
        project_name = str(payload.get("project_name", "")).strip()
        if not project_name:
            raise ValueError("project_name is required")
        if str(payload.get("action", "")).strip():
            event = append_audit_event(
                COLLAB_ROOT,
                project_name=project_name,
                action=str(payload.get("action", "")),
                actor=str(payload.get("actor", "system")),
                details=dict(payload.get("details", {})) if isinstance(payload.get("details"), dict) else {},
            )
            return {"logged": True, "event": event}
        return get_audit_log(COLLAB_ROOT, project_name, limit=int(payload.get("limit", 200)))
    if path == "/api/project-diff":
        if str(payload.get("project_name_a", "")).strip() and str(payload.get("project_name_b", "")).strip():
            project_a = load_project(str(payload.get("project_name_a", "")).strip())
            project_b = load_project(str(payload.get("project_name_b", "")).strip())
        elif isinstance(payload.get("project_a"), dict) and isinstance(payload.get("project_b"), dict):
            project_a = payload["project_a"]
            project_b = payload["project_b"]
        else:
            raise ValueError("Provide project_name_a/project_name_b or project_a/project_b")
        return diff_projects(project_a, project_b)
    if path == "/api/review-submit":
        project_name = str(payload.get("project_name", "")).strip()
        if not project_name:
            raise ValueError("project_name is required")
        snapshot = load_project(project_name)
        out = submit_review(
            COLLAB_ROOT,
            project_name=project_name,
            submitter=str(payload.get("submitter", "")).strip(),
            summary=str(payload.get("summary", "")),
            project_snapshot=snapshot,
        )
        append_audit_event(
            COLLAB_ROOT,
            project_name=project_name,
            action="review_submit",
            actor=str(payload.get("submitter", "system")),
            details={"review_id": out["review"]["review_id"]},
        )
        return out
    if path == "/api/review-approve":
        review_id = str(payload.get("review_id", "")).strip()
        reviewer = str(payload.get("reviewer", "")).strip()
        if not review_id or not reviewer:
            raise ValueError("review_id and reviewer are required")
        review_doc = load_review(COLLAB_ROOT, review_id)
        actual_project_name = str(review_doc.get("project_name", "")).strip()
        payload_project_name = str(payload.get("project_name", "")).strip()
        if payload_project_name and actual_project_name and payload_project_name != actual_project_name:
            raise ValueError("project_name does not match review project")
        project_name = payload_project_name or actual_project_name
        if project_name:
            role = role_for_user(COLLAB_ROOT, project_name, reviewer)
            if role not in {"reviewer", "owner"}:
                raise ValueError("reviewer lacks permission (requires reviewer|owner role)")
        out = approve_review(
            COLLAB_ROOT,
            review_id=review_id,
            reviewer=reviewer,
            note=str(payload.get("note", "")),
        )
        project = project_name or str(out.get("review", {}).get("project_name", "")).strip()
        if project:
            append_audit_event(
                COLLAB_ROOT,
                project_name=project,
                action="review_approve",
                actor=reviewer,
                details={"review_id": review_id},
            )
        return out
    if path == "/api/project-save":
        return save_project(payload, get_record)
    if path == "/api/project-load":
        return load_project(str(payload.get("project_name", "")).strip())
    if path == "/api/project-list":
        return list_projects()
    if path == "/api/project-delete":
        return delete_project(str(payload.get("project_name", "")).strip())
    if path == "/api/collection-save":
        projects = payload.get("projects", [])
        if isinstance(projects, str):
            projects = [item.strip() for item in projects.split(",") if item.strip()]
        return save_collection(
            str(payload.get("collection_name", "")).strip(),
            [str(item) for item in projects],
            notes=str(payload.get("notes", "")),
        )
    if path == "/api/collection-load":
        return load_collection(str(payload.get("collection_name", "")).strip())
    if path == "/api/collection-list":
        return list_collections()
    if path == "/api/collection-delete":
        return delete_collection(str(payload.get("collection_name", "")).strip())
    if path == "/api/collection-add-project":
        return add_project_to_collection(
            str(payload.get("collection_name", "")).strip(),
            str(payload.get("project_name", "")).strip(),
        )
    if path == "/api/share-create":
        projects = payload.get("projects", [])
        if isinstance(projects, str):
            projects = [item.strip() for item in projects.split(",") if item.strip()]
        return create_share_bundle(
            [str(item) for item in projects],
            collection_name=str(payload.get("collection_name", "")).strip(),
            include_content=bool(payload.get("include_content", True)),
        )
    if path == "/api/share-load":
        return load_share_bundle(str(payload.get("share_id", "")).strip())
    if path == "/api/project-history-graph":
        return project_history_graph(str(payload.get("project_name", "")).strip())
    if path == "/api/project-history-svg":
        return project_history_svg(str(payload.get("project_name", "")).strip())
    return None
