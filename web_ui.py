#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict

from backend.analysis_api import handle_analysis_endpoint
from backend.assembly_api import handle_assembly_endpoint
from backend.biology_api import handle_biology_endpoint
from backend.core_api import handle_core_endpoint, parse_record
from backend.design_api import handle_design_endpoint
from backend.ngs_api import handle_ngs_endpoint
from backend.project_api import handle_project_endpoint, render_share_view_html
from backend.search_reference_api import handle_search_reference_endpoint
from backend.trace_api import handle_trace_endpoint
from genomeforge_toolkit import SequenceRecord

ROOT = Path(__file__).resolve().parent
WEBUI_ROOT = ROOT / "webui"
INDEX_PATH = WEBUI_ROOT / "index.html"
COLLAB_ROOT = ROOT / "collab_data"
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
DEFAULT_MAX_POST_BYTES = 64 * 1024 * 1024


SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "font-src 'self'; "
        "object-src 'none'; "
        "base-uri 'none'; "
        "form-action 'none'; "
        "frame-ancestors 'none'"
    ),
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
}


class PayloadTooLargeError(ValueError):
    pass


def parse_content_length(value: str | None) -> int:
    if value is None or str(value).strip() == "":
        return 0
    try:
        length = int(str(value).strip())
    except ValueError as exc:
        raise ValueError("Content-Length must be an integer") from exc
    if length < 0:
        raise ValueError("Content-Length cannot be negative")
    return length


def payload_limit_bytes_from_mb(max_post_mb: int) -> int:
    if max_post_mb < 1:
        raise ValueError("max-post-mb must be at least 1")
    return max_post_mb * 1024 * 1024


def validate_post_length(length: int, max_bytes: int = DEFAULT_MAX_POST_BYTES) -> int:
    if max_bytes < 1:
        raise ValueError("max_post_bytes must be positive")
    if length > max_bytes:
        raise PayloadTooLargeError(f"POST body exceeds configured limit of {max_bytes} bytes")
    return length


class Handler(BaseHTTPRequestHandler):
    max_post_bytes = DEFAULT_MAX_POST_BYTES

    def end_headers(self) -> None:
        for name, value in SECURITY_HEADERS.items():
            self.send_header(name, value)
        super().end_headers()

    def _send_json(self, data: Dict[str, Any], status: int = 200) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str, status: int = 200) -> None:
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, file_path: Path, status: int = 200) -> None:
        body = file_path.read_bytes()
        mime_type, _ = mimetypes.guess_type(str(file_path))
        content_type = mime_type or "application/octet-stream"
        if content_type.startswith("text/") or content_type in {"application/javascript", "application/json"}:
            content_type = f"{content_type}; charset=utf-8"
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        request_path = self.path.split("?", 1)[0]
        if request_path in {"/", "/index.html"}:
            self._send_html(INDEX_PATH.read_text(encoding="utf-8"))
            return
        if request_path.startswith("/share/"):
            share_id = request_path.split("/share/", 1)[1].strip().strip("/")
            if not share_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not Found")
                return
            try:
                self._send_html(render_share_view_html(share_id))
            except Exception as e:
                self.send_error(HTTPStatus.NOT_FOUND, str(e))
            return
        static_path = (WEBUI_ROOT / request_path.lstrip("/")).resolve()
        try:
            static_path.relative_to(WEBUI_ROOT.resolve())
        except ValueError:
            self.send_error(HTTPStatus.NOT_FOUND, "Not Found")
            return
        if static_path.is_file():
            self._send_file(static_path)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def do_POST(self) -> None:  # noqa: N802
        try:
            n = validate_post_length(
                parse_content_length(self.headers.get("Content-Length")),
                self.max_post_bytes,
            )
        except PayloadTooLargeError as e:
            self._send_json(
                {"error": str(e), "max_post_bytes": self.max_post_bytes},
                status=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
            )
            return
        except ValueError as e:
            self._send_json({"error": str(e)}, status=400)
            return

        try:
            payload = json.loads(self.rfile.read(n).decode("utf-8") if n > 0 else "{}")
            record: SequenceRecord | None = None

            def get_record() -> SequenceRecord:
                nonlocal record
                if record is None:
                    record = parse_record(payload)
                return record

            if (domain_response := handle_core_endpoint(self.path, payload, get_record, COLLAB_ROOT)) is not None:
                self._send_json(domain_response)
            elif (domain_response := handle_trace_endpoint(self.path, payload)) is not None:
                self._send_json(domain_response)
            elif (domain_response := handle_search_reference_endpoint(self.path, payload, get_record)) is not None:
                self._send_json(domain_response)
            elif (domain_response := handle_design_endpoint(self.path, payload, get_record)) is not None:
                self._send_json(domain_response)
            elif (domain_response := handle_analysis_endpoint(self.path, payload, get_record)) is not None:
                self._send_json(domain_response)
            elif (domain_response := handle_ngs_endpoint(self.path, payload, get_record)) is not None:
                self._send_json(domain_response)
            elif (domain_response := handle_biology_endpoint(self.path, payload, get_record)) is not None:
                self._send_json(domain_response)
            elif (domain_response := handle_project_endpoint(self.path, payload, get_record)) is not None:
                self._send_json(domain_response)
            elif (domain_response := handle_assembly_endpoint(self.path, payload)) is not None:
                self._send_json(domain_response)
            else:
                self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")
        except Exception as e:  # pragma: no cover - user-facing service
            self._send_json({"error": str(e)}, status=400)


def is_loopback_host(host: str) -> bool:
    return str(host).strip().lower() in LOOPBACK_HOSTS


def validate_bind_host(host: str, allow_remote: bool = False) -> str:
    clean_host = str(host).strip() or "127.0.0.1"
    if is_loopback_host(clean_host) or allow_remote:
        return clean_host
    raise ValueError(
        "Refusing to bind Genome Forge to a non-loopback host without --allow-remote. "
        "This local-first server does not provide production-grade authentication."
    )


def run(
    host: str = "127.0.0.1",
    port: int = 8080,
    allow_remote: bool = False,
    max_post_mb: int = DEFAULT_MAX_POST_BYTES // (1024 * 1024),
) -> None:
    host = validate_bind_host(host, allow_remote=allow_remote)
    Handler.max_post_bytes = payload_limit_bytes_from_mb(max_post_mb)
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Genome Forge web UI running at http://{host}:{port} (max POST {max_post_mb} MiB)")
    server.serve_forever()


def main() -> None:
    ap = argparse.ArgumentParser(description="Run Genome Forge local web UI")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument(
        "--allow-remote",
        action="store_true",
        help="Allow binding to a non-loopback host. Use only behind a trusted network boundary.",
    )
    ap.add_argument(
        "--max-post-mb",
        type=int,
        default=DEFAULT_MAX_POST_BYTES // (1024 * 1024),
        help="Maximum accepted JSON POST body size in MiB.",
    )
    args = ap.parse_args()
    run(host=args.host, port=args.port, allow_remote=args.allow_remote, max_post_mb=args.max_post_mb)


if __name__ == "__main__":
    main()
