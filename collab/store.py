from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def _safe_name(name: str, label: str = "name") -> str:
    safe = "".join(ch for ch in str(name) if ch.isalnum() or ch in ("-", "_")).strip("_-")
    if not safe:
        raise ValueError(f"Invalid {label}")
    return safe


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def workspace_path(root: Path, workspace_name: str) -> Path:
    d = root / "workspaces"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{_safe_name(workspace_name, 'workspace_name')}.json"


def permissions_path(root: Path, project_name: str) -> Path:
    d = root / "permissions"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{_safe_name(project_name, 'project_name')}.json"


def audit_path(root: Path, project_name: str) -> Path:
    d = root / "audit_logs"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{_safe_name(project_name, 'project_name')}.json"


def create_workspace(root: Path, workspace_name: str, owner: str, members: List[str] | None = None) -> Dict[str, Any]:
    owner = str(owner).strip()
    if not owner:
        raise ValueError("owner is required")
    m = sorted(set([owner] + [str(x).strip() for x in (members or []) if str(x).strip()]))
    doc = {
        "workspace_name": _safe_name(workspace_name, "workspace_name"),
        "owner": owner,
        "members": m,
        "created_at": _now(),
        "updated_at": _now(),
    }
    p = workspace_path(root, workspace_name)
    p.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return {"created": True, "workspace": doc, "path": str(p)}


def get_project_permissions(root: Path, project_name: str) -> Dict[str, Any]:
    p = permissions_path(root, project_name)
    if not p.exists():
        return {
            "project_name": _safe_name(project_name, "project_name"),
            "roles": {},
            "updated_at": "",
        }
    return json.loads(p.read_text(encoding="utf-8"))


def set_project_permissions(root: Path, project_name: str, roles: Dict[str, str]) -> Dict[str, Any]:
    clean: Dict[str, str] = {}
    for user, role in dict(roles or {}).items():
        u = str(user).strip()
        r = str(role).strip().lower()
        if not u:
            continue
        if r not in {"viewer", "editor", "reviewer", "owner"}:
            raise ValueError(f"Unsupported role for {u}: {r}")
        clean[u] = r
    doc = {
        "project_name": _safe_name(project_name, "project_name"),
        "roles": clean,
        "updated_at": _now(),
    }
    p = permissions_path(root, project_name)
    p.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return {"saved": True, "permissions": doc, "path": str(p)}


def role_for_user(root: Path, project_name: str, user: str) -> str:
    perms = get_project_permissions(root, project_name).get("roles", {})
    if not isinstance(perms, dict):
        return "viewer"
    return str(perms.get(str(user), "viewer")).lower()


def append_audit_event(
    root: Path,
    project_name: str,
    action: str,
    actor: str = "system",
    details: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    p = audit_path(root, project_name)
    if p.exists():
        doc = json.loads(p.read_text(encoding="utf-8"))
    else:
        doc = {"project_name": _safe_name(project_name, "project_name"), "events": [], "updated_at": _now()}
    events = doc.get("events", [])
    if not isinstance(events, list):
        events = []
    row = {
        "timestamp": _now(),
        "actor": str(actor or "system"),
        "action": str(action),
        "details": details or {},
    }
    events.append(row)
    doc["events"] = events[-1000:]
    doc["updated_at"] = _now()
    p.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return row


def get_audit_log(root: Path, project_name: str, limit: int = 200) -> Dict[str, Any]:
    p = audit_path(root, project_name)
    if not p.exists():
        return {"project_name": _safe_name(project_name, "project_name"), "count": 0, "events": []}
    doc = json.loads(p.read_text(encoding="utf-8"))
    events = doc.get("events", [])
    if not isinstance(events, list):
        events = []
    lim = max(1, min(2000, int(limit)))
    tail = events[-lim:]
    return {"project_name": doc.get("project_name", project_name), "count": len(tail), "events": tail}

