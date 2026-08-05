import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MIGRATION_PATH = (
    ROOT_DIR
    / "src/migrations/versions/f8a9b0c1d2e3_add_screw_configuration_to_order_lines.py"
)
MODELS_PATH = ROOT_DIR / "src/api/models.py"
UTILS_PATH = ROOT_DIR / "src/api/utils.py"


class ScrewConfigurationModelTest(unittest.TestCase):
    def test_cart_and_order_lines_freeze_screw_configuration(self):
        source = MODELS_PATH.read_text(encoding="utf-8")

        self.assertEqual(
            source.count('screw_option = db.Column(db.String(20), nullable=False, default="standard")'),
            2,
        )
        self.assertEqual(
            source.count("screw_length_mm = db.Column(db.Integer, nullable=True)"),
            2,
        )
        self.assertEqual(
            source.count("screw_supplement = db.Column(db.Float, nullable=False, default=0.0)"),
            2,
        )

    def test_authoritative_rules_cover_both_enabled_installations(self):
        source = UTILS_PATH.read_text(encoding="utf-8")

        self.assertIn('DEFAULT_CONFIGURATOR_SCREW_OPTION = "standard"', source)
        self.assertIn('SCREW_OPTION_LONG_150 = "long_150"', source)
        self.assertEqual(source.count('"length_mm": 150'), 2)
        self.assertEqual(source.count('"supplement": 8.95'), 2)

    def test_additive_migration_hangs_from_current_head_and_backfills_legacy_lines(self):
        source = MIGRATION_PATH.read_text(encoding="utf-8")

        self.assertIn('revision = "f8a9b0c1d2e3"', source)
        self.assertIn('down_revision = "e7f8a9b0c1d2"', source)
        self.assertIn('for table_name in ("cart", "order_details")', source)
        self.assertIn(".values(screw_length_mm=80)", source)
        self.assertIn(".values(screw_length_mm=70)", source)
        self.assertNotIn("drop_table", source)


if __name__ == "__main__":
    unittest.main()
