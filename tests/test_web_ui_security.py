from __future__ import annotations

import io
import unittest

from web_ui import Handler, SECURITY_HEADERS, validate_bind_host


class HeaderCaptureHandler(Handler):
    def send_header(self, keyword: str, value: str) -> None:
        self.captured_headers[keyword] = value
        super().send_header(keyword, value)


def make_handler_for_header_capture() -> HeaderCaptureHandler:
    handler = HeaderCaptureHandler.__new__(HeaderCaptureHandler)
    handler.captured_headers = {}
    handler._headers_buffer = []  # noqa: SLF001
    handler.wfile = io.BytesIO()
    handler.request_version = "HTTP/1.1"
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
