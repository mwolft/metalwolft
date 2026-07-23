import importlib.util
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
        CONTACT_RATE_LIMIT_REQUESTS,
        CONTACT_SMTP_TIMEOUT_SECONDS,
        _contact_rate_limiter,
        email_bp,
    )


@unittest.skipUnless(
    HAS_ENDPOINT_DEPS,
    "Flask/Flask-Mail/SQLAlchemy test dependencies are not installed.",
)
class ContactEndpointSecurityTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            MAIL_SERVER="smtp.example.com",
            MAIL_PORT=587,
            MAIL_USE_TLS=False,
            MAIL_USE_SSL=False,
            MAIL_USERNAME=None,
            MAIL_PASSWORD=None,
            MAIL_DEFAULT_SENDER="sender@example.com",
        )
        self.app.register_blueprint(email_bp, url_prefix="/api/email")
        self.client = self.app.test_client()
        _contact_rate_limiter.reset()
        self.payload = {
            "name": "Ana",
            "firstname": "Cliente",
            "phone": "+34 600 123 123",
            "email": "ana@example.com",
            "message": "Necesito información sobre una reja a medida.",
        }

    def tearDown(self):
        _contact_rate_limiter.reset()

    @patch("api.email_routes._send_contact_email")
    def test_valid_contact_is_normalized_and_sent(self, send_contact_email):
        payload = dict(self.payload, name="  Ana   María  ")

        response = self.client.post("/api/email/contact", json=payload)

        self.assertEqual(response.status_code, 200)
        sent_data = send_contact_email.call_args.args[0]
        self.assertEqual(sent_data["name"], "Ana María")
        self.assertEqual(sent_data["email"], "ana@example.com")

    @patch("api.email_routes._send_contact_email")
    def test_invalid_fields_return_400_without_sending_email(self, send_contact_email):
        invalid_values = {
            "name": "",
            "firstname": "x" * 121,
            "email": "not-an-email",
            "phone": "123",
            "message": "short",
        }

        for field, value in invalid_values.items():
            with self.subTest(field=field):
                _contact_rate_limiter.reset()
                response = self.client.post(
                    "/api/email/contact",
                    json=dict(self.payload, **{field: value}),
                )
                self.assertEqual(response.status_code, 400)

        send_contact_email.assert_not_called()

    @patch("api.email_routes._send_contact_email")
    def test_oversized_request_returns_400_without_sending_email(
        self, send_contact_email
    ):
        response = self.client.post(
            "/api/email/contact",
            json=dict(self.payload, message="x" * 17_000),
        )

        self.assertEqual(response.status_code, 400)
        send_contact_email.assert_not_called()

    @patch("api.email_routes._send_contact_email")
    def test_rate_limit_returns_429_with_retry_after(self, send_contact_email):
        for _ in range(CONTACT_RATE_LIMIT_REQUESTS):
            response = self.client.post("/api/email/contact", json=self.payload)
            self.assertEqual(response.status_code, 200)

        response = self.client.post("/api/email/contact", json=self.payload)

        self.assertEqual(response.status_code, 429)
        self.assertGreater(int(response.headers["Retry-After"]), 0)
        self.assertEqual(send_contact_email.call_count, CONTACT_RATE_LIMIT_REQUESTS)

    @patch("api.email_routes.smtplib.SMTP", side_effect=TimeoutError("private data"))
    def test_smtp_timeout_returns_safe_503(self, smtp):
        with self.assertLogs(self.app.logger.name, level="WARNING") as logs:
            response = self.client.post("/api/email/contact", json=self.payload)

        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private data", response.get_data(as_text=True))
        self.assertNotIn(self.payload["email"], " ".join(logs.output))
        self.assertNotIn(self.payload["message"], " ".join(logs.output))
        smtp.assert_called_once_with(
            host="smtp.example.com",
            port=587,
            timeout=CONTACT_SMTP_TIMEOUT_SECONDS,
        )

    @patch(
        "api.email_routes._send_contact_email",
        side_effect=ValueError("ana@example.com private data"),
    )
    def test_unexpected_error_returns_safe_500(self, send_contact_email):
        with self.assertLogs(self.app.logger.name, level="ERROR") as logs:
            response = self.client.post("/api/email/contact", json=self.payload)

        self.assertEqual(response.status_code, 500)
        public_response = response.get_data(as_text=True)
        log_output = " ".join(logs.output)
        self.assertNotIn("ana@example.com", public_response)
        self.assertNotIn("ana@example.com", log_output)
        self.assertNotIn("private data", log_output)


if __name__ == "__main__":
    unittest.main()
