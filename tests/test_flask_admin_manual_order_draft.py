import ast
import base64
import importlib.util
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
ADMIN_PATH = SRC_DIR / "api" / "admin.py"
TEMPLATE_DIR = SRC_DIR / "templates" / "admin"
STATIC_DIR = SRC_DIR / "static" / "admin"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def source(path):
    return path.read_text(encoding="utf-8")


def module_ast():
    return ast.parse(source(ADMIN_PATH))


def class_node(class_name):
    for node in module_ast().body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return node
    raise AssertionError(f"{class_name} not found")


def class_source(class_name):
    return ast.get_source_segment(source(ADMIN_PATH), class_node(class_name))


def method_source(class_name, method_name):
    text = source(ADMIN_PATH)
    for statement in class_node(class_name).body:
        if isinstance(statement, ast.FunctionDef) and statement.name == method_name:
            return ast.get_source_segment(text, statement)
    raise AssertionError(f"{method_name} not found in {class_name}")


def class_assignment_value(class_name, assignment_name):
    for statement in class_node(class_name).body:
        if not isinstance(statement, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == assignment_name for target in statement.targets):
            return ast.literal_eval(statement.value)
    raise AssertionError(f"{assignment_name} not found in {class_name}")


HAS_ADMIN_DEPS = all(
    importlib.util.find_spec(package) is not None
    for package in ("flask", "flask_admin", "flask_sqlalchemy", "sqlalchemy", "slugify")
)


class FlaskAdminManualOrderDraftContractTest(unittest.TestCase):
    def setUp(self):
        self.view_source = class_source("ManualOrderDraftAdminView")

    def test_registers_manual_orders_under_sales_without_a_new_endpoint(self):
        admin_source = source(ADMIN_PATH)

        self.assertIn(
            'ManualOrderDraftAdminView(ManualOrderDraft, db.session, name="Pedidos manuales", category="Ventas")',
            admin_source,
        )
        self.assertNotIn("endpoint=\"manualorderdraft\"", admin_source)

    def test_view_uses_custom_forms_and_never_exposes_raw_customer_json_or_derived_values(self):
        for forbidden_field in (
            "customer_draft = TextAreaField",
            "last_quote_snapshot =",
            "quote_fingerprint =",
            "issuance_key =",
            "issued_order_id =",
            "total_amount =",
            "discount_value =",
            "shipping_cost =",
        ):
            self.assertNotIn(forbidden_field, self.view_source)

        template = source(TEMPLATE_DIR / "manual_order_draft_edit.html")
        self.assertNotIn("customer_draft", template)
        self.assertNotIn("line_total[]", template)
        self.assertNotIn("unit_price[]", template)
        self.assertIn("name=\"line_product_id[]\"", template)
        self.assertIn("name=\"line_quantity[]\"", template)
        self.assertIn("name=\"line_alto[]\"", template)
        self.assertIn("name=\"line_ancho[]\"", template)

    def test_custom_routes_are_post_protected_for_each_mutation(self):
        review_source = method_source("ManualOrderDraftAdminView", "review_draft")
        issue_source = method_source("ManualOrderDraftAdminView", "confirm_issue")
        cancel_source = method_source("ManualOrderDraftAdminView", "cancel_draft")

        for method in (review_source, issue_source, cancel_source):
            self.assertIn("_valid_work_order_csrf_token", method)
            self.assertIn("request.form.get(\"csrf_token\")", method)

        self.assertIn('methods=["POST"]', self.view_source)
        self.assertIn('methods=["GET", "POST"]', self.view_source)

    def test_review_and_issue_delegate_to_the_canonical_services(self):
        review_source = method_source("ManualOrderDraftAdminView", "review_draft")
        issue_source = method_source("ManualOrderDraftAdminView", "confirm_issue")

        self.assertEqual(review_source.count("review_manual_order_draft("), 1)
        self.assertIn("db_session=self.session", review_source)
        self.assertEqual(issue_source.count("issue_manual_order_draft("), 1)
        self.assertIn("actor=invoice_admin_actor_from_basic_auth(request.authorization)", issue_source)
        self.assertNotIn("Orders(", issue_source)
        self.assertNotIn("CheckoutSessions(", issue_source)
        self.assertNotIn("build_checkout_quote(", review_source)
        self.assertNotIn("build_checkout_quote(", issue_source)

    def test_status_guards_are_server_side_and_cancel_preserves_the_audit_record(self):
        edit_source = method_source("ManualOrderDraftAdminView", "edit_view")
        cancel_source = method_source("ManualOrderDraftAdminView", "cancel_draft")

        self.assertIn("if not draft.is_editable:", edit_source)
        self.assertIn("if not draft.is_editable:", cancel_source)
        self.assertIn("ManualOrderDraft.STATUS_CANCELLED", cancel_source)
        self.assertNotIn("self.session.delete", cancel_source)
        self.assertNotIn("invalidate_manual_order_draft_review", cancel_source)

    def test_payment_only_changes_do_not_invalidate_the_current_review(self):
        save_source = method_source("ManualOrderDraftAdminView", "_save_manual_order_draft")

        self.assertIn("commercial_changed", save_source)
        self.assertIn("invalidate_manual_order_draft_review(draft)", save_source)
        for payment_field in (
            "payment_method",
            "payment_reference",
            "payment_confirmed_at",
            "payment_note",
            "internal_note",
        ):
            self.assertNotIn(f'or draft.{payment_field} !=', save_source)

    def test_external_script_is_csp_safe_and_handles_line_lifecycle(self):
        script = source(STATIC_DIR / "manual_order_draft.js")

        self.assertIn("addEventListener", script)
        self.assertIn("addLine", script)
        self.assertIn("moveLine", script)
        self.assertIn("line.remove", script)
        self.assertNotIn("onclick", script.lower())
        self.assertNotIn("javascript:", script.lower())


