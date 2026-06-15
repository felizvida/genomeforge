from __future__ import annotations

from typing import Any, Callable, Dict

from compat.interop_audit import compatibility_audit, golden_project_compatibility_report
from genomeforge_toolkit import SequenceRecord


RecordGetter = Callable[[], SequenceRecord]


def handle_compatibility_endpoint(path: str, payload: Dict[str, Any], get_record: RecordGetter) -> Dict[str, Any] | None:
    if path == "/api/compatibility-audit":
        return compatibility_audit(payload, get_record)

    if path == "/api/compatibility-golden-project":
        return golden_project_compatibility_report(payload)

    return None
