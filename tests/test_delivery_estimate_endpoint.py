import importlib.util
import sys
import unittest
from pathlib import Path


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
    for package in (
        "flask",
        "flask_jwt_extended",
        "flask_sqlalchemy",
        "sqlalchemy",
        "slugify",
    )
)


if HAS_ENDPOINT_DEPS:
    from flask import Flask

    from api.models import DeliveryEstimateConfig, db
    from api.routes import api


@unittest.skipUnless(
    HAS_ENDPOINT_DEPS,
    "Flask/SQLAlchemy test dependencies are not installed.",
)
class DeliveryEstimateEndpointTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        db.init_app(self.app)
        self.app.register_blueprint(api, url_prefix="/api")

        with self.app.app_context():
            DeliveryEstimateConfig.__table__.create(db.engine)

        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            DeliveryEstimateConfig.__table__.drop(db.engine, checkfirst=True)

    def test_active_configuration_preserves_public_contract(self):
        with self.app.app_context():
            db.session.add(
                DeliveryEstimateConfig(
                    delivery_days=15,
                    range_days=7,
                    is_active=True,
                )
            )
            db.session.commit()

        response = self.client.get("/api/delivery-estimate")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(set(payload), {"start_date", "end_date", "is_active"})
        self.assertTrue(payload["is_active"])
        self.assertRegex(payload["start_date"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertRegex(payload["end_date"], r"^\d{4}-\d{2}-\d{2}$")

    def test_missing_active_configuration_preserves_404_contract(self):
        response = self.client.get("/api/delivery-estimate")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), {"is_active": False})

    def test_internal_error_does_not_expose_details(self):
        with self.app.app_context():
            DeliveryEstimateConfig.__table__.drop(db.engine)

        with self.assertLogs(self.app.logger.name, level="ERROR") as captured_logs:
            response = self.client.get("/api/delivery-estimate")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.get_json(), {"message": "Error al obtener la estimación"})
        response_text = response.get_data(as_text=True)
        self.assertNotIn("OperationalError", response_text)
        self.assertNotIn("delivery_estimate_config", response_text)
        self.assertTrue(
            any("error_type=OperationalError" in message for message in captured_logs.output)
        )


if __name__ == "__main__":
    unittest.main()
