import importlib.util
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def has_package(package):
    try:
        return importlib.util.find_spec(package) is not None
    except (ImportError, ValueError):
        return False


HAS_ENDPOINT_DEPS = all(
    has_package(package)
    for package in ("flask", "flask_mail", "flask_sqlalchemy", "sqlalchemy")
)


if HAS_ENDPOINT_DEPS:
    from flask import Flask

    from api.email_routes import (
        ISSUE_RATE_LIMIT_REQUESTS,
        _issue_rate_limiter,
        email_bp,
    )


def png_bytes(extra=b""):
    return b"\x89PNG\r\n\x1a\n" + extra


@unittest.skipUnless(
    HAS_ENDPOINT_DEPS,
    "Flask/Flask-Mail/SQLAlchemy test dependencies are not installed.",
)
class IssueReportEndpointTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            MAIL_DEFAULT_SENDER="sender@example.com",
        )
        self.app.register_blueprint(email_bp, url_prefix="/api/email")
        self.client = self.app.test_client()
        _issue_rate_limiter.reset()
        self.payload = {
            "name": "Ana Cliente",
            "email": "ana@example.com",
            "order_number": "MW1234",
            "issue_type": "Pintura o acabado",
            "message": "Hay una marca visible en el acabado.",
        }

    def tearDown(self):
        _issue_rate_limiter.reset()

    @patch("api.email_routes._send_issue_report_email")
    def test_required_fields_are_validated(self, send_issue_report_email):
        response = self.client.post(
            "/api/email/report-issue",
            data={key: value for key, value in self.payload.items() if key != "order_number"},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 400)
        send_issue_report_email.assert_not_called()

    @patch("api.email_routes._send_issue_report_email")
    def test_multiple_images_are_forwarded(self, send_issue_report_email):
        response = self.client.post(
            "/api/email/report-issue",
            data={
                **self.payload,
                "images": [
                    (io.BytesIO(png_bytes()), "detalle-uno.png"),
                    (io.BytesIO(png_bytes(b"two")), "detalle-dos.png"),
                ],
            },
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        issue_data, attachments = send_issue_report_email.call_args.args
        self.assertEqual(issue_data["name"], "Ana Cliente")
        self.assertEqual(len(attachments), 2)
        self.assertEqual(attachments[0][0], "detalle-uno.png")
        self.assertEqual(attachments[1][0], "detalle-dos.png")

    @patch("api.email_routes._send_issue_report_email")
    def test_rejects_invalid_mime_and_oversized_images(self, send_issue_report_email):
        invalid_type = self.client.post(
            "/api/email/report-issue",
            data={**self.payload, "images": (io.BytesIO(b"not-an-image"), "detalle.txt")},
            content_type="multipart/form-data",
        )
        self.assertEqual(invalid_type.status_code, 400)

        with patch("api.email_routes.ISSUE_MAX_IMAGE_BYTES", 16):
            oversized = self.client.post(
                "/api/email/report-issue",
                data={
                    **self.payload,
                    "images": (io.BytesIO(png_bytes(b"x" * 20)), "detalle.png"),
                },
                content_type="multipart/form-data",
            )
        self.assertEqual(oversized.status_code, 400)
        send_issue_report_email.assert_not_called()

    @patch("api.email_routes._send_issue_report_email")
    def test_rejects_more_than_three_images(self, send_issue_report_email):
        response = self.client.post(
            "/api/email/report-issue",
            data={
                **self.payload,
                "images": [
                    (io.BytesIO(png_bytes()), "uno.png"),
                    (io.BytesIO(png_bytes()), "dos.png"),
                    (io.BytesIO(png_bytes()), "tres.png"),
                    (io.BytesIO(png_bytes()), "cuatro.png"),
                ],
            },
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 400)
        send_issue_report_email.assert_not_called()

    @patch("api.email_routes._send_issue_report_email")
    def test_rate_limit_returns_429(self, send_issue_report_email):
        for _ in range(ISSUE_RATE_LIMIT_REQUESTS):
            response = self.client.post(
                "/api/email/report-issue",
                data=self.payload,
                content_type="multipart/form-data",
            )
            self.assertEqual(response.status_code, 200)

        response = self.client.post(
            "/api/email/report-issue",
            data=self.payload,
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 429)
        self.assertGreater(int(response.headers["Retry-After"]), 0)

    @patch("api.email_routes._send_issue_report_email", side_effect=RuntimeError("private data"))
    def test_delivery_error_is_safe(self, send_issue_report_email):
        with self.assertLogs(self.app.logger.name, level="ERROR") as logs:
            response = self.client.post(
                "/api/email/report-issue",
                data=self.payload,
                content_type="multipart/form-data",
            )

        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private data", response.get_data(as_text=True))
        self.assertNotIn("ana@example.com", " ".join(logs.output))


if __name__ == "__main__":
    unittest.main()
