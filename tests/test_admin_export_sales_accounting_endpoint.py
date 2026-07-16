import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def routes_source():
    return (ROOT_DIR / "src/api/routes.py").read_text(encoding="utf-8")


def function_source(function_name):
    source = routes_source()
    start = source.index(f"def {function_name}")
    next_route = source.find("\n@api.route", start + 1)
    next_function = source.find("\ndef ", start + 1)
    endings = [position for position in (next_route, next_function) if position != -1]
    if not endings:
        return source[start:]
    return source[start:min(endings)]


def endpoint_source():
    return function_source("admin_export_sales_accounting_entries")


class AdminExportSalesAccountingEndpointSourceTest(unittest.TestCase):
    def test_route_is_get_admin_endpoint_and_requires_jwt(self):
        source = routes_source()
        route_start = source.index("@api.route('/admin/accounting/sales/export', methods=['GET'])")
        route_header = source[route_start:source.index("def admin_export_sales_accounting_entries", route_start)]

        self.assertIn("@jwt_required()", route_header)
        self.assertIn("methods=['GET']", route_header)

    def test_non_admin_is_rejected(self):
        source = endpoint_source()

        self.assertIn('if not current_user.get("is_admin"):', source)
        self.assertIn("Access forbidden: Admins only", source)
        self.assertIn("), 403", source)

    def test_only_date_filters_are_allowed(self):
        source = routes_source()
        endpoint = endpoint_source()

        self.assertIn('ALLOWED_ACCOUNTING_EXPORT_QUERY_PARAMS = {"date_from", "date_to"}', source)
        self.assertIn("unexpected_params = set(request.args.keys()) - ALLOWED_ACCOUNTING_EXPORT_QUERY_PARAMS", endpoint)
        self.assertIn("ACCOUNTING_EXPORT_QUERY_NOT_ALLOWED", endpoint)
        self.assertNotIn("output_path = request.args", endpoint)
        self.assertNotIn("filename = request.args", endpoint)

    def test_dates_are_parsed_as_iso_dates(self):
        helper = function_source("_parse_accounting_export_date")
        endpoint = endpoint_source()

        self.assertIn('datetime.strptime(value, "%Y-%m-%d").date()', helper)
        self.assertIn('request.args.get("date_from")', endpoint)
        self.assertIn('request.args.get("date_to")', endpoint)
        self.assertIn("ACCOUNTING_EXPORT_INVALID_DATE", endpoint)
        self.assertIn("), 400", endpoint)

    def test_inverted_range_is_rejected(self):
        source = endpoint_source()

        self.assertIn("if date_from and date_to and date_from > date_to:", source)
        self.assertIn("ACCOUNTING_EXPORT_INVALID_RANGE", source)
        self.assertIn("), 400", source)

    def test_query_uses_only_accounting_entry_sale_records(self):
        source = endpoint_source()

        self.assertIn("query = AccountingEntry.query.filter_by(entry_type=ENTRY_TYPE_SALE)", source)
        self.assertIn("AccountingEntry.invoice_date >= date_from", source)
        self.assertIn("AccountingEntry.invoice_date <= date_to", source)
        for forbidden in (
            "Invoices.query",
            "Orders.query",
            "Users.query",
            "CheckoutSessions.query",
            "invoice_snapshot",
        ):
            self.assertNotIn(forbidden, source)

    def test_query_order_matches_service_order(self):
        source = endpoint_source()

        self.assertIn("AccountingEntry.invoice_date.asc()", source)
        self.assertIn("AccountingEntry.invoice_number.asc()", source)
        self.assertIn("AccountingEntry.id.asc()", source)

    def test_no_records_returns_404(self):
        source = endpoint_source()

        self.assertIn("if not entries:", source)
        self.assertIn("ACCOUNTING_EXPORT_NO_RECORDS", source)
        self.assertIn("), 404", source)

    def test_filename_policy_is_deterministic(self):
        helper = function_source("_accounting_sales_export_filename")

        self.assertIn('return "ingresos_completo.xlsx"', helper)
        self.assertIn('from_label = date_from.isoformat() if date_from else "inicio"', helper)
        self.assertIn('to_label = date_to.isoformat() if date_to else "fin"', helper)
        self.assertIn('return f"ingresos_{from_label}_{to_label}.xlsx"', helper)

    def test_export_folder_uses_controlled_config_with_safe_fallback(self):
        helper = function_source("_accounting_export_folder")

        self.assertIn('current_app.config.get("ACCOUNTING_EXPORT_FOLDER")', helper)
        self.assertIn('os.getenv("ACCOUNTING_EXPORT_FOLDER")', helper)
        self.assertIn("current_app, \"instance_path\"", helper)
        self.assertIn("tempfile.gettempdir()", helper)
        self.assertNotIn("request.args", helper)

    def test_endpoint_delegates_to_excel_service_with_overwrite(self):
        source = endpoint_source()

        self.assertIn("export_sales_accounting_entries(entries, output_path=output_path, overwrite=True)", source)
        self.assertNotIn("Workbook(", source)
        self.assertNotIn("openpyxl", source)

    def test_response_is_xlsx_attachment(self):
        source = endpoint_source()

        self.assertIn("send_file(", source)
        self.assertIn("as_attachment=True", source)
        self.assertIn("download_name=result.filename", source)
        self.assertIn("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", source)

    def test_endpoint_does_not_expose_absolute_paths_as_json(self):
        source = endpoint_source()

        self.assertNotIn('"output_path"', source)
        self.assertNotIn('"file_path"', source)
        self.assertNotIn("jsonify(result.output_path", source)

    def test_endpoint_does_not_modify_accounting_entries(self):
        source = endpoint_source()

        for forbidden in (
            "entry.status =",
            "entry.recorded_at =",
            "AccountingEntry(",
            "db.session.add",
            "db.session.delete",
        ):
            self.assertNotIn(forbidden, source)

    def test_endpoint_does_not_commit_or_rollback(self):
        source = endpoint_source()

        self.assertNotIn("db.session.commit()", source)
        self.assertNotIn("db.session.rollback()", source)

    def test_export_errors_are_sanitized(self):
        source = endpoint_source()

        self.assertIn("except AccountingExcelExportError:", source)
        self.assertIn("logger.exception", source)
        self.assertIn("ACCOUNTING_EXPORT_FAILED", source)
        self.assertNotIn('"error": str(', source)
        self.assertNotIn("traceback", source.lower())

    def test_imports_excel_service_and_tempfile(self):
        source = routes_source()

        self.assertIn("import tempfile", source)
        self.assertIn("AccountingExcelExportError", source)
        self.assertIn("export_sales_accounting_entries", source)

    def test_env_example_documents_export_folder(self):
        env_example = (ROOT_DIR / ".env.example").read_text(encoding="utf-8")

        self.assertIn("ACCOUNTING_EXPORT_FOLDER=", env_example)

    def test_endpoint_does_not_call_invoice_order_user_or_checkout_services(self):
        source = endpoint_source()

        for forbidden in (
            "issue_invoice_for_order",
            "create_accounting_entry",
            "generate_invoice_pdf",
            "send_email",
            "build_checkout_quote",
            "cleanup_cart_lines_from_checkout_quote",
            "validate_payment_amount",
        ):
            self.assertNotIn(forbidden, source)

    def test_no_csv_email_or_external_side_effects(self):
        source = endpoint_source().lower()

        for forbidden in ("csv", "email", "mail.", "verifactu", "paypal", "stripe"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
