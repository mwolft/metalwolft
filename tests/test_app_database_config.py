import ast
import os
import unittest
from contextlib import contextmanager
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
APP_PATH = ROOT_DIR / "src" / "app.py"

LOCAL_SQLITE_DATABASE_URI = "sqlite:////tmp/test.db"
HELPER_NAMES = {
    "BOOLEAN_FALSE_VALUES",
    "BOOLEAN_TRUE_VALUES",
    "LOCAL_SQLITE_DATABASE_URI",
    "PRODUCTION_APP_ENV",
    "VALID_APP_ENVIRONMENTS",
    "parse_boolean_env",
    "resolve_app_environment",
    "resolve_database_uri",
    "should_force_https",
}
CONTROLLED_ENV_KEYS = (
    "APP_ENV",
    "DATABASE_URL",
    "FLASK_ENV",
    "FORCE_HTTPS",
    "FLASK_DEBUG",
    "DEBUG",
    "CODESPACES",
    "GITPOD_WORKSPACE_URL",
)


@contextmanager
def controlled_environment(**values):
    original = {key: os.environ.get(key) for key in CONTROLLED_ENV_KEYS}
    try:
        for key in CONTROLLED_ENV_KEYS:
            os.environ.pop(key, None)
        for key, value in values.items():
            if value is not None:
                os.environ[key] = value
        yield
    finally:
        for key in CONTROLLED_ENV_KEYS:
            os.environ.pop(key, None)
            if original[key] is not None:
                os.environ[key] = original[key]


def load_database_config_helpers():
    source_tree = ast.parse(APP_PATH.read_text(encoding="utf-8"), filename=str(APP_PATH))
    selected_nodes = []

    for node in source_tree.body:
        if isinstance(node, ast.Assign):
            assigned_names = {
                target.id for target in node.targets if isinstance(target, ast.Name)
            }
            if assigned_names & HELPER_NAMES:
                selected_nodes.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name in HELPER_NAMES:
            selected_nodes.append(node)

    helper_tree = ast.Module(body=selected_nodes, type_ignores=[])
    ast.fix_missing_locations(helper_tree)

    namespace = {"os": os}
    exec(compile(helper_tree, str(APP_PATH), "exec"), namespace)
    return namespace


class AppDatabaseConfigTest(unittest.TestCase):
    def test_missing_app_env_fails(self):
        helpers = load_database_config_helpers()

        with controlled_environment(FORCE_HTTPS="0"):
            with self.assertRaisesRegex(RuntimeError, "APP_ENV is required"):
                helpers["resolve_database_uri"]()

    def test_empty_app_env_fails(self):
        helpers = load_database_config_helpers()

        with controlled_environment(APP_ENV="", FORCE_HTTPS="0"):
            with self.assertRaisesRegex(RuntimeError, "APP_ENV is required"):
                helpers["resolve_database_uri"]()

    def test_invalid_app_env_fails(self):
        helpers = load_database_config_helpers()

        with controlled_environment(APP_ENV="staging", FORCE_HTTPS="0"):
            with self.assertRaisesRegex(RuntimeError, "Invalid APP_ENV"):
                helpers["resolve_database_uri"]()

    def test_production_without_database_url_fails_before_sqlite_fallback(self):
        helpers = load_database_config_helpers()

        with controlled_environment(
            APP_ENV="production",
            FLASK_ENV="development",
            FORCE_HTTPS="0",
        ):
            with self.assertRaisesRegex(RuntimeError, "DATABASE_URL is required"):
                helpers["resolve_database_uri"]()

    def test_development_without_database_url_keeps_sqlite_fallback(self):
        helpers = load_database_config_helpers()

        with controlled_environment(
            APP_ENV="development",
            FLASK_ENV="development",
            FORCE_HTTPS="0",
        ):
            database_uri = helpers["resolve_database_uri"]()

        self.assertEqual(database_uri, LOCAL_SQLITE_DATABASE_URI)

    def test_test_environment_without_database_url_keeps_sqlite_fallback(self):
        helpers = load_database_config_helpers()

        with controlled_environment(
            APP_ENV="test",
            FLASK_ENV="development",
            FORCE_HTTPS="0",
        ):
            database_uri = helpers["resolve_database_uri"]()

        self.assertEqual(database_uri, LOCAL_SQLITE_DATABASE_URI)

    def test_production_with_database_url_keeps_postgres_url_normalization(self):
        helpers = load_database_config_helpers()

        with controlled_environment(
            APP_ENV="production",
            DATABASE_URL="postgres://user:pass@example.invalid:5432/metalwolft",
            FLASK_ENV="development",
            FORCE_HTTPS="0",
        ):
            database_uri = helpers["resolve_database_uri"]()

        self.assertEqual(
            database_uri,
            "postgresql://user:pass@example.invalid:5432/metalwolft",
        )

    def test_development_with_database_url_uses_configured_url(self):
        helpers = load_database_config_helpers()

        with controlled_environment(
            APP_ENV="development",
            DATABASE_URL="postgresql://user:pass@example.invalid:5432/metalwolft_dev",
            FLASK_ENV="production",
            FORCE_HTTPS="0",
        ):
            database_uri = helpers["resolve_database_uri"]()

        self.assertEqual(
            database_uri,
            "postgresql://user:pass@example.invalid:5432/metalwolft_dev",
        )

    def test_app_env_has_priority_over_flask_env(self):
        helpers = load_database_config_helpers()

        with controlled_environment(
            APP_ENV="development",
            FLASK_ENV="production",
            FORCE_HTTPS="0",
        ):
            database_uri = helpers["resolve_database_uri"]()

        self.assertEqual(database_uri, LOCAL_SQLITE_DATABASE_URI)

    def test_flask_env_is_not_environment_authority(self):
        helpers = load_database_config_helpers()

        with controlled_environment(
            FLASK_ENV="development",
            FORCE_HTTPS="0",
        ):
            with self.assertRaisesRegex(RuntimeError, "APP_ENV is required"):
                helpers["resolve_database_uri"]()

    def test_force_https_is_enabled_by_default_in_production(self):
        helpers = load_database_config_helpers()
        helpers["env"] = "production"

        with controlled_environment(APP_ENV="production"):
            self.assertTrue(helpers["should_force_https"]())

    def test_force_https_is_disabled_by_default_in_development(self):
        helpers = load_database_config_helpers()
        helpers["env"] = "development"

        with controlled_environment(APP_ENV="development"):
            self.assertFalse(helpers["should_force_https"]())

    def test_force_https_is_disabled_by_default_in_tests(self):
        helpers = load_database_config_helpers()
        helpers["env"] = "test"

        with controlled_environment(APP_ENV="test"):
            self.assertFalse(helpers["should_force_https"]())

    def test_force_https_explicit_override_has_priority(self):
        helpers = load_database_config_helpers()
        helpers["env"] = "development"

        with controlled_environment(APP_ENV="development", FORCE_HTTPS="1"):
            self.assertTrue(helpers["should_force_https"]())

        helpers["env"] = "production"
        with controlled_environment(APP_ENV="production", FORCE_HTTPS="0"):
            self.assertFalse(helpers["should_force_https"]())


if __name__ == "__main__":
    unittest.main()
