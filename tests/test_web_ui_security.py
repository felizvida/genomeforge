from __future__ import annotations

import io
import unittest

from web_ui import Handler, SECURITY_HEADERS


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
