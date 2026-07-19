import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
APP_PATH = ROOT_DIR / "src/app.py"
ENV_EXAMPLE_PATH = ROOT_DIR / ".env.example"


class VeriFactuConfigSourceTest(unittest.TestCase):
    def test_app_config_declares_disabled_default_and_identity_fields(self):
        source = APP_PATH.read_text(encoding="utf-8")

        self.assertIn('app.config["VERIFACTU_ENABLED"] = parse_boolean_env("VERIFACTU_ENABLED", default=False)', source)
        for key in (
            "VERIFACTU_SYSTEM_NAME",
            "VERIFACTU_SYSTEM_VERSION",
            "VERIFACTU_SYSTEM_ID",
            "VERIFACTU_INSTALLATION_ID",
            "VERIFACTU_PRODUCER_NAME",
            "VERIFACTU_PRODUCER_TAX_ID",
        ):
            self.assertIn(f'app.config["{key}"] = os.getenv("{key}")', source)

    def test_env_example_documents_public_non_secret_verifactu_identity(self):
        source = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")

        self.assertIn("VERIFACTU_ENABLED=false", source)
        for key in (
            "VERIFACTU_SYSTEM_NAME=",
            "VERIFACTU_SYSTEM_VERSION=",
            "VERIFACTU_SYSTEM_ID=",
            "VERIFACTU_INSTALLATION_ID=",
            "VERIFACTU_PRODUCER_NAME=",
            "VERIFACTU_PRODUCER_TAX_ID=",
        ):
            self.assertIn(key, source)


if __name__ == "__main__":
    unittest.main()
