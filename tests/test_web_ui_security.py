from __future__ import annotations

import io
import unittest

from web_ui import (
    DEFAULT_MAX_POST_BYTES,
    Handler,
    PayloadTooLargeError,
    SECURITY_HEADERS,
    parse_content_length,
    payload_limit_bytes_from_mb,
    validate_bind_host,
    validate_post_length,
)


class HeaderCaptureHandler(Handler):
    def send_header(self, keyword: str, value: str) -> None:
        self.captured_headers[keyword] = value
        super().send_header(keyword, value)


class JsonCaptureHandler(Handler):
    def _send_json(self, data, status: int = 200) -> None:
        self.sent_json = data
        self.sent_status = status


def make_handler_for_header_capture() -> HeaderCaptureHandler:
    handler = HeaderCaptureHandler.__new__(HeaderCaptureHandler)
    handler.captured_headers = {}
    handler._headers_buffer = []  # noqa: SLF001
    handler.wfile = io.BytesIO()
    handler.request_version = "HTTP/1.1"
    return handler


def make_handler_for_post_capture(content_length: int | str) -> JsonCaptureHandler:
    handler = JsonCaptureHandler.__new__(JsonCaptureHandler)
    handler.sent_json = None
    handler.sent_status = None
    handler.headers = {"Content-Length": str(content_length)}
    handler.rfile = io.BytesIO(b"")
    handler.wfile = io.BytesIO()
    handler.path = "/api/info"
    return handler


class WebUiSecurityHeaderTests(unittest.TestCase):
    def test_handler_emits_local_security_headers(self) -> None:
        handler = make_handler_for_header_capture()
        handler.end_headers()

        self.assertEqual(handler.captured_headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(handler.captured_headers["X-Frame-Options"], "DENY")
        self.assertEqual(handler.captured_headers["Referrer-Policy"], "no-referrer")
        self.assertEqual(handler.captured_headers["Cross-Origin-Opener-Policy"], "same-origin")
        self.assertIn("Permissions-Policy", handler.captured_headers)

    def test_csp_keeps_scripts_and_connections_local(self) -> None:
        csp = SECURITY_HEADERS["Content-Security-Policy"]

        self.assertIn("default-src 'self'", csp)
        self.assertIn("script-src 'self'", csp)
        self.assertIn("connect-src 'self'", csp)
        self.assertIn("img-src 'self' data:", csp)
        self.assertIn("object-src 'none'", csp)
        self.assertIn("frame-ancestors 'none'", csp)
        self.assertNotIn("script-src 'self' 'unsafe-inline'", csp)

    def test_loopback_bind_hosts_are_allowed_by_default(self) -> None:
        self.assertEqual(validate_bind_host("127.0.0.1"), "127.0.0.1")
        self.assertEqual(validate_bind_host("localhost"), "localhost")
        self.assertEqual(validate_bind_host("::1"), "::1")
        self.assertEqual(validate_bind_host(""), "127.0.0.1")

    def test_non_loopback_bind_host_requires_explicit_opt_in(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-loopback"):
            validate_bind_host("0.0.0.0")
        with self.assertRaisesRegex(ValueError, "non-loopback"):
            validate_bind_host("192.168.1.10")

    def test_non_loopback_bind_host_can_be_explicitly_allowed(self) -> None:
        self.assertEqual(validate_bind_host("0.0.0.0", allow_remote=True), "0.0.0.0")

    def test_content_length_parsing_rejects_invalid_values(self) -> None:
        self.assertEqual(parse_content_length(None), 0)
        self.assertEqual(parse_content_length(" 42 "), 42)
        with self.assertRaisesRegex(ValueError, "integer"):
            parse_content_length("abc")
        with self.assertRaisesRegex(ValueError, "negative"):
            parse_content_length("-1")

    def test_post_length_limit_accepts_boundary_and_rejects_oversize(self) -> None:
        self.assertEqual(validate_post_length(DEFAULT_MAX_POST_BYTES), DEFAULT_MAX_POST_BYTES)
        with self.assertRaisesRegex(PayloadTooLargeError, "configured limit"):
            validate_post_length(DEFAULT_MAX_POST_BYTES + 1)

    def test_post_size_limit_can_be_configured_in_mebibytes(self) -> None:
        self.assertEqual(payload_limit_bytes_from_mb(1), 1024 * 1024)
        self.assertEqual(payload_limit_bytes_from_mb(64), DEFAULT_MAX_POST_BYTES)
        with self.assertRaisesRegex(ValueError, "at least 1"):
            payload_limit_bytes_from_mb(0)

    def test_oversized_post_returns_payload_too_large(self) -> None:
        handler = make_handler_for_post_capture(DEFAULT_MAX_POST_BYTES + 1)
        handler.do_POST()

        self.assertEqual(handler.sent_status, 413)
        self.assertEqual(handler.sent_json["max_post_bytes"], DEFAULT_MAX_POST_BYTES)
        self.assertIn("configured limit", handler.sent_json["error"])
