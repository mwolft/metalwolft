import base64
import importlib.util
import re
import sys
import unittest
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def has_package(package):
    try:
        return importlib.util.find_spec(package) is not None
    except (ImportError, ValueError):
        return False


HAS_ADMIN_DEPS = all(
    has_package(package)
    for package in ("flask", "flask_admin", "flask_sqlalchemy", "sqlalchemy", "slugify")
)

if HAS_ADMIN_DEPS:
    from flask import Flask  # noqa: E402
    from flask_admin import Admin  # noqa: E402
    from sqlalchemy.orm import configure_mappers  # noqa: E402

    import api.admin as admin_module  # noqa: E402
    from api.supplier_invoice_registration_service import (  # noqa: E402
        SupplierInvoiceRegistrationValidationError,
    )
    from api.models import (  # noqa: E402
        SupplierInvoice,
        SupplierInvoiceDocument,
        SupplierInvoiceExtraction,
        SupplierInvoiceReceptionSequence,
        SupplierInvoiceTaxBreakdown,
        db,
    )
    from api.supplier_invoice_snapshot_integrity import calculate_supplier_invoice_snapshot_hash  # noqa: E402


@unittest.skipUnless(HAS_ADMIN_DEPS, "Flask Admin test dependencies are not installed.")
class FlaskAdminSupplierInvoiceTest(unittest.TestCase):
    def setUp(self):
        admin_module.ADMIN_USER = "admin"
        admin_module.ADMIN_PW = "secret"
        configure_mappers()
        self.app = Flask(__name__, template_folder=str(SRC_DIR / "templates"))
        self.app.config.update(
            SECRET_KEY="test-secret",
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        db.init_app(self.app)
        self.admin = Admin(self.app, url="/admin")
        self.view = admin_module.SupplierInvoiceAdminView(SupplierInvoice, db.session, name="Facturas recibidas")
        self.admin.add_view(self.view)
        with self.app.app_context():
            db.create_all()
            db.session.add(SupplierInvoiceReceptionSequence(id=1, last_number=0))
            self.invoice = self._make_draft()
            db.session.commit()
            self.invoice_id = self.invoice.id
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _make_draft(self):
        invoice = SupplierInvoice(
            supplier_legal_name="Acero Proveedor SL",
            supplier_tax_id="B12345678",
            supplier_invoice_number="P-2026-001",
            issue_date=date(2026, 8, 11),
            concept="Material de taller",
            total_amount=Decimal("121.00"),
            aeat_expense_concept_code="G03",
            expense_deductible_amount=Decimal("100.00"),
        )
        db.session.add(invoice)
        db.session.flush()
        db.session.add(
            SupplierInvoiceTaxBreakdown(
                supplier_invoice_id=invoice.id,
                position=1,
                tax_base=Decimal("100.00"),
                tax_rate=Decimal("21.00"),
                tax_amount=Decimal("21.00"),
                deductible_tax_amount=Decimal("21.00"),
            )
        )
        return invoice

    def _auth_header(self):
        token = base64.b64encode(b"admin:secret").decode("ascii")
        return {"Authorization": f"Basic {token}"}

    def _register_rule(self):
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint.endswith(".confirm_register"):
                return rule
        raise AssertionError("Supplier invoice registration route was not registered")

    def _url(self):
        return self._registration_url(self.invoice_id)

    def _registration_url(self, supplier_invoice_id):
        return self._register_rule().rule.replace("<int:supplier_invoice_id>", str(supplier_invoice_id))

    def _edit_url(self):
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint.endswith(".edit_view"):
                return f"{rule.rule}?id={self.invoice_id}"
        raise AssertionError("Supplier invoice edit route was not registered")

    def _legacy_classification_url(self, supplier_invoice_id):
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint.endswith(".classify_legacy_expense_aeat"):
                return rule.rule.replace("<int:supplier_invoice_id>", str(supplier_invoice_id))
        raise AssertionError("Supplier invoice legacy classification route was not registered")

    def _make_registered_legacy(self, *, supplier_tax_id="B13019559"):
        invoice = db.session.get(SupplierInvoice, self.invoice_id)
        snapshot = {
            "schema_version": 1,
            "supplier": {
                "legal_name": "Proveedor legacy SL",
                "tax_id": supplier_tax_id,
                "country_code": "ES",
                "tax_id_type": "NIF",
            },
            "document": {
                "supplier_invoice_number": "LEGACY-1",
                "reception_number": 7,
                "issue_date": "2026-06-12",
                "operation_date": None,
                "concept": "Material",
                "currency": "EUR",
                "fiscal_invoice_type": "F1",
                "tax_treatment": "domestic_standard",
                "special_regime_key": None,
            },
            "tax_breakdowns": [{
                "position": 1,
                "tax_base": "35.76",
                "tax_rate": "21.00",
                "tax_amount": "7.51",
                "deductible_tax_amount": "7.51",
            }],
            "totals": {
                "tax_base": "35.76",
                "tax_amount": "7.51",
                "deductible_tax_amount": "7.51",
                "total_amount": "43.27",
            },
            "registration": {
                "registered_at": "2026-06-12T00:00:00",
                "registered_by": "admin",
                "source": "manual",
                "duplicate_override_used": False,
            },
        }
        invoice.status = SupplierInvoice.STATUS_REGISTERED
        invoice.reception_number = 7
        invoice.registered_at = datetime(2026, 6, 12)
        invoice.fiscal_snapshot = snapshot
        invoice.snapshot_schema_version = 1
        invoice.snapshot_hash = calculate_supplier_invoice_snapshot_hash(snapshot)
        invoice.aeat_expense_concept_code = None
        invoice.expense_deductible_amount = None
        db.session.commit()
        return invoice

    def _upload_rule(self):
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint.endswith(".upload_document"):
                return rule
        raise AssertionError("Supplier invoice upload route was not registered")

    def _upload_url(self, supplier_invoice_id=None):
        rule = self._upload_rule().rule
        if supplier_invoice_id:
            return f"{rule}?supplier_invoice_id={supplier_invoice_id}"
        return rule

    def _upload_and_process_rule(self):
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint.endswith(".upload_and_process"):
                return rule
        raise AssertionError("Supplier invoice upload-and-process route was not registered")

    def _upload_and_process_url(self):
        return self._upload_and_process_rule().rule

    def _download_rule(self):
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint.endswith(".download_document"):
                return rule
        raise AssertionError("Supplier invoice download route was not registered")

    def _delete_document_rule(self):
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint.endswith(".delete_document"):
                return rule
        raise AssertionError("Supplier invoice delete document route was not registered")

    def _review_extraction_rule(self):
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint.endswith(".review_extraction"):
                return rule
        raise AssertionError("Supplier extraction review route was not registered")

    def _extract_rule(self):
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint.endswith(".extract_document"):
                return rule
        raise AssertionError("Supplier document extraction route was not registered")

    def _quick_upload_tokens(self):
        response = self.client.get(self._upload_and_process_url(), headers=self._auth_header())
        self.assertEqual(response.status_code, 200)
        csrf_token = re.search(rb'name="csrf_token" value="([^"]+)"', response.data).group(1).decode()
        submission_token = re.search(rb'name="submission_token" value="([^"]+)"', response.data).group(1).decode()
        return csrf_token, submission_token

    @staticmethod
    def _persisted_upload_result(supplier_invoice, db_session):
        document = SupplierInvoiceDocument(
            supplier_invoice=supplier_invoice,
            storage_provider="r2",
            storage_key=f"supplier-invoices/2026/08/quick-{supplier_invoice.id}.pdf",
            original_filename="factura.pdf",
            mime_type="application/pdf",
            file_size=4,
            sha256=(f"{supplier_invoice.id:064x}"[-64:]),
            uploaded_by="admin",
        )
        db_session.add(document)
        db_session.flush()
        return SimpleNamespace(document=document, duplicate_count=0)

    @staticmethod
    def _failed_extraction_result(document, db_session):
        extraction = SupplierInvoiceExtraction(
            supplier_invoice_document=document,
            provider="fake",
            extractor_version="fake-v1",
            status=SupplierInvoiceExtraction.STATUS_FAILED,
            payload_schema_version=1,
            error_code="extraction_failed",
            started_at=datetime(2026, 8, 11),
            completed_at=datetime(2026, 8, 11),
        )
        db_session.add(extraction)
        db_session.flush()
        return SimpleNamespace(extraction=extraction, succeeded=False)

    def test_quick_upload_page_and_supplier_invoice_list_use_the_same_route(self):
        quick_url = self._upload_and_process_url()
        response = self.client.get(quick_url, headers=self._auth_header())
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Nueva factura recibida", response.data)
        self.assertIn(b"SUBIR Y PROCESAR", response.data)
        self.assertIn(b'accept="application/pdf"', response.data)

        list_response = self.client.get("/admin/supplierinvoice/", headers=self._auth_header())
        self.assertEqual(list_response.status_code, 200)
        self.assertIn(b"SUBIR FACTURA", list_response.data)
        self.assertIn(quick_url.encode(), list_response.data)

    def test_dashboard_template_links_to_the_quick_upload_route(self):
        rendered = (SRC_DIR / "templates" / "admin" / "dashboard.html").read_text(encoding="utf-8")
        self.assertIn("NUEVA FACTURA RECIBIDA", rendered)
        self.assertIn("supplierinvoice.upload_and_process", rendered)

    def test_quick_pdf_upload_creates_one_draft_runs_extraction_and_redirects_to_review(self):
        csrf_token, submission_token = self._quick_upload_tokens()

        def upload(_file, *, supplier_invoice, db_session, **kwargs):
            self.assertEqual(kwargs["allowed_mime_types"], {"application/pdf"})
            return self._persisted_upload_result(supplier_invoice, db_session)

        with patch.object(admin_module, "upload_supplier_invoice_document", side_effect=upload) as uploader, patch.object(
            admin_module,
            "get_supplier_invoice_extraction_provider",
            return_value=SimpleNamespace(),
        ), patch.object(
            admin_module,
            "run_supplier_invoice_extraction",
            side_effect=lambda document, **kwargs: self._failed_extraction_result(document, kwargs["db_session"]),
        ) as extractor:
            response = self.client.post(
                self._upload_and_process_url(),
                data={
                    "csrf_token": csrf_token,
                    "submission_token": submission_token,
                    "document": (BytesIO(b"pdf"), "factura.pdf", "application/pdf"),
                },
                content_type="multipart/form-data",
                headers=self._auth_header(),
            )

        self.assertEqual(response.status_code, 302)
        self.assertIn("review-extraction", response.headers["Location"])
        uploader.assert_called_once()
        extractor.assert_called_once()
        with self.app.app_context():
            invoices = db.session.query(SupplierInvoice).all()
            self.assertEqual(len(invoices), 2)
            quick_draft = next(invoice for invoice in invoices if invoice.id != self.invoice_id)
            self.assertEqual(quick_draft.status, SupplierInvoice.STATUS_DRAFT)
            self.assertEqual(len(quick_draft.documents), 1)
            self.assertEqual(quick_draft.documents[0].mime_type, "application/pdf")
            self.assertEqual(quick_draft.documents[0].extractions[0].status, SupplierInvoiceExtraction.STATUS_FAILED)

    def test_quick_upload_rejects_non_pdf_without_creating_a_draft(self):
        csrf_token, submission_token = self._quick_upload_tokens()
        response = self.client.post(
            self._upload_and_process_url(),
            data={
                "csrf_token": csrf_token,
                "submission_token": submission_token,
                "document": (BytesIO(b"image"), "factura.png", "image/png"),
            },
            content_type="multipart/form-data",
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            self.assertEqual(db.session.query(SupplierInvoice).count(), 1)
            self.assertEqual(db.session.query(SupplierInvoiceDocument).count(), 0)

    def test_quick_upload_storage_failure_rolls_back_the_new_draft(self):
        csrf_token, submission_token = self._quick_upload_tokens()
        with patch.object(
            admin_module,
            "upload_supplier_invoice_document",
            side_effect=admin_module.SupplierInvoiceDocumentStorageOperationError("R2 unavailable"),
        ):
            response = self.client.post(
                self._upload_and_process_url(),
                data={
                    "csrf_token": csrf_token,
                    "submission_token": submission_token,
                    "document": (BytesIO(b"pdf"), "factura.pdf", "application/pdf"),
                },
                content_type="multipart/form-data",
                headers=self._auth_header(),
            )

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            self.assertEqual(db.session.query(SupplierInvoice).count(), 1)
            self.assertEqual(db.session.query(SupplierInvoiceDocument).count(), 0)

    def test_quick_upload_requires_csrf_and_consumes_the_submission_token(self):
        _csrf_token, submission_token = self._quick_upload_tokens()
        missing_csrf = self.client.post(
            self._upload_and_process_url(),
            data={"submission_token": submission_token},
            headers=self._auth_header(),
        )
        self.assertEqual(missing_csrf.status_code, 302)
        csrf_token, submission_token = self._quick_upload_tokens()

        with patch.object(
            admin_module,
            "upload_supplier_invoice_document",
            side_effect=lambda _file, *, supplier_invoice, db_session, **_kwargs: self._persisted_upload_result(
                supplier_invoice, db_session
            ),
        ), patch.object(
            admin_module,
            "get_supplier_invoice_extraction_provider",
            return_value=SimpleNamespace(),
        ), patch.object(
            admin_module,
            "run_supplier_invoice_extraction",
            side_effect=lambda document, **kwargs: self._failed_extraction_result(document, kwargs["db_session"]),
        ):
            first = self.client.post(
                self._upload_and_process_url(),
                data={
                    "csrf_token": csrf_token,
                    "submission_token": submission_token,
                    "document": (BytesIO(b"pdf"), "factura.pdf", "application/pdf"),
                },
                content_type="multipart/form-data",
                headers=self._auth_header(),
            )
            second = self.client.post(
                self._upload_and_process_url(),
                data={
                    "csrf_token": csrf_token,
                    "submission_token": submission_token,
                    "document": (BytesIO(b"pdf"), "factura.pdf", "application/pdf"),
                },
                content_type="multipart/form-data",
                headers=self._auth_header(),
            )

        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 302)
        with self.app.app_context():
            self.assertEqual(db.session.query(SupplierInvoice).count(), 2)

    def test_quick_upload_unexpected_extraction_error_compensates_r2_and_rolls_back(self):
        csrf_token, submission_token = self._quick_upload_tokens()
        storage = Mock()

        with patch.object(
            admin_module,
            "upload_supplier_invoice_document",
            side_effect=lambda _file, *, supplier_invoice, db_session, **_kwargs: self._persisted_upload_result(
                supplier_invoice, db_session
            ),
        ), patch.object(
            admin_module,
            "get_supplier_invoice_extraction_provider",
            return_value=SimpleNamespace(),
        ), patch.object(admin_module, "run_supplier_invoice_extraction", side_effect=RuntimeError("boom")), patch.object(
            admin_module,
            "get_supplier_invoice_document_storage",
            return_value=storage,
        ):
            response = self.client.post(
                self._upload_and_process_url(),
                data={
                    "csrf_token": csrf_token,
                    "submission_token": submission_token,
                    "document": (BytesIO(b"pdf"), "factura.pdf", "application/pdf"),
                },
                content_type="multipart/form-data",
                headers=self._auth_header(),
            )

        self.assertEqual(response.status_code, 302)
        storage.delete_document.assert_called_once()
        with self.app.app_context():
            self.assertEqual(db.session.query(SupplierInvoice).count(), 1)
            self.assertEqual(db.session.query(SupplierInvoiceDocument).count(), 0)

    def test_quick_upload_final_commit_failure_compensates_r2_and_rolls_back(self):
        csrf_token, submission_token = self._quick_upload_tokens()
        storage = Mock()

        with patch.object(
            admin_module,
            "upload_supplier_invoice_document",
            side_effect=lambda _file, *, supplier_invoice, db_session, **_kwargs: self._persisted_upload_result(
                supplier_invoice, db_session
            ),
        ), patch.object(
            admin_module,
            "get_supplier_invoice_extraction_provider",
            return_value=SimpleNamespace(),
        ), patch.object(
            admin_module,
            "run_supplier_invoice_extraction",
            side_effect=lambda document, **kwargs: self._failed_extraction_result(document, kwargs["db_session"]),
        ), patch.object(self.view.session, "commit", side_effect=RuntimeError("database unavailable")), patch.object(
            admin_module,
            "get_supplier_invoice_document_storage",
            return_value=storage,
        ):
            response = self.client.post(
                self._upload_and_process_url(),
                data={
                    "csrf_token": csrf_token,
                    "submission_token": submission_token,
                    "document": (BytesIO(b"pdf"), "factura.pdf", "application/pdf"),
                },
                content_type="multipart/form-data",
                headers=self._auth_header(),
            )

        self.assertEqual(response.status_code, 302)
        storage.delete_document.assert_called_once()
        with self.app.app_context():
            self.assertEqual(db.session.query(SupplierInvoice).count(), 1)
            self.assertEqual(db.session.query(SupplierInvoiceDocument).count(), 0)

    def test_confirmation_action_registers_only_an_editable_draft(self):
        response = self.client.get(self._url(), headers=self._auth_header())
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"CONFIRMAR Y REGISTRAR", response.data)

        response = self.client.post(self._url(), headers=self._auth_header())
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            registered = db.session.get(SupplierInvoice, self.invoice_id)
            self.assertEqual(registered.status, SupplierInvoice.STATUS_REGISTERED)
            self.assertEqual(registered.reception_number, 1)
            self.assertEqual(registered.snapshot_schema_version, 2)

    def test_new_draft_form_does_not_default_to_g01(self):
        with self.app.app_context():
            with self.app.test_request_context("/admin/supplierinvoice/new/"):
                form = self.view.create_form()
                html = str(form.aeat_expense_concept_code())

        self.assertIsNone(form.aeat_expense_concept_code.data)
        self.assertIn('value=""', html)
        self.assertNotIn('value="G01" selected', html)

    def test_new_draft_persists_blank_expense_code_as_null(self):
        response = self.client.post(
            "/admin/supplierinvoice/new/",
            data={
                "status": SupplierInvoice.STATUS_DRAFT,
                "aeat_expense_concept_code": "",
                "issue_date": "",
                "operation_date": "",
            },
            headers=self._auth_header(),
        )

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            draft = SupplierInvoice.query.order_by(SupplierInvoice.id.desc()).first()
            self.assertIsNone(draft.aeat_expense_concept_code)

    def test_operation_date_help_explains_registration_fallback(self):
        with self.app.app_context():
            with self.app.test_request_context("/admin/supplierinvoice/new/"):
                form = self.view.create_form()

        self.assertIn("Al aplicar una extracción", form.operation_date.description)
        self.assertIn("Puedes corregirla", form.operation_date.description)

    def test_edit_form_prefills_editable_expense_classification_for_empty_draft_values(self):
        with self.app.app_context():
            invoice = db.session.get(SupplierInvoice, self.invoice_id)
            invoice.supplier_tax_id = "B13559141"
            invoice.aeat_expense_concept_code = None
            invoice.expense_deductible_amount = None
            with self.app.test_request_context("/admin/supplierinvoice/edit/"):
                form = self.view.edit_form(invoice)

        self.assertEqual(form.aeat_expense_concept_code.data, "G01")
        self.assertEqual(form.expense_deductible_amount.data, Decimal("100.00"))
        self.assertEqual(form.aeat_expense_concept_code.label.text, "Concepto de gasto AEAT (propuesto)")
        self.assertIn("Propuesto según el NIF", form.aeat_expense_concept_code.description)

    def test_nonstandard_g01_requires_explicit_admin_confirmation(self):
        with self.app.app_context():
            invoice = db.session.get(SupplierInvoice, self.invoice_id)
            invoice.aeat_expense_concept_code = "G01"
            db.session.commit()

        response = self.client.get(self._url(), headers=self._auth_header())
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'name="allow_nonstandard_g01"', response.data)

        self.client.post(self._url(), headers=self._auth_header())
        with self.app.app_context():
            self.assertEqual(
                db.session.get(SupplierInvoice, self.invoice_id).status,
                SupplierInvoice.STATUS_DRAFT,
            )

        self.client.post(
            self._url(),
            data={"allow_nonstandard_g01": "1"},
            headers=self._auth_header(),
        )
        with self.app.app_context():
            self.assertEqual(
                db.session.get(SupplierInvoice, self.invoice_id).status,
                SupplierInvoice.STATUS_REGISTERED,
            )

    def test_registered_invoice_cannot_open_edit_or_be_deleted(self):
        self.client.post(self._url(), headers=self._auth_header())
        with self.app.app_context():
            registered = db.session.get(SupplierInvoice, self.invoice_id)
            response = self.client.get(self._edit_url(), headers=self._auth_header())
            self.assertEqual(response.status_code, 302)
        with self.app.test_request_context("/admin/supplierinvoice/"):
            self.assertFalse(self.view.delete_model(registered))

    def test_legacy_classification_requires_csrf_confirmation_and_persists_audit(self):
        with self.app.app_context():
            invoice = self._make_registered_legacy()
            snapshot_before = dict(invoice.fiscal_snapshot)
            hash_before = invoice.snapshot_hash
            url = self._legacy_classification_url(invoice.id)

        response = self.client.get(url, headers=self._auth_header())
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"CLASIFICAR GASTO AEAT LEGACY", response.data)
        self.assertIn(b'value="G01" selected', response.data)
        token = re.search(rb'name="csrf_token" value="([^"]+)"', response.data).group(1).decode()

        response = self.client.post(
            url,
            data={
                "csrf_token": token,
                "aeat_expense_concept_code": "G01",
                "expense_deductible_amount": "35.76",
                "legacy_expense_received_at": "2026-06-12",
            },
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            self.assertIsNone(db.session.get(SupplierInvoice, self.invoice_id).legacy_expense_classified_at)

        response = self.client.post(
            url,
            data={
                "csrf_token": token,
                "confirm_legacy_classification": "confirmed",
                "aeat_expense_concept_code": "G01",
                "expense_deductible_amount": "35.76",
                "legacy_expense_received_at": "2026-06-12",
            },
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            persisted = db.session.get(SupplierInvoice, self.invoice_id)
            self.assertEqual(persisted.aeat_expense_concept_code, "G01")
            self.assertEqual(persisted.expense_deductible_amount, Decimal("35.76"))
            self.assertEqual(persisted.legacy_expense_received_at, date(2026, 6, 12))
            self.assertEqual(persisted.legacy_expense_classified_by, "admin")
            self.assertIsNotNone(persisted.legacy_expense_classified_at)
            self.assertEqual(persisted.fiscal_snapshot, snapshot_before)
            self.assertEqual(persisted.snapshot_hash, hash_before)

    def test_legacy_classification_action_is_not_available_for_v2(self):
        response = self.client.get(
            self._legacy_classification_url(self.invoice_id),
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            self.assertIsNotNone(db.session.get(SupplierInvoice, self.invoice_id))

    def test_detail_formatter_offers_registration_only_before_registration(self):
        with self.app.app_context():
            view = type("View", (), {"get_url": lambda *_args, **_kwargs: "/register"})()
            before = admin_module._format_supplier_invoice_registration(view, None, self.invoice, None)
            self.assertIn("CONFIRMAR Y REGISTRAR", str(before))
            self.client.post(self._url(), headers=self._auth_header())
            registered = db.session.get(SupplierInvoice, self.invoice_id)
            after = admin_module._format_supplier_invoice_registration(view, None, registered, None)
            self.assertNotIn("CONFIRMAR Y REGISTRAR", str(after))

    def test_date_fields_render_as_native_iso_date_inputs_and_parse_dates(self):
        with self.app.app_context():
            invoice = db.session.get(SupplierInvoice, self.invoice_id)
            with self.app.test_request_context(
                "/admin/supplierinvoice/edit/",
                method="POST",
                data={"issue_date": "2026-07-25", "operation_date": "2026-12-31"},
            ):
                form = self.view.edit_form(invoice)

                self.assertIn("%Y-%m-%d", form.issue_date.format)
                self.assertIn("%Y-%m-%d", form.operation_date.format)
                issue_html = str(form.issue_date())
                operation_html = str(form.operation_date())
                self.assertIn('type="date"', issue_html)
                self.assertIn('type="date"', operation_html)
                self.assertNotIn("data-role=\"datepicker\"", issue_html)
                self.assertNotIn("data-role=\"datepicker\"", operation_html)
                self.assertNotIn("data-date-format", issue_html)
                self.assertNotIn("data-date-format", operation_html)
                for literal_token in ("yyyy", "Tu", "Su"):
                    self.assertNotIn(literal_token, issue_html)
                    self.assertNotIn(literal_token, operation_html)

                self.assertEqual(form.issue_date.data, date(2026, 7, 25))
                self.assertEqual(form.operation_date.data, date(2026, 12, 31))

    def test_create_then_edit_draft_preserves_issue_date_and_allows_empty_operation_date(self):
        with self.app.app_context():
            with self.app.test_request_context(
                "/admin/supplierinvoice/new/",
                method="POST",
                data={
                    "supplier_legal_name": "Proveedor de prueba SL",
                    "supplier_tax_id": "B87654321",
                    "supplier_invoice_number": "P-2026-002",
                    "issue_date": "2026-07-25",
                    "operation_date": "",
                    "concept": "Material auxiliar",
                    "total_amount": "0.00",
                    "currency": "EUR",
                    "fiscal_invoice_type": "F1",
                    "tax_treatment": "domestic_standard",
                    "status": "draft",
                    "source": "manual",
                },
            ):
                form = self.view.create_form()
                self.assertTrue(form.validate())
                invoice = SupplierInvoice()
                form.populate_obj(invoice)
            db.session.add(invoice)
            db.session.commit()

            updated = db.session.get(SupplierInvoice, invoice.id)
            self.assertEqual(updated.issue_date, date(2026, 7, 25))
            self.assertIsNone(updated.operation_date)

            with self.app.test_request_context("/admin/supplierinvoice/edit/"):
                edit_form = self.view.edit_form(updated)
                self.assertEqual(edit_form.issue_date.data, date(2026, 7, 25))
                self.assertIsNone(edit_form.operation_date.data)
                self.assertIn('value="2026-07-25"', str(edit_form.issue_date()))

    def test_draft_form_allows_empty_issue_and_operation_dates(self):
        with self.app.app_context():
            with self.app.test_request_context(
                "/admin/supplierinvoice/new/",
                method="POST",
                data={"issue_date": "", "operation_date": ""},
            ):
                form = self.view.create_form()
                self.assertTrue(form.validate())
                self.assertFalse(form.issue_date.errors)
                self.assertFalse(form.operation_date.errors)

    def test_tax_breakdown_inline_html_and_script_are_csp_safe(self):
        with self.app.app_context():
            invoice = db.session.get(SupplierInvoice, self.invoice_id)
            with self.app.test_request_context("/admin/supplierinvoice/edit/"):
                form = self.view.edit_form(invoice)
                inline_html = str(form.tax_breakdowns())

        script_path = SRC_DIR / "static" / "admin" / "supplier_invoice_tax_breakdowns.js"
        script = script_path.read_text(encoding="utf-8")

        self.assertIn('type="button"', inline_html)
        self.assertIn('data-supplier-invoice-inline-add="tax_breakdowns"', inline_html)
        self.assertNotIn("javascript:", inline_html.lower())
        self.assertNotIn("onclick=", inline_html.lower())
        self.assertEqual(self.view.extra_js, ["/static/admin/supplier_invoice_tax_breakdowns.js"])
        self.assertIn("window.faForm.addInlineField", script)
        self.assertIn("nextPosition", script)
        self.assertNotIn("javascript:", script.lower())
        self.assertNotIn("onclick", script.lower())

    def test_multiple_inline_tax_breakdowns_populate_with_distinct_positions(self):
        form_data = {
            "supplier_legal_name": "Proveedor de prueba SL",
            "supplier_tax_id": "B87654321",
            "supplier_invoice_number": "P-2026-003",
            "issue_date": "2026-07-25",
            "concept": "Material auxiliar",
            "total_amount": "242.00",
            "currency": "EUR",
            "fiscal_invoice_type": "F1",
            "tax_treatment": "domestic_standard",
            "status": "draft",
            "source": "manual",
            "tax_breakdowns-0-position": "1",
            "tax_breakdowns-0-tax_base": "100.00",
            "tax_breakdowns-0-tax_rate": "21.00",
            "tax_breakdowns-0-tax_amount": "21.00",
            "tax_breakdowns-0-deductible_tax_amount": "21.00",
            "tax_breakdowns-1-position": "2",
            "tax_breakdowns-1-tax_base": "100.00",
            "tax_breakdowns-1-tax_rate": "21.00",
            "tax_breakdowns-1-tax_amount": "21.00",
            "tax_breakdowns-1-deductible_tax_amount": "21.00",
        }
        with self.app.app_context():
            with self.app.test_request_context(
                "/admin/supplierinvoice/new/",
                method="POST",
                data=form_data,
            ):
                form = self.view.create_form()
                self.assertTrue(form.validate())
                invoice = SupplierInvoice()
                form.populate_obj(invoice)

            self.assertEqual(len(invoice.tax_breakdowns), 2)
            self.assertEqual([item.position for item in invoice.tax_breakdowns], [1, 2])

    def test_registration_error_messages_are_specific_and_safe(self):
        messages = {
            "Campo obligatorio ausente: supplier_legal_name.": "Indica la razón social o nombre del proveedor.",
            "Campo obligatorio ausente: supplier_tax_id.": "Indica el NIF/CIF del proveedor.",
            "Campo obligatorio ausente: supplier_invoice_number.": "Indica el número de factura del proveedor.",
            "Campo obligatorio ausente: issue_date.": "Indica la fecha de expedición.",
            "Fecha no válida: issue_date.": "Indica una fecha de expedición válida.",
            "Importe no válido: total_amount.": "Indica un total de factura válido.",
            "Debe existir al menos un desglose de IVA.": "Debe existir al menos un desglose de IVA.",
            "El total no coincide con la suma de las bases y cuotas de IVA.": (
                "El total no coincide con la suma de las bases y cuotas de IVA."
            ),
            "La cuota deducible no puede superar la cuota soportada.": (
                "La cuota deducible no puede superar la cuota soportada."
            ),
        }
        for source_message, expected_message in messages.items():
            with self.subTest(source_message=source_message):
                error = SupplierInvoiceRegistrationValidationError(source_message)
                self.assertEqual(
                    admin_module._supplier_invoice_registration_error_message(error),
                    expected_message,
                )

        unknown_error = SupplierInvoiceRegistrationValidationError("internal detail that must not be displayed")
        self.assertEqual(
            admin_module._supplier_invoice_registration_error_message(unknown_error),
            "No se ha podido registrar la factura recibida. Revisa sus datos fiscales.",
        )

    def test_registering_without_tax_breakdowns_flashes_the_specific_message(self):
        with self.app.app_context():
            invoice = SupplierInvoice(
                supplier_legal_name="Proveedor sin desglose SL",
                supplier_tax_id="B11223344",
                supplier_invoice_number="P-2026-004",
                issue_date=date(2026, 7, 25),
                concept="Documento sin desglose",
                total_amount=Decimal("0.00"),
            )
            db.session.add(invoice)
            db.session.commit()
            invoice_id = invoice.id

        response = self.client.post(self._registration_url(invoice_id), headers=self._auth_header())
        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction() as session:
            flashed_messages = [message for _category, message in session.get("_flashes", [])]
        self.assertIn("Debe existir al menos un desglose de IVA.", flashed_messages)

    def test_document_upload_page_is_authenticated_csrf_protected_and_csp_safe(self):
        response = self.client.get(self._upload_url(self.invoice_id), headers=self._auth_header())
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"SUBIR DOCUMENTO", response.data)
        self.assertIn(b'enctype="multipart/form-data"', response.data)
        self.assertIn(b'name="csrf_token"', response.data)
        self.assertNotIn(b"javascript:", response.data.lower())
        self.assertNotIn(b"onclick=", response.data.lower())

        invalid_response = self.client.post(
            self._upload_url(self.invoice_id),
            data={"document": (BytesIO(b"irrelevant"), "invoice.pdf")},
            content_type="multipart/form-data",
            headers=self._auth_header(),
        )
        self.assertEqual(invalid_response.status_code, 302)
        with self.client.session_transaction() as session:
            messages = [message for _category, message in session.get("_flashes", [])]
        self.assertIn("La sesión del formulario ha caducado. Vuelve a intentarlo.", messages)

    def test_upload_action_persists_via_service_and_warns_for_duplicate_hash(self):
        response = self.client.get(self._upload_url(self.invoice_id), headers=self._auth_header())
        token = re.search(rb'name="csrf_token" value="([^"]+)"', response.data).group(1).decode()

        with self.app.app_context():
            invoice = db.session.get(SupplierInvoice, self.invoice_id)
            document = SupplierInvoiceDocument(
                supplier_invoice=invoice,
                storage_provider="r2",
                storage_key="supplier-invoices/2026/08/test.pdf",
                original_filename="test.pdf",
                mime_type="application/pdf",
                file_size=4,
                sha256="a" * 64,
                uploaded_by="admin",
            )
            db.session.add(document)
            db.session.commit()

        result = SimpleNamespace(document=document, duplicate_count=1)
        with patch.object(admin_module, "upload_supplier_invoice_document", return_value=result) as upload:
            response = self.client.post(
                self._upload_url(self.invoice_id),
                data={
                    "csrf_token": token,
                    "document": (BytesIO(b"test"), "test.pdf"),
                },
                content_type="multipart/form-data",
                headers=self._auth_header(),
            )
        self.assertEqual(response.status_code, 302)
        upload.assert_called_once()
        with self.client.session_transaction() as session:
            messages = [message for _category, message in session.get("_flashes", [])]
        self.assertIn(
            "Se ha detectado un documento con el mismo hash. Revisa si es un duplicado antes de registrarlo.",
            messages,
        )

    def test_document_download_is_authenticated_and_uses_safe_headers(self):
        with self.app.app_context():
            invoice = db.session.get(SupplierInvoice, self.invoice_id)
            document = SupplierInvoiceDocument(
                supplier_invoice=invoice,
                storage_provider="r2",
                storage_key="supplier-invoices/2026/08/test.pdf",
                original_filename="test.pdf",
                mime_type="application/pdf",
                file_size=4,
                sha256="b" * 64,
            )
            db.session.add(document)
            db.session.commit()
            document_id = document.id

        storage = Mock()
        storage.get_document.return_value = b"test"
        url = self._download_rule().rule.replace("<int:document_id>", str(document_id))
        unauthorized_response = self.client.get(url)
        self.assertEqual(unauthorized_response.status_code, 401)
        with patch.object(admin_module, "get_supplier_invoice_document_storage", return_value=storage):
            response = self.client.get(url, headers=self._auth_header())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"test")
        self.assertIn("attachment; filename=test.pdf", response.headers["Content-Disposition"])
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_document_delete_requires_confirmation_and_only_shows_when_eligible(self):
        with self.app.app_context():
            invoice = db.session.get(SupplierInvoice, self.invoice_id)
            removable = SupplierInvoiceDocument(
                supplier_invoice=invoice,
                storage_provider="r2",
                storage_key="supplier-invoices/2026/08/removable.pdf",
                original_filename="removable.pdf",
                mime_type="application/pdf",
                file_size=4,
                sha256="1" * 64,
            )
            applied = SupplierInvoiceDocument(
                supplier_invoice=invoice,
                storage_provider="r2",
                storage_key="supplier-invoices/2026/08/applied.pdf",
                original_filename="applied.pdf",
                mime_type="application/pdf",
                file_size=4,
                sha256="2" * 64,
                processing_status=SupplierInvoiceDocument.STATUS_APPLIED,
            )
            db.session.add_all((removable, applied))
            db.session.flush()
            db.session.add(
                SupplierInvoiceExtraction(
                    supplier_invoice_document=applied,
                    provider="fake",
                    extractor_version="fake-v1",
                    status=SupplierInvoiceExtraction.STATUS_APPLIED,
                    payload_schema_version=1,
                    extraction_payload={"schema_version": 1},
                    payload_hash="3" * 64,
                    completed_at=datetime(2026, 8, 11),
                )
            )
            db.session.commit()
            with self.app.test_request_context("/admin/supplierinvoice/"):
                formatted = str(admin_module._format_supplier_invoice_documents(self.view, None, invoice, None))
            self.assertEqual(formatted.count("ELIMINAR DOCUMENTO"), 1)
            document_id = removable.id

        delete_url = self._delete_document_rule().rule.replace("<int:document_id>", str(document_id))
        response = self.client.get(delete_url, headers=self._auth_header())
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Confirmo que quiero eliminar", response.data)
        token = re.search(rb'name="csrf_token" value="([^"]+)"', response.data).group(1).decode()

        with patch.object(admin_module, "delete_supplier_invoice_document") as delete_document:
            response = self.client.post(
                delete_url,
                data={"csrf_token": token, "confirm_delete": "1"},
                headers=self._auth_header(),
            )
        self.assertEqual(response.status_code, 302)
        delete_document.assert_called_once()

    def test_registered_invoice_does_not_offer_or_accept_document_upload(self):
        self.client.post(self._url(), headers=self._auth_header())
        response = self.client.get(self._upload_url(self.invoice_id), headers=self._auth_header())
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            registered = db.session.get(SupplierInvoice, self.invoice_id)
            view = type("View", (), {"get_url": lambda *_args, **_kwargs: "/documents"})()
            formatted = str(admin_module._format_supplier_invoice_documents(view, None, registered, None))
        self.assertNotIn("SUBIR DOCUMENTO", formatted)

    def test_extraction_action_and_review_are_csrf_safe_and_do_not_register(self):
        payload = {
            "schema_version": 1,
            "fields": {
                name: {"value": None, "confidence": None, "source": None}
                for name in (
                    "supplier_legal_name", "supplier_tax_id", "supplier_invoice_number",
                    "issue_date", "operation_date", "concept", "currency", "total_amount",
                    "fiscal_invoice_type", "tax_treatment",
                )
            },
            "tax_breakdowns": [
                {
                    "tax_base": "263.09",
                    "tax_rate": "21.00",
                    "tax_amount": "55.25",
                    "deductible_tax_amount": None,
                    "confidence": 0.98,
                    "source": None,
                },
                {
                    "tax_base": "100.00",
                    "tax_rate": "10.00",
                    "tax_amount": "10.00",
                    "deductible_tax_amount": None,
                    "confidence": 0.97,
                    "source": None,
                },
            ],
            "warnings": ["Revisión manual necesaria."],
        }
        payload["fields"]["currency"]["value"] = "EUR"
        payload["fields"]["fiscal_invoice_type"]["value"] = "F1"
        payload["fields"]["tax_treatment"]["value"] = "domestic_standard"
        with self.app.app_context():
            invoice = db.session.get(SupplierInvoice, self.invoice_id)
            document = SupplierInvoiceDocument(
                supplier_invoice=invoice,
                storage_provider="r2",
                storage_key="supplier-invoices/2026/08/extraction.pdf",
                original_filename="extraction.pdf",
                mime_type="application/pdf",
                file_size=4,
                sha256="c" * 64,
            )
            db.session.add(document)
            db.session.flush()
            extraction = SupplierInvoiceExtraction(
                supplier_invoice_document=document,
                provider="fake",
                extractor_version="fake-v1",
                status=SupplierInvoiceExtraction.STATUS_NEEDS_REVIEW,
                payload_schema_version=1,
                extraction_payload=payload,
                payload_hash="d" * 64,
                started_at=datetime(2026, 8, 11),
                completed_at=datetime(2026, 8, 11),
            )
            db.session.add(extraction)
            db.session.commit()
            extraction_id = extraction.id
            with self.app.test_request_context("/admin/supplierinvoice/"):
                formatted = str(admin_module._format_supplier_invoice_extraction(self.view, None, invoice, None))
        self.assertIn("EXTRAER DATOS", formatted)
        self.assertIn('method="post"', formatted)
        self.assertNotIn("javascript:", formatted.lower())
        self.assertNotIn("onclick=", formatted.lower())

        review_url = self._review_extraction_rule().rule.replace("<int:extraction_id>", str(extraction_id))
        response = self.client.get(review_url, headers=self._auth_header())
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Revisar propuesta de extracci", response.data)
        self.assertIn(b"Revisi", response.data)
        deductible_inputs = re.findall(
            rb'name="deductible_tax_amount"[^>]*value="([^"]+)"',
            response.data,
        )
        self.assertEqual(deductible_inputs, [b"55.25", b"10.00"])
        with self.app.app_context():
            invoice = db.session.get(SupplierInvoice, self.invoice_id)
            self.assertEqual(invoice.status, SupplierInvoice.STATUS_DRAFT)
            self.assertIsNone(invoice.reception_number)

    def test_extract_document_post_creates_a_reviewable_attempt_without_registering(self):
        with self.app.app_context():
            invoice = db.session.get(SupplierInvoice, self.invoice_id)
            document = SupplierInvoiceDocument(
                supplier_invoice=invoice,
                storage_provider="r2",
                storage_key="supplier-invoices/2026/08/extract-post.pdf",
                original_filename="extract-post.pdf",
                mime_type="application/pdf",
                file_size=4,
                sha256="e" * 64,
            )
            db.session.add(document)
            db.session.commit()
            document_id = document.id

        upload_page = self.client.get(self._upload_url(self.invoice_id), headers=self._auth_header())
        token = re.search(rb'name="csrf_token" value="([^"]+)"', upload_page.data).group(1).decode()
        storage = Mock()
        storage.get_document.return_value = b"test"
        extract_url = self._extract_rule().rule.replace("<int:document_id>", str(document_id))
        with patch(
            "api.supplier_invoice_extraction_service.get_supplier_invoice_document_storage",
            return_value=storage,
        ):
            response = self.client.post(
                extract_url,
                data={"csrf_token": token},
                headers=self._auth_header(),
            )
        self.assertEqual(response.status_code, 302)
        self.assertIn("review-extraction", response.headers["Location"])
        with self.app.app_context():
            extraction = db.session.query(SupplierInvoiceExtraction).one()
            invoice = db.session.get(SupplierInvoice, self.invoice_id)
            self.assertEqual(extraction.status, SupplierInvoiceExtraction.STATUS_NEEDS_REVIEW)
            self.assertEqual(invoice.status, SupplierInvoice.STATUS_DRAFT)
            self.assertIsNone(invoice.reception_number)


if __name__ == "__main__":
    unittest.main()
