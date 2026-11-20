import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import design_v1_demo_import as importer


class DesignV1DemoImportSafetyTest(unittest.TestCase):
    def setUp(self):
        self.source = {
            "V1_READONLY_DATABASE_URL": "postgresql://design_reader:synthetic@ep-demo.neon.tech:5432/neondb",
            "V1_EXPECTED_HOST": "ep-demo.neon.tech",
            "V1_EXPECTED_PORT": "5432",
            "V1_EXPECTED_DATABASE": "neondb",
            "V1_EXPECTED_USER": "design_reader",
            "V1_SOURCE_CUSTOMER_EMAIL": "test@example.test",
        }

    def test_reference_selection_is_strict(self):
        self.assertEqual(importer.normalize_references([" dp-abc123abcd "]), ("DP-ABC123ABCD",))
        for values in ([], ["DP-ABC123ABCD", "dp-abc123abcd"], ["not-a-reference"]):
            with self.assertRaises(RuntimeError):
                importer.normalize_references(values)

    def test_source_requires_independent_reference_and_read_only_role(self):
        url, email = importer.source_configuration(self.source)
        self.assertEqual((url.host, url.database, url.username, email),
                         ("ep-demo.neon.tech", "neondb", "design_reader", "test@example.test"))
        for change in (
            {"V1_EXPECTED_HOST": "other.neon.tech"},
            {"V1_EXPECTED_USER": "other_reader"},
            {"V1_READONLY_DATABASE_URL": self.source["V1_READONLY_DATABASE_URL"].replace("design_reader", "neondb_owner")},
            {"V1_READONLY_DATABASE_URL": self.source["V1_READONLY_DATABASE_URL"].replace("ep-demo.neon.tech", "db")},
        ):
            with self.assertRaises(RuntimeError):
                importer.source_configuration({**self.source, **change})
        with self.assertRaises(RuntimeError):
            importer.source_configuration({key: value for key, value in self.source.items() if key != "V1_EXPECTED_HOST"})

    def test_result_requires_matching_private_local_copy(self):
        content = b"%PDF-1.4 synthetic\n"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "result.pdf"
            path.write_bytes(content)
            row = {
                "status": "delivered", "result_storage_key": "design-results/demo.pdf",
                "result_filename": "result.pdf", "result_mime": "application/pdf",
                "result_size": len(content), "result_sha256": hashlib.sha256(content).hexdigest(),
            }
            importer.validate_legacy_result(row, path)
            with self.assertRaises(RuntimeError):
                importer.validate_legacy_result(row, None)
            with self.assertRaises(RuntimeError):
                importer.validate_legacy_result({**row, "result_sha256": "0" * 64}, path)
            files = importer.resolve_input_files(("DP-ABC123ABCD",), ["DP-ABC123ABCD=result.pdf"], root)
            self.assertEqual(files["DP-ABC123ABCD"], path)
            with self.assertRaises(RuntimeError):
                importer.resolve_input_files(("DP-ABC123ABCD",), ["DP-ABC123ABCD=../outside.pdf"], root)

    def test_source_role_must_have_no_write_privileges(self):
        class Cursor:
            def __init__(self, responses):
                self.responses = iter(responses)

            def execute(self, *_args):
                pass

            def fetchone(self):
                return next(self.responses)

        url, _ = importer.source_configuration(self.source)
        allowed = [
            ("neondb", "design_reader", "on"),
            (False, False, False, False, False),
            (False,), (False,), (False,), (False,),
            *((True,) for _ in importer.REQUIRED_TABLES),
        ]
        importer._assert_read_only(Cursor(allowed), url)
        for index in range(1, 6):
            denied = list(allowed)
            denied[index] = (True,) if index > 1 else (True, False, False, False, False)
            with self.subTest(check=index), self.assertRaises(RuntimeError):
                importer._assert_read_only(Cursor(denied), url)

    def test_incomplete_or_unpaid_request_is_rejected(self):
        row = {
            "reference": "DP-ABC123ABCD", "status": "pending", "paid_at": None,
            "currency": "EUR", "item_count": 1,
            **{field: None for field in importer.RESULT_FIELDS},
        }
        item = {
            "reference": "DP-ABC123ABCD", "line_type": "design_service",
            "product_name": "Synthetic", "product_slug": "synthetic",
            "category_slug": "rejas", "width_cm": 80, "height_cm": 95,
            "quantity": 1,
        }
        with self.assertRaises(RuntimeError):
            importer.validate_source_rows([row], [item], {})
        row["paid_at"] = "synthetic-paid-date"
        self.assertEqual(importer.validate_source_rows([row], [item], {}), {"DP-ABC123ABCD": [item]})

    def test_import_preserves_legacy_result_and_is_idempotent(self):
        from datetime import datetime
        from flask import Flask
        from api.models import db, Users, DesignRequest, DesignRequestItem
        from scripts import design_v2_demo

        with tempfile.TemporaryDirectory() as directory:
            app = Flask(__name__)
            app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", SQLALCHEMY_TRACK_MODIFICATIONS=False)
            db.init_app(app)
            with app.app_context():
                db.create_all()
                db.session.add(Users(email="demo@example.test", firstname="Demo", lastname="Customer", password="synthetic"))
                db.session.commit()
            content = b"%PDF-1.4 synthetic\n"
            result = Path(directory) / "legacy.pdf"
            result.write_bytes(content)
            now = datetime(2026, 1, 2, 3, 4)
            request = {
                "reference": "DP-ABC123ABCD", "status": "delivered", "requested_at": now,
                "paid_at": now, "started_at": now, "delivered_at": now, "cancelled_at": None,
                "subtotal_gross": 24.95, "price_gross": 24.95, "discount_amount": 0,
                "currency": "EUR", "lead_time_hours": 24, "order_date": now,
                "total_amount": 24.95, "order_status": "pendiente", "item_count": 1,
                "result_storage_key": "design-results/synthetic/legacy.pdf",
                "result_filename": "legacy.pdf", "result_mime": "application/pdf",
                "result_size": len(content), "result_sha256": hashlib.sha256(content).hexdigest(),
            }
            item = {
                "reference": request["reference"], "product_name": "Reja historica",
                "width_cm": 80, "height_cm": 95, "quantity": 1,
                "line_type": "design_service", "alto": 95, "ancho": 80, "precio_total": 24.95,
                "product_slug": "reja-demo", "current_product_name": "Reja actual",
                "current_price": 180, "current_discounted_price": None,
                "published": True, "available_for_sale": True, "opening_type": "fixed",
                "category_slug": "rejas-para-ventanas", "category_name": "Rejas",
            }
            with patch.object(design_v2_demo, "STATE_DIR", Path(directory)):
                storage = design_v2_demo.LocalDemoStorage()
                args = (app, db, {"customer_email": "demo@example.test"}, [request], [item],
                        {request["reference"]: result}, storage)
                self.assertEqual(importer.import_into_demo(*args), 1)
                self.assertEqual(importer.import_into_demo(*args), 0)
                with app.app_context():
                    stored = DesignRequest.query.filter_by(reference=request["reference"]).one()
                    self.assertEqual((stored.user.email, stored.status, stored.delivered_at),
                                     ("demo@example.test", "delivered", now))
                    self.assertEqual(DesignRequestItem.query.filter_by(design_request_id=stored.id).count(), 1)
                    self.assertEqual(storage.get_object(storage_key=request["result_storage_key"]), content)


if __name__ == "__main__":
    unittest.main()
