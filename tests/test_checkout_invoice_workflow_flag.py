import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def app_source():
    return (ROOT_DIR / "src/app.py").read_text(encoding="utf-8")


def env_example_source():
    return (ROOT_DIR / ".env.example").read_text(encoding="utf-8")


class CheckoutInvoiceWorkflowFlagTest(unittest.TestCase):
    def test_env_example_documents_disabled_checkout_invoice_workflow_flag(self):
        source = env_example_source()

        self.assertIn("ENABLE_INVOICE_WORKFLOW_AFTER_CHECKOUT=false", source)

    def test_flask_config_exposes_flag_disabled_by_default(self):
        source = app_source()

        self.assertIn("def parse_boolean_env(", source)
        self.assertIn('"ENABLE_INVOICE_WORKFLOW_AFTER_CHECKOUT"', source)
        self.assertIn('app.config["ENABLE_INVOICE_WORKFLOW_AFTER_CHECKOUT"] = parse_boolean_env(', source)
        self.assertIn("default=False", source)

    def test_boolean_parser_accepts_safe_true_and_false_values(self):
        source = app_source()

        self.assertIn('BOOLEAN_TRUE_VALUES = {"1", "true", "t", "yes", "on"}', source)
        self.assertIn('BOOLEAN_FALSE_VALUES = {"0", "false", "f", "no", "off"}', source)
        self.assertIn("Invalid boolean value for %s=%r. Falling back to %s.", source)

    def test_checkout_still_does_not_run_invoice_workflow_automatically(self):
        source = (ROOT_DIR / "tests/test_checkout_invoice_workflow_characterization.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("test_checkout_payment_paths_are_protected_against_accidental_document_workflow", source)


if __name__ == "__main__":
    unittest.main()
