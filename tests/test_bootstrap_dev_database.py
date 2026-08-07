import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.bootstrap_dev_database import (
    BootstrapExecutionError,
    BootstrapSafetyError,
    bootstrap_dev_database,
    validate_database_url,
)


SAFE_ENV = {
    "DATABASE_URL": "postgres://gitpod:postgres@db:5432/example",
    "FLASK_ENV": "development",
}


class FakeAppContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class FakeApp:
    def app_context(self):
        return FakeAppContext()


class FakeDb:
    def __init__(self, calls):
        self.calls = calls
        self.engine = object()

    def create_all(self):
        self.calls.append("create_all")


def fake_loader(calls):
    def load():
        return FakeApp(), FakeDb(calls)

    return load


class BootstrapDevDatabaseTest(unittest.TestCase):
    def test_rejects_neon_database_url(self):
        with self.assertRaises(BootstrapSafetyError):
            validate_database_url(
                "postgresql://user:secret@ep-test.eu-central-1.aws.neon.tech/example",
                {"FLASK_ENV": "development"},
            )

    def test_rejects_external_or_render_like_host(self):
        with self.assertRaises(BootstrapSafetyError):
            validate_database_url(
                "postgresql://user:secret@metalwolft-db.render.com/example",
                {"FLASK_ENV": "development"},
            )

    def test_rejects_database_name_other_than_example(self):
        with self.assertRaises(BootstrapSafetyError):
            validate_database_url(
                "postgresql://gitpod:postgres@db:5432/production",
                {"FLASK_ENV": "development"},
            )

    def test_rejects_production_environment_marker(self):
        with self.assertRaises(BootstrapSafetyError):
            validate_database_url(
                SAFE_ENV["DATABASE_URL"],
                {"FLASK_ENV": "development", "RENDER_SERVICE_ID": "srv-prod"},
            )

    def test_rejects_base_with_existing_tables(self):
        with self.assertRaises(BootstrapSafetyError):
            bootstrap_dev_database(
                confirm=True,
                environ=SAFE_ENV,
                app_loader=fake_loader([]),
                table_inspector=lambda _db: ("orders",),
                alembic_stamper=lambda: None,
                output=lambda _message: None,
            )

    def test_dry_run_does_not_write(self):
        calls = []
        output = []

        result = bootstrap_dev_database(
            confirm=False,
            environ=SAFE_ENV,
            app_loader=fake_loader(calls),
            table_inspector=lambda _db: (),
            alembic_stamper=lambda: calls.append("stamp_head"),
            output=output.append,
        )

        self.assertFalse(result.executed)
        self.assertFalse(result.confirmed)
        self.assertEqual(calls, [])
        self.assertIn("DRY RUN", output[0])

    def test_confirmation_is_required_for_create_all_and_stamp(self):
        calls = []

        result = bootstrap_dev_database(
            confirm=False,
            environ=SAFE_ENV,
            app_loader=fake_loader(calls),
            table_inspector=lambda _db: (),
            alembic_stamper=lambda: calls.append("stamp_head"),
            output=lambda _message: None,
        )

        self.assertFalse(result.confirmed)
        self.assertFalse(result.executed)
        self.assertEqual(calls, [])

    def test_confirm_calls_create_all_and_stamps_head_afterwards(self):
        calls = []

        result = bootstrap_dev_database(
            confirm=True,
            environ=SAFE_ENV,
            app_loader=fake_loader(calls),
            table_inspector=lambda _db: (),
            alembic_stamper=lambda: calls.append("stamp_head"),
            output=lambda _message: None,
        )

        self.assertTrue(result.executed)
        self.assertEqual(calls, ["create_all", "stamp_head"])

    def test_partial_failure_is_controlled(self):
        calls = []

        def fail_stamp():
            calls.append("stamp_head")
            raise RuntimeError("alembic detail")

        with self.assertRaises(BootstrapExecutionError) as context:
            bootstrap_dev_database(
                confirm=True,
                environ=SAFE_ENV,
                app_loader=fake_loader(calls),
                table_inspector=lambda _db: (),
                alembic_stamper=fail_stamp,
                output=lambda _message: None,
            )

        self.assertEqual(calls, ["create_all", "stamp_head"])
        self.assertNotIn("alembic detail", str(context.exception))

    def test_safe_output_does_not_include_credentials(self):
        output = []

        bootstrap_dev_database(
            confirm=False,
            environ=SAFE_ENV,
            app_loader=fake_loader([]),
            table_inspector=lambda _db: (),
            alembic_stamper=lambda: None,
            output=output.append,
        )

        self.assertIn("postgresql://db:5432/example", output[0])
        self.assertNotIn("gitpod", output[0])
        self.assertNotIn("postgres@", output[0])

    def test_script_does_not_contain_hardcoded_credentials(self):
        source = (ROOT_DIR / "scripts/bootstrap_dev_database.py").read_text(encoding="utf-8")

        self.assertNotIn("gitpod:postgres", source)
        self.assertNotIn("neon.tech/", source)

    def test_bootstrap_is_not_invoked_from_app_startup(self):
        source = (ROOT_DIR / "src/app.py").read_text(encoding="utf-8")

        self.assertNotIn("bootstrap_dev_database", source)
        self.assertNotIn("bootstrap_dev_database.py", source)


if __name__ == "__main__":
    unittest.main()
