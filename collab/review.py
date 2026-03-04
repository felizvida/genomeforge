from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def _safe_name(name: str, label: str = "name") -> str:
    safe = "".join(ch for ch in str(name) if ch.isalnum() or ch in ("-", "_")).strip("_-")
    if not safe:
        raise ValueError(f"Invalid {label}")
    return safe


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def review_path(root: Path, review_id: str) -> Path:
    d = root / "reviews"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{_safe_name(review_id, 'review_id')}.json"


def submit_review(
    root: Path,
    project_name: str,
    submitter: str,
    summary: str = "",
    project_snapshot: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    sub = str(submitter).strip()
    if not sub:
        raise ValueError("submitter is required")
    rid = "rev_" + uuid.uuid4().hex[:10]
    doc = {
        "review_id": rid,
        "project_name": _safe_name(project_name, "project_name"),
        "status": "submitted",
        "submitter": sub,
        "summary": str(summary or ""),
        "submitted_at": _now(),
        "updated_at": _now(),
        "approved_by": "",
        "approved_at": "",
        "project_snapshot": project_snapshot or {},
    }
    p = review_path(root, rid)
    p.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return {"submitted": True, "review": doc, "path": str(p)}


def approve_review(root: Path, review_id: str, reviewer: str, note: str = "") -> Dict[str, Any]:
    p = review_path(root, review_id)
    if not p.exists():
        raise ValueError("Review not found")
    doc = json.loads(p.read_text(encoding="utf-8"))
    if str(doc.get("status", "")) == "approved":
        return {"approved": True, "review": doc, "already_approved": True}
    doc["status"] = "approved"
    doc["approved_by"] = str(reviewer).strip()
    doc["approved_at"] = _now()
    doc["approval_note"] = str(note or "")
    doc["updated_at"] = _now()
    p.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return {"approved": True, "review": doc}

