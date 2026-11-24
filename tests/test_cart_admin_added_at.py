import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from api.admin import CartAdminView


class CartAdminAddedAtTest(unittest.TestCase):
    def setUp(self):
        self.formatter = CartAdminView.column_formatters["added_at"]

    def format(self, value):
        return self.formatter(None, None, SimpleNamespace(added_at=value), "added_at")

    def test_winter_naive_utc(self):
        self.assertEqual(self.format(datetime(2026, 1, 10, 12, 30)), "10/01/2026 13:30")

    def test_summer_naive_utc(self):
        self.assertEqual(self.format(datetime(2026, 7, 10, 12, 30)), "10/07/2026 14:30")

    def test_aware_value_respects_its_source_timezone(self):
        source = datetime(2026, 7, 10, 14, 30, tzinfo=timezone(timedelta(hours=2)))
        self.assertEqual(self.format(source), "10/07/2026 14:30")

    def test_daylight_saving_transitions_and_missing_value(self):
        self.assertEqual(self.format(datetime(2026, 3, 29, 0, 30)), "29/03/2026 01:30")
        self.assertEqual(self.format(datetime(2026, 3, 29, 1, 30)), "29/03/2026 03:30")
        self.assertEqual(self.format(None), "")


if __name__ == "__main__":
    unittest.main()