@unittest.skipUnless(HAS_ADMIN_DEPS, "Flask-Admin/SQLAlchemy test dependencies are not installed.")
class FlaskAdminManualOrderDraftIntegrationTest(unittest.TestCase):
    def setUp(self):
        from flask import Flask
        from flask_admin import Admin
        from sqlalchemy import text

        from api import admin as admin_module
        from api.models import Categories, ManualOrderDraft, Orders, Products, Users, db

        self.admin_module = admin_module
        self.ManualOrderDraft = ManualOrderDraft
        self.Orders = Orders
        self.Users = Users
        self.db = db
        admin_module.ADMIN_USER = "admin"
        admin_module.ADMIN_PW = "secret"

        self.app = Flask(__name__, template_folder=str(SRC_DIR / "templates"))
        self.app.config.update(
            SECRET_KEY="manual-order-draft-test-secret",
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        db.init_app(self.app)
        self.admin = Admin(self.app, url="/admin")
        self.orders_view = admin_module.OrderAdminView(Orders, db.session, name="Pedidos")
        self.view = admin_module.ManualOrderDraftAdminView(
            ManualOrderDraft,
            db.session,
            name="Pedidos manuales",
        )
        self.admin.add_view(self.orders_view)
        self.admin.add_view(self.view)

        with self.app.app_context():
            db.create_all()
            db.session.execute(text("PRAGMA foreign_keys=ON"))
            category = Categories(nombre="Rejas", descripcion="Tests", slug="rejas")
            self.user = Users(
                email="cliente@example.test",
                password="x",
                firstname="Perfil",
                lastname="Original",
                phone="611 111 111",
            )
            db.session.add_all([category, self.user])
            db.session.flush()
            self.product = Products(
                nombre="Reja fija Essex",
                descripcion="Modelo de pruebas",
                precio=100,
                categoria_id=category.id,
                slug="reja-fija-essex",
            )
            db.session.add(self.product)
            db.session.commit()
            self.user_id = self.user.id
            self.product_id = self.product.id

        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            self.db.session.remove()
            self.db.drop_all()

    @staticmethod
    def _auth_header():
        token = base64.b64encode(b"admin:secret").decode("ascii")
        return {"Authorization": f"Basic {token}"}

    def _rule(self, suffix):
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint == f"{self.view.endpoint}{suffix}":
                return rule
        raise AssertionError(f"No manual-order route ending in {suffix}")

    def _create_url(self):
        return self._rule(".create_view").rule

    def _edit_url(self, draft_id):
        return f"{self._rule('.edit_view').rule}?id={draft_id}"

    def _detail_url(self, draft_id):
        return f"{self._rule('.details_view').rule}?id={draft_id}"

    def _action_url(self, endpoint_suffix, draft_id):
        return self._rule(endpoint_suffix).rule.replace("<int:draft_id>", str(draft_id))

    @staticmethod
    def _csrf(response):
        match = re.search(rb'name="csrf_token" value="([^"]+)"', response.data)
        if not match:
            raise AssertionError("Expected CSRF token in response")
        return match.group(1).decode("ascii")

    def _payload(self, csrf_token, **overrides):
        payload = {
            "csrf_token": csrf_token,
            "customer_mode": "registered_user",
            "user_id": str(self.user_id),
            "user_email": "attacker@example.test",
            "firstname": "Ana",
            "lastname": "Cliente",
            "phone": "600 000 000",
            "legal_name": "Ana Cliente",
            "tax_id": "00000000T",
            "billing_address": "Calle Fiscal 1",
            "billing_postal_code": "13001",
            "billing_city": "Ciudad Real",
            "billing_province": "Ciudad Real",
            "billing_country_code": "ES",
            "shipping_same_as_billing": "y",
            "discount_code": "",
            "estimated_delivery_at": "2026-09-30",
            "estimated_delivery_note": "Entrega planificada",
            "payment_method": "bank_transfer",
            "payment_reference": "TRF-123",
            "payment_confirmed_at": "2026-09-10T10:00",
            "payment_note": "Extracto conciliado",
            "internal_note": "",
            "line_product_id[]": str(self.product_id),
            "line_quantity[]": "1",
            "line_alto[]": "118",
            "line_ancho[]": "122",
            "line_anclaje[]": "Sin obra: con agujeros interiores",
            "line_color[]": "satinado_blanco",
            "line_screw_option[]": "standard",
        }
        payload.update(overrides)
        return payload

    def _create_draft(self):
        create_page = self.client.get(self._create_url(), headers=self._auth_header())
        self.assertEqual(create_page.status_code, 200)
        response = self.client.post(
            self._create_url(),
            data=self._payload(self._csrf(create_page)),
            headers=self._auth_header(),
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            draft = self.ManualOrderDraft.query.one()
            return draft.id

    def test_view_requires_auth_and_lists_drafts(self):
        index_url = self._rule(".index_view").rule
        self.assertEqual(self.client.get(index_url).status_code, 401)
        self.assertEqual(self.client.get(self._create_url()).status_code, 401)

        response = self.client.get(index_url, headers=self._auth_header())
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"NUEVO PEDIDO MANUAL", response.data)

    def test_create_requires_user_and_csrf_then_forces_account_email_without_mutating_user(self):
        create_page = self.client.get(self._create_url(), headers=self._auth_header())
        self.assertEqual(create_page.status_code, 200)
        self.assertIn(b"/static/admin/manual_order_draft.js", create_page.data)
        self.assertIn(b"data-manual-order-shipping-same", create_page.data)
        self.assertNotIn(b"onclick=", create_page.data.lower())
        payload = self._payload(self._csrf(create_page), user_id="0")
        response = self.client.post(self._create_url(), data=payload, headers=self._auth_header())
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            self.assertEqual(self.ManualOrderDraft.query.count(), 0)

        response = self.client.post(
            self._create_url(),
            data=self._payload("invalid-token"),
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            self.assertEqual(self.ManualOrderDraft.query.count(), 0)

        draft_id = self._create_draft()
        with self.app.app_context():
            draft = self.db.session.get(self.ManualOrderDraft, draft_id)
            user = self.db.session.get(self.Users, self.user_id)
            self.assertEqual(draft.customer_draft["email"], "cliente@example.test")
            self.assertEqual(user.firstname, "Perfil")
            self.assertEqual(user.phone, "611 111 111")
            self.assertEqual(len(draft.lines), 1)

    def test_manual_customer_can_be_saved_reviewed_and_issued_without_an_account(self):
        create_page = self.client.get(self._create_url(), headers=self._auth_header())
        payload = self._payload(
            self._csrf(create_page),
            customer_mode="manual_customer",
            user_id="0",
            user_email="manual@example.test",
        )
        created = self.client.post(
            self._create_url(),
            data=payload,
            headers=self._auth_header(),
            follow_redirects=False,
        )
        self.assertEqual(created.status_code, 302)
        with self.app.app_context():
            draft = self.ManualOrderDraft.query.one()
            draft_id = draft.id
            self.assertEqual(draft.customer_mode, "manual_customer")
            self.assertIsNone(draft.user_id)
            self.assertEqual(draft.customer_draft["email"], "manual@example.test")
            self.assertEqual(self.Users.query.count(), 1)

        review_url = self._action_url(".review_draft", draft_id)
        review_page = self.client.get(self._edit_url(draft_id), headers=self._auth_header())
        reviewed = self.client.post(
            review_url,
            data={"csrf_token": self._csrf(review_page)},
            headers=self._auth_header(),
            follow_redirects=False,
        )
        self.assertEqual(reviewed.status_code, 302)

        issue_url = self._action_url(".confirm_issue", draft_id)
        confirm_page = self.client.get(issue_url, headers=self._auth_header())
        with patch("api.email_routes.send_email") as send_email:
            issued = self.client.post(
                issue_url,
                data={
                    "csrf_token": self._csrf(confirm_page),
                    "confirm_issue": "confirmed",
                },
                headers=self._auth_header(),
                follow_redirects=False,
            )
        send_email.assert_called_once()
        self.assertEqual(send_email.call_args.kwargs["recipients"][0], "manual@example.test")
        self.assertEqual(issued.status_code, 302)
        order_detail = self.client.get(
            issued.headers["Location"],
            headers=self._auth_header(),
        )
        self.assertEqual(order_detail.status_code, 200)
        self.assertIn(b"Ana Cliente", order_detail.data)
        self.assertIn(b"manual@example.test", order_detail.data)
        with self.app.app_context():
            draft = self.db.session.get(self.ManualOrderDraft, draft_id)
            order = self.db.session.get(self.Orders, draft.issued_order_id)
            self.assertIsNone(order.user_id)
            self.assertEqual(order.confirmed_order_context.source, "admin_external")
            self.assertEqual(
                order.confirmed_order_context.customer_snapshot["email"],
                "manual@example.test",
            )

    def test_review_invalidates_only_commercial_changes_and_issues_idempotently(self):
        draft_id = self._create_draft()
        edit_page = self.client.get(self._edit_url(draft_id), headers=self._auth_header())
        token = self._csrf(edit_page)

        review_url = self._action_url(".review_draft", draft_id)
        missing_token = self.client.post(review_url, data={}, headers=self._auth_header())
        self.assertEqual(missing_token.status_code, 302)
        with self.app.app_context():
            self.assertIsNone(self.db.session.get(self.ManualOrderDraft, draft_id).last_quote_snapshot)

        reviewed = self.client.post(
            review_url,
            data={"csrf_token": token},
            headers=self._auth_header(),
            follow_redirects=False,
        )
        self.assertEqual(reviewed.status_code, 302)
        with self.app.app_context():
            draft = self.db.session.get(self.ManualOrderDraft, draft_id)
            self.assertIsNotNone(draft.last_quote_snapshot)
            self.assertIsNotNone(draft.quote_fingerprint)

        edit_page = self.client.get(self._edit_url(draft_id), headers=self._auth_header())
        changed_payment = self.client.post(
            self._edit_url(draft_id),
            data=self._payload(self._csrf(edit_page), payment_reference="TRF-456"),
            headers=self._auth_header(),
            follow_redirects=False,
        )
        self.assertEqual(changed_payment.status_code, 302)
        with self.app.app_context():
            self.assertIsNotNone(self.db.session.get(self.ManualOrderDraft, draft_id).last_quote_snapshot)

        edit_page = self.client.get(self._edit_url(draft_id), headers=self._auth_header())
        changed_customer = self.client.post(
            self._edit_url(draft_id),
            data=self._payload(self._csrf(edit_page), firstname="Ana Revisada"),
            headers=self._auth_header(),
            follow_redirects=False,
        )
        self.assertEqual(changed_customer.status_code, 302)
        with self.app.app_context():
            self.assertIsNone(self.db.session.get(self.ManualOrderDraft, draft_id).last_quote_snapshot)

        edit_page = self.client.get(self._edit_url(draft_id), headers=self._auth_header())
        self.client.post(
            review_url,
            data={"csrf_token": self._csrf(edit_page)},
            headers=self._auth_header(),
        )
        with self.app.app_context():
            self.assertIsNotNone(self.db.session.get(self.ManualOrderDraft, draft_id).last_quote_snapshot)

        edit_page = self.client.get(self._edit_url(draft_id), headers=self._auth_header())
        changed_delivery = self.client.post(
            self._edit_url(draft_id),
            data=self._payload(self._csrf(edit_page), estimated_delivery_note="Nueva entrega planificada"),
            headers=self._auth_header(),
            follow_redirects=False,
        )
        self.assertEqual(changed_delivery.status_code, 302)
        with self.app.app_context():
            self.assertIsNone(self.db.session.get(self.ManualOrderDraft, draft_id).last_quote_snapshot)

        edit_page = self.client.get(self._edit_url(draft_id), headers=self._auth_header())
        changed_line = self.client.post(
            self._edit_url(draft_id),
            data=self._payload(self._csrf(edit_page), **{"line_quantity[]": "2"}),
            headers=self._auth_header(),
            follow_redirects=False,
        )
        self.assertEqual(changed_line.status_code, 302)
        with self.app.app_context():
            self.assertIsNone(self.db.session.get(self.ManualOrderDraft, draft_id).last_quote_snapshot)

        edit_page = self.client.get(self._edit_url(draft_id), headers=self._auth_header())
        token = self._csrf(edit_page)
        self.client.post(review_url, data={"csrf_token": token}, headers=self._auth_header())
        issue_url = self._action_url(".confirm_issue", draft_id)
        missing_token = self.client.post(issue_url, data={"confirm_issue": "confirmed"}, headers=self._auth_header())
        self.assertEqual(missing_token.status_code, 302)
        with self.app.app_context():
            self.assertEqual(self.Orders.query.count(), 0)

        confirm_page = self.client.get(issue_url, headers=self._auth_header())
        token = self._csrf(confirm_page)
        with patch("api.email_routes.send_email") as send_email:
            issued = self.client.post(
                issue_url,
                data={"csrf_token": token, "confirm_issue": "confirmed"},
                headers=self._auth_header(),
                follow_redirects=False,
            )
        send_email.assert_called_once()
        self.assertEqual(send_email.call_args.kwargs["recipients"][0], "cliente@example.test")
        self.assertEqual(issued.status_code, 302)
        self.assertIn(b"/admin/orders/details/", issued.headers["Location"].encode("utf-8"))
        with self.app.app_context():
            draft = self.db.session.get(self.ManualOrderDraft, draft_id)
            self.assertEqual(draft.status, self.ManualOrderDraft.STATUS_ISSUED)
            self.assertEqual(self.Orders.query.count(), 1)
            order_id = draft.issued_order_id

        retry = self.client.post(
            issue_url,
            data={"csrf_token": token, "confirm_issue": "confirmed"},
            headers=self._auth_header(),
            follow_redirects=False,
        )
        self.assertEqual(retry.status_code, 302)
        send_email.assert_called_once()
        with self.app.app_context():
            self.assertEqual(self.Orders.query.count(), 1)
            self.assertEqual(self.db.session.get(self.ManualOrderDraft, draft_id).issued_order_id, order_id)

    def test_email_failure_after_commit_does_not_revert_manual_order(self):
        draft_id = self._create_draft()
        review_page = self.client.get(self._edit_url(draft_id), headers=self._auth_header())
        self.client.post(
            self._action_url(".review_draft", draft_id),
            data={"csrf_token": self._csrf(review_page)},
            headers=self._auth_header(),
            follow_redirects=False,
        )
        issue_url = self._action_url(".confirm_issue", draft_id)
        confirm_page = self.client.get(issue_url, headers=self._auth_header())

        with patch(
            "api.admin.send_order_confirmation_email",
            side_effect=RuntimeError("smtp unavailable"),
        ) as send_email:
            issued = self.client.post(
                issue_url,
                data={"csrf_token": self._csrf(confirm_page), "confirm_issue": "confirmed"},
                headers=self._auth_header(),
                follow_redirects=False,
            )

        self.assertEqual(issued.status_code, 302)
        send_email.assert_called_once()
        with self.app.app_context():
            draft = self.db.session.get(self.ManualOrderDraft, draft_id)
            self.assertEqual(draft.status, self.ManualOrderDraft.STATUS_ISSUED)
            self.assertEqual(self.Orders.query.count(), 1)

        issued_edit = self.client.get(
            self._edit_url(draft_id),
            headers=self._auth_header(),
            follow_redirects=False,
        )
        self.assertEqual(issued_edit.status_code, 302)
        self.assertIn(b"/admin/orders/details/", issued_edit.headers["Location"].encode("utf-8"))

        issued_cancel = self.client.post(
            self._action_url(".cancel_draft", draft_id),
            data={"confirm_cancel": "cancelled"},
            headers=self._auth_header(),
            follow_redirects=False,
        )
        self.assertEqual(issued_cancel.status_code, 302)
        with self.app.app_context():
            self.assertEqual(self.db.session.get(self.ManualOrderDraft, draft_id).status, self.ManualOrderDraft.STATUS_ISSUED)

    def test_cancel_requires_csrf_preserves_data_and_blocks_later_editing(self):
        draft_id = self._create_draft()
        cancel_url = self._action_url(".cancel_draft", draft_id)
        missing_token = self.client.post(
            cancel_url,
            data={"confirm_cancel": "cancelled"},
            headers=self._auth_header(),
            follow_redirects=False,
        )
        self.assertEqual(missing_token.status_code, 302)
        with self.app.app_context():
            self.assertEqual(self.db.session.get(self.ManualOrderDraft, draft_id).status, self.ManualOrderDraft.STATUS_DRAFT)

        cancel_page = self.client.get(cancel_url, headers=self._auth_header())
        cancelled = self.client.post(
            cancel_url,
            data={"csrf_token": self._csrf(cancel_page), "confirm_cancel": "cancelled"},
            headers=self._auth_header(),
            follow_redirects=False,
        )
        self.assertEqual(cancelled.status_code, 302)
        with self.app.app_context():
            draft = self.db.session.get(self.ManualOrderDraft, draft_id)
            self.assertEqual(draft.status, self.ManualOrderDraft.STATUS_CANCELLED)
            self.assertEqual(len(draft.lines), 1)
            self.assertEqual(draft.customer_draft["email"], "cliente@example.test")

        edit = self.client.get(self._edit_url(draft_id), headers=self._auth_header(), follow_redirects=False)
        self.assertEqual(edit.status_code, 302)


if __name__ == "__main__":
    unittest.main()
