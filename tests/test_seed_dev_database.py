import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.seed_dev_database import (
    DEV_CATEGORY_SLUG,
    DEV_PRODUCT_SLUG,
    SeedSafetyError,
    seed_dev_database,
)


ROOT_DIR = Path(__file__).resolve().parents[1]


SAFE_ENV = {
    "DATABASE_URL": "postgres://gitpod:postgres@db:5432/example",
    "DEV_CUSTOMER_PASSWORD": "local-customer-password",
    "DEV_ADMIN_PASSWORD": "local-admin-password",
}


def fake_password_hasher(password):
    return f"hashed::{password}"


class FakeApp:
    def app_context(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class FakeModel:
    def __init__(self, **kwargs):
        self.id = None
        for key, value in kwargs.items():
            setattr(self, key, value)


class FakeUser(FakeModel):
    pass


class FakeCategory(FakeModel):
    pass


class FakeSubcategory(FakeModel):
    pass


class FakeProduct(FakeModel):
    pass


class FakeDeliveryEstimateConfig(FakeModel):
    pass


class FakeQuery:
    def __init__(self, rows):
        self.rows = list(rows)

    def filter_by(self, **filters):
        filtered = [
            row for row in self.rows
            if all(getattr(row, key, None) == value for key, value in filters.items())
        ]
        return FakeQuery(filtered)

    def first(self):
        return self.rows[0] if self.rows else None


class FakeSession:
    def __init__(self):
        self.store = {
            FakeCategory: [],
            FakeDeliveryEstimateConfig: [],
            FakeProduct: [],
            FakeSubcategory: [],
            FakeUser: [],
        }
        self.added = []
        self.commit_count = 0
        self.rollback_count = 0
        self._next_id = 1

    def query(self, model):
        return FakeQuery(self.store.setdefault(model, []))

    def add(self, obj):
        self.store.setdefault(type(obj), []).append(obj)
        self.added.append(obj)

    def flush(self):
        for rows in self.store.values():
            for row in rows:
                if getattr(row, "id", None) is None:
                    row.id = self._next_id
                    self._next_id += 1

    def commit(self):
        self.commit_count += 1

    def rollback(self):
        self.rollback_count += 1


class FakeDb:
    def __init__(self):
        self.session = FakeSession()


def make_models():
    return {
        "Categories": FakeCategory,
        "DeliveryEstimateConfig": FakeDeliveryEstimateConfig,
        "Products": FakeProduct,
        "Subcategories": FakeSubcategory,
        "Users": FakeUser,
    }


def make_loader(db):
    return lambda: (FakeApp(), db, make_models())


class SeedDevDatabaseTest(unittest.TestCase):
    def setUp(self):
        self.password_hasher_patch = patch(
            "scripts.seed_dev_database._hash_password",
            side_effect=fake_password_hasher,
        )
        self.password_hasher_patch.start()

    def tearDown(self):
        self.password_hasher_patch.stop()

    def test_rejects_neon_database(self):
        env = {"DATABASE_URL": "postgres://user:pass@ep-test.neon.tech/example"}
        with self.assertRaises(SeedSafetyError):
            seed_dev_database(environ=env, app_loader=make_loader(FakeDb()))

    def test_rejects_render_environment(self):
        env = dict(SAFE_ENV, RENDER="true")
        with self.assertRaises(SeedSafetyError):
            seed_dev_database(environ=env, app_loader=make_loader(FakeDb()))

    def test_rejects_database_other_than_example(self):
        env = {"DATABASE_URL": "postgres://gitpod:postgres@db:5432/metalwolft"}
        with self.assertRaises(SeedSafetyError):
            seed_dev_database(environ=env, app_loader=make_loader(FakeDb()))

    def test_dry_run_does_not_write(self):
        db = FakeDb()
        result = seed_dev_database(
            environ={"DATABASE_URL": SAFE_ENV["DATABASE_URL"]},
            app_loader=make_loader(db),
            output=lambda message: None,
        )

        self.assertFalse(result.executed)
        self.assertEqual(db.session.added, [])
        self.assertEqual(db.session.commit_count, 0)

    def test_confirm_requires_local_passwords(self):
        env = {"DATABASE_URL": SAFE_ENV["DATABASE_URL"]}
        with self.assertRaises(SeedSafetyError):
            seed_dev_database(
                confirm=True,
                environ=env,
                app_loader=make_loader(FakeDb()),
            )

    def test_creates_minimal_category(self):
        db = FakeDb()
        seed_dev_database(
            confirm=True,
            environ=SAFE_ENV,
            app_loader=make_loader(db),
            output=lambda message: None,
        )

        categories = db.session.store[FakeCategory]
        self.assertEqual(len(categories), 1)
        self.assertEqual(categories[0].slug, DEV_CATEGORY_SLUG)

    def test_creates_minimal_product(self):
        db = FakeDb()
        seed_dev_database(
            confirm=True,
            environ=SAFE_ENV,
            app_loader=make_loader(db),
            output=lambda message: None,
        )

        products = db.session.store[FakeProduct]
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].slug, DEV_PRODUCT_SLUG)
        self.assertEqual(products[0].categoria_id, db.session.store[FakeCategory][0].id)
        self.assertGreater(products[0].precio, 0)

    def test_creates_customer_user(self):
        db = FakeDb()
        seed_dev_database(
            confirm=True,
            environ=SAFE_ENV,
            app_loader=make_loader(db),
            output=lambda message: None,
        )

        customer = [
            user for user in db.session.store[FakeUser]
            if user.email == "dev.customer@metalwolft.local"
        ][0]
        self.assertFalse(customer.is_admin)
        self.assertNotEqual(customer.password, SAFE_ENV["DEV_CUSTOMER_PASSWORD"])

    def test_creates_admin_user(self):
        db = FakeDb()
        seed_dev_database(
            confirm=True,
            environ=SAFE_ENV,
            app_loader=make_loader(db),
            output=lambda message: None,
        )

        admin = [
            user for user in db.session.store[FakeUser]
            if user.email == "dev.admin@metalwolft.local"
        ][0]
        self.assertTrue(admin.is_admin)
        self.assertNotEqual(admin.password, SAFE_ENV["DEV_ADMIN_PASSWORD"])

    def test_creates_required_delivery_configuration(self):
        db = FakeDb()
        seed_dev_database(
            confirm=True,
            environ=SAFE_ENV,
            app_loader=make_loader(db),
            output=lambda message: None,
        )

        configs = db.session.store[FakeDeliveryEstimateConfig]
        self.assertEqual(len(configs), 1)
        self.assertTrue(configs[0].is_active)
        self.assertEqual(configs[0].delivery_days, 15)

    def test_second_run_does_not_duplicate_records(self):
        db = FakeDb()
        seed_dev_database(
            confirm=True,
            environ=SAFE_ENV,
            app_loader=make_loader(db),
            output=lambda message: None,
        )
        second = seed_dev_database(
            confirm=True,
            environ=SAFE_ENV,
            app_loader=make_loader(db),
            output=lambda message: None,
        )

        self.assertEqual(len(db.session.store[FakeCategory]), 1)
        self.assertEqual(len(db.session.store[FakeProduct]), 1)
        self.assertEqual(len(db.session.store[FakeUser]), 2)
        self.assertIn(f"product:{DEV_PRODUCT_SLUG}", second.reused)

    def test_seed_does_not_delete_existing_data(self):
        db = FakeDb()
        existing_category = FakeCategory(nombre="Otra categoria", slug="otra-categoria")
        existing_category.id = 99
        db.session.store[FakeCategory].append(existing_category)

        seed_dev_database(
            confirm=True,
            environ=SAFE_ENV,
            app_loader=make_loader(db),
            output=lambda message: None,
        )

        slugs = {category.slug for category in db.session.store[FakeCategory]}
        self.assertIn("otra-categoria", slugs)
        self.assertIn(DEV_CATEGORY_SLUG, slugs)

    def test_script_does_not_contain_real_credentials(self):
        source = (ROOT_DIR / "scripts/seed_dev_database.py").read_text(encoding="utf-8")

        self.assertNotIn("sk_live", source)
        self.assertNotIn("AKIA", source)
        self.assertNotIn("paypal.com/v1/oauth2/token", source)
        self.assertNotIn("sergio@", source.lower())

    def test_script_is_not_invoked_from_app_startup(self):
        source = (ROOT_DIR / "src/app.py").read_text(encoding="utf-8")

        self.assertNotIn("seed_dev_database", source)
        self.assertNotIn("seed_dev_database.py", source)

    def test_seed_data_matches_next_required_endpoints(self):
        db = FakeDb()
        seed_dev_database(
            confirm=True,
            environ=SAFE_ENV,
            app_loader=make_loader(db),
            output=lambda message: None,
        )

        category = db.session.store[FakeCategory][0]
        product = db.session.store[FakeProduct][0]
        self.assertEqual(category.slug, "rejas-para-ventanas")
        self.assertEqual(product.slug, "reja-fija-pittsburgh")
        self.assertEqual(product.categoria_id, category.id)
        self.assertTrue(product.nombre)
        self.assertTrue(product.descripcion)


if __name__ == "__main__":
    unittest.main()
