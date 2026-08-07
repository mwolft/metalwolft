import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from api.database_identity import (  # noqa: E402
    DatabaseIdentityError,
    mask_database_identity,
    parse_database_identity,
    validate_database_identity,
)
from scripts.inspect_database_identity import run_identity_check  # noqa: E402


SECRET = "super-secret-password"
VALID_URL = (
    "postgresql://fake_user:super-secret-password@"
    "ep-fake-branch.example.test:5432/fake_database?sslmode=require"
)
FULL_URL_WITH_SECRET = (
    "postgresql://fake_user:super-secret-password@"
    "ep-fake-branch.example.test:5432/fake_database"
)
SENSITIVE_OUTPUT_VALUES = (
    SECRET,
    "203.0.113.10",
    "other_password",
    "/tmp/services",
)


class DatabaseIdentityTest(unittest.TestCase):
    def assert_database_url_is_rejected_safely(
        self,
        database_url,
        expected_message,
    ):
        with self.assertRaises(DatabaseIdentityError) as context:
            parse_database_identity(database_url)

        message = str(context.exception)
        self.assertIn(expected_message, message)
        self.assertNotIn(FULL_URL_WITH_SECRET, message)
        for sensitive_value in SENSITIVE_OUTPUT_VALUES:
            self.assertNotIn(sensitive_value, message)

    def test_valid_postgresql_url_is_parsed(self):
        identity = parse_database_identity(VALID_URL)

        self.assertEqual(identity.scheme, "postgresql")
        self.assertEqual(identity.host, "ep-fake-branch.example.test")
        self.assertEqual(identity.port, 5432)
        self.assertEqual(identity.database_name, "fake_database")
        self.assertEqual(identity.username, "fake_user")

    def test_valid_postgres_url_is_normalized(self):
        identity = parse_database_identity(
            "postgres://fake_user:super-secret-password@"
            "ep-fake-branch.example.test:5432/fake_database"
        )

        self.assertEqual(identity.scheme, "postgresql")

    def test_password_never_appears_in_safe_representation(self):
        identity = parse_database_identity(VALID_URL)
        safe_representation = repr(mask_database_identity(identity))

        self.assertNotIn(SECRET, safe_representation)
        self.assertNotIn(FULL_URL_WITH_SECRET, safe_representation)

    def test_query_string_is_not_exposed(self):
        identity = parse_database_identity(VALID_URL)
        safe_representation = repr(mask_database_identity(identity))

        self.assertNotIn("sslmode", safe_representation)
        self.assertNotIn("?sslmode=require", safe_representation)

    def test_allowed_sslmode_query_parameter_is_accepted(self):
        identity = parse_database_identity(
            FULL_URL_WITH_SECRET + "?sslmode=require"
        )

        self.assertEqual(identity.host, "ep-fake-branch.example.test")

    def test_allowed_channel_binding_query_parameter_is_accepted(self):
        identity = parse_database_identity(
            FULL_URL_WITH_SECRET + "?channel_binding=require"
        )

        self.assertEqual(identity.host, "ep-fake-branch.example.test")

    def test_allowed_query_parameters_can_be_combined_once(self):
        identity = parse_database_identity(
            FULL_URL_WITH_SECRET + "?sslmode=require&channel_binding=require"
        )

        self.assertEqual(identity.database_name, "fake_database")

    def test_dangerous_query_parameters_are_rejected_safely(self):
        cases = (
            ("?host=evil.example.test", "unsupported query parameter: host."),
            ("?hostaddr=203.0.113.10", "unsupported query parameter: hostaddr."),
            ("?port=6543", "unsupported query parameter: port."),
            ("?dbname=other_database", "unsupported query parameter: dbname."),
            ("?user=other_user", "unsupported query parameter: user."),
            ("?password=other_password", "unsupported query parameter: password."),
            ("?passfile=/tmp/file", "unsupported query parameter: passfile."),
            ("?service=production", "unsupported query parameter: service."),
            ("?servicefile=/tmp/services", "unsupported query parameter: servicefile."),
        )

        for query_string, expected_message in cases:
            with self.subTest(query_string=query_string):
                self.assert_database_url_is_rejected_safely(
                    FULL_URL_WITH_SECRET + query_string,
                    expected_message,
                )

    def test_unknown_query_parameter_is_rejected_safely(self):
        self.assert_database_url_is_rejected_safely(
            FULL_URL_WITH_SECRET + "?unknown=value",
            "unsupported query parameter: unknown.",
        )

    def test_duplicate_allowed_query_parameter_is_rejected_safely(self):
        self.assert_database_url_is_rejected_safely(
            FULL_URL_WITH_SECRET + "?sslmode=require&sslmode=disable",
            "duplicate query parameter: sslmode.",
        )

    def test_empty_allowed_query_parameter_value_is_rejected_safely(self):
        self.assert_database_url_is_rejected_safely(
            FULL_URL_WITH_SECRET + "?sslmode=",
            "empty value for query parameter: sslmode.",
        )

    def test_query_parameter_without_name_is_rejected_safely(self):
        self.assert_database_url_is_rejected_safely(
            FULL_URL_WITH_SECRET + "?=require",
            "query parameter without a name.",
        )

    def test_multiple_hosts_are_rejected_safely(self):
        self.assert_database_url_is_rejected_safely(
            "postgresql://fake_user:super-secret-password@"
            "host1.example.test,host2.example.test/fake_database",
            "exactly one database host.",
        )

    def test_fragment_is_rejected_safely(self):
        self.assert_database_url_is_rejected_safely(
            FULL_URL_WITH_SECRET + "#fragment",
            "must not include a fragment.",
        )

    def test_missing_database_url_is_rejected(self):
        with self.assertRaisesRegex(DatabaseIdentityError, "DATABASE_URL is required"):
            parse_database_identity(None)

    def test_empty_database_url_is_rejected(self):
        with self.assertRaisesRegex(DatabaseIdentityError, "DATABASE_URL is required"):
            parse_database_identity("  ")

    def test_non_postgresql_scheme_is_rejected(self):
        with self.assertRaisesRegex(DatabaseIdentityError, "PostgreSQL scheme"):
            parse_database_identity("mysql://fake_user:secret@example.test/fake_database")

    def test_missing_hostname_is_rejected(self):
        with self.assertRaisesRegex(DatabaseIdentityError, "database host"):
            parse_database_identity("postgresql:///fake_database")

    def test_missing_database_name_is_rejected(self):
        with self.assertRaisesRegex(DatabaseIdentityError, "database name"):
            parse_database_identity(
                "postgresql://fake_user:super-secret-password@"
                "ep-fake-branch.example.test:5432"
            )

    def test_missing_username_is_rejected(self):
        with self.assertRaisesRegex(DatabaseIdentityError, "database user"):
            parse_database_identity("postgresql://ep-fake-branch.example.test/fake_database")

    def test_invalid_url_is_rejected_without_secret(self):
        with self.assertRaises(DatabaseIdentityError) as context:
            parse_database_identity(
                "postgresql://fake_user:super-secret-password@"
                "ep-fake-branch.example.test:not-a-port/fake_database"
            )

        self.assertNotIn(SECRET, str(context.exception))

    def test_missing_expected_host_is_rejected(self):
        identity = parse_database_identity(VALID_URL)

        with self.assertRaisesRegex(DatabaseIdentityError, "DATABASE_EXPECTED_HOST"):
            validate_database_identity(
                identity,
                expected_host="",
                expected_name="fake_database",
                expected_user="fake_user",
            )

    def test_missing_expected_name_is_rejected(self):
        identity = parse_database_identity(VALID_URL)

        with self.assertRaisesRegex(DatabaseIdentityError, "DATABASE_EXPECTED_NAME"):
            validate_database_identity(
                identity,
                expected_host="ep-fake-branch.example.test",
                expected_name=None,
                expected_user="fake_user",
            )

    def test_missing_expected_user_is_rejected(self):
        identity = parse_database_identity(VALID_URL)

        with self.assertRaisesRegex(DatabaseIdentityError, "DATABASE_EXPECTED_USER"):
            validate_database_identity(
                identity,
                expected_host="ep-fake-branch.example.test",
                expected_name="fake_database",
                expected_user=" ",
            )

    def test_different_host_is_rejected(self):
        identity = parse_database_identity(VALID_URL)

        with self.assertRaisesRegex(DatabaseIdentityError, "database host does not match"):
            validate_database_identity(
                identity,
                expected_host="ep-other.example.test",
                expected_name="fake_database",
                expected_user="fake_user",
            )

    def test_different_database_name_is_rejected(self):
        identity = parse_database_identity(VALID_URL)

        with self.assertRaisesRegex(DatabaseIdentityError, "database name does not match"):
            validate_database_identity(
                identity,
                expected_host="ep-fake-branch.example.test",
                expected_name="other_database",
                expected_user="fake_user",
            )

    def test_different_user_is_rejected(self):
        identity = parse_database_identity(VALID_URL)

        with self.assertRaisesRegex(DatabaseIdentityError, "database user does not match"):
            validate_database_identity(
                identity,
                expected_host="ep-fake-branch.example.test",
                expected_name="fake_database",
                expected_user="other_user",
            )

    def test_complete_match_is_accepted(self):
        identity = parse_database_identity(VALID_URL)

        validate_database_identity(
            identity,
            expected_host="ep-fake-branch.example.test",
            expected_name="fake_database",
            expected_user="fake_user",
        )

    def test_script_returns_zero_for_matching_identity(self):
        lines = []
        exit_code = run_identity_check(
            {
                "DATABASE_URL": VALID_URL,
                "DATABASE_EXPECTED_HOST": "ep-fake-branch.example.test",
                "DATABASE_EXPECTED_NAME": "fake_database",
                "DATABASE_EXPECTED_USER": "fake_user",
            },
            output=lines.append,
        )

        output = "\n".join(lines)
        self.assertEqual(exit_code, 0)
        self.assertIn("Database identity check: OK", output)
        self.assertIn("Scheme: postgresql", output)
        self.assertIn("Host: ep-fake-branch.example.test", output)
        self.assertIn("Port: 5432", output)
        self.assertIn("Database: fake_database", output)
        self.assertIn("User: fake_user", output)
        self.assertNotIn(SECRET, output)
        self.assertNotIn(FULL_URL_WITH_SECRET, output)
        self.assertNotIn("sslmode", output)

    def test_script_returns_nonzero_for_mismatch(self):
        lines = []
        exit_code = run_identity_check(
            {
                "DATABASE_URL": (
                    "postgresql://fake_user:super-secret-password@"
                    "ep-wrong.example.test:5432/fake_database?sslmode=require"
                ),
                "DATABASE_EXPECTED_HOST": "ep-fake-branch.example.test",
                "DATABASE_EXPECTED_NAME": "fake_database",
                "DATABASE_EXPECTED_USER": "fake_user",
            },
            output=lines.append,
        )

        output = "\n".join(lines)
        self.assertNotEqual(exit_code, 0)
        self.assertIn("Database identity check: FAILED", output)
        self.assertIn("database host does not match DATABASE_EXPECTED_HOST", output)
        self.assertNotIn(SECRET, output)
        self.assertNotIn("postgresql://fake_user", output)
        self.assertNotIn("sslmode", output)


if __name__ == "__main__":
    unittest.main()
