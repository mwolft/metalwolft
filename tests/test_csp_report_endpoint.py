import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def has_package(package):
    try:
        return importlib.util.find_spec(package) is not None
    except (ImportError, ValueError):
        return False


HAS_ENDPOINT_DEPS = has_package("flask")


if HAS_ENDPOINT_DEPS:
    from flask import Flask

    from api.security_routes import (
        CSP_REPORT_MAX_BYTES,
        CSP_REPORT_RATE_LIMIT_REQUESTS,
        _csp_report_rate_limiter,
        security_bp,
    )


@unittest.skipUnless(HAS_ENDPOINT_DEPS, "Flask test dependency is not installed.")
class CspReportEndpointTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(TESTING=True)
        self.app.register_blueprint(security_bp, url_prefix="/api")
        self.client = self.app.test_client()
        _csp_report_rate_limiter.reset()

    def tearDown(self):
        _csp_report_rate_limiter.reset()

    @staticmethod
    def legacy_report():
        return {
            "csp-report": {
                "blocked-uri": "inline",
                "violated-directive": "script-src-elem",
                "effective-directive": "script-src-elem",
                "document-uri": "https://www.metalwolft.com/cart?email=private@example.test",
                "source-file": "https://www.metalwolft.com/_next/static/app.js?token=secret",
                "line-number": 12,
                "column-number": 8,
                "disposition": "report",
            }
        }

    def test_accepts_and_sanitizes_legacy_report_without_persistence(self):
        with self.assertLogs(self.app.logger.name, level="INFO") as logs:
            response = self.client.post(
                "/api/security/csp-report",
                data=json.dumps(self.legacy_report()),
                content_type="application/csp-report",
            )

        self.assertEqual(response.status_code, 204)
        log_output = " ".join(logs.output)
        self.assertIn('"event":"csp_violation_report"', log_output)
        self.assertIn("https://www.metalwolft.com/cart", log_output)
        self.assertNotIn("private@example.test", log_output)
        self.assertNotIn("token=secret", log_output)
        self.assertNotIn("Authorization", log_output)

    def test_accepts_reporting_api_format(self):
        payload = [
            {
                "type": "csp-violation",
                "body": {
                    "blockedURL": "https://www.googletagmanager.com/gtm.js?id=private",
                    "violatedDirective": "script-src-elem",
                    "effectiveDirective": "script-src-elem",
                    "documentURL": "https://www.metalwolft.com/",
                    "disposition": "report",
                },
            }
        ]

        response = self.client.post(
            "/api/security/csp-report",
            data=json.dumps(payload),
            content_type="application/reports+json",
        )

        self.assertEqual(response.status_code, 204)

    def test_rejects_oversized_or_invalid_payloads(self):
        oversized = b"x" * (CSP_REPORT_MAX_BYTES + 1)
        response = self.client.post(
            "/api/security/csp-report",
            data=oversized,
            content_type="application/csp-report",
        )
        self.assertEqual(response.status_code, 413)

        invalid = self.client.post(
            "/api/security/csp-report",
            data="not-json",
            content_type="application/csp-report",
        )
        self.assertEqual(invalid.status_code, 400)

    def test_rate_limit_returns_429_without_storing_reports(self):
        payload = json.dumps(self.legacy_report())
        for _ in range(CSP_REPORT_RATE_LIMIT_REQUESTS):
            response = self.client.post(
                "/api/security/csp-report",
                data=payload,
                content_type="application/csp-report",
            )
            self.assertEqual(response.status_code, 204)

        response = self.client.post(
            "/api/security/csp-report",
            data=payload,
            content_type="application/csp-report",
        )
        self.assertEqual(response.status_code, 429)
        self.assertGreater(int(response.headers["Retry-After"]), 0)

    def test_rejects_unknown_content_type(self):
        response = self.client.post(
            "/api/security/csp-report",
            data=json.dumps(self.legacy_report()),
            content_type="text/plain",
        )
        self.assertEqual(response.status_code, 415)


if __name__ == "__main__":
    unittest.main()
