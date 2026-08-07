import ast
import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
ROUTES_PATH = ROOT_DIR / "src/api/routes.py"
ADMIN_PATH = ROOT_DIR / "src/api/admin.py"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def source(path):
    return path.read_text(encoding="utf-8")


def function_source(path, function_name):
    text = source(path)
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return ast.get_source_segment(text, node)
    raise AssertionError(f"{function_name} not found in {path}")


class InvoicePdfDownloadEndpointCompatibilityTest(unittest.TestCase):
    def setUp(self):
        self.download_source = function_source(ROUTES_PATH, "download_invoice")
        self.admin_download_source = function_source(ADMIN_PATH, "download_pdf")

    def test_jwt_download_endpoint_keeps_auth_and_filename_guard(self):
        route_source = source(ROUTES_PATH)
        route_start = route_source.index("@api.route('/download-invoice/<filename>', methods=['GET'])")
        route_header = route_source[route_start:route_source.index("def download_invoice", route_start)]

        self.assertIn("@jwt_required()", route_header)
        self.assertIn("safe_filename = os.path.basename(filename)", self.download_source)
        self.assertIn("safe_filename != filename", self.download_source)

    def test_jwt_download_endpoint_reuses_safe_resolver_for_valid_files(self):
        self.assertIn("resolve_invoice_pdf_download(", self.download_source)
        self.assertIn("resolved_pdf.file_path", self.download_source)
        self.assertIn("download_name=safe_filename", self.download_source)

    def test_jwt_download_keeps_legacy_fallback_only_for_missing_admin_file(self):
        missing_file_block = self.download_source[
            self.download_source.index("except InvoicePdfDownloadFileMissing"):
            self.download_source.index("except InvoicePdfDownloadInvalidPath")
        ]

        self.assertIn('if current_user.get("is_admin"):', missing_file_block)
        self.assertIn("render_original_order_invoice_pdf(", missing_file_block)
        self.assertIn("BytesIO(regenerated_pdf)", missing_file_block)
        self.assertNotIn("render_original_order_invoice_pdf(", self.admin_download_source)
        self.assertNotIn("BytesIO(", self.admin_download_source)

    def test_jwt_download_invalid_path_and_unexpected_errors_are_sanitized(self):
        invalid_path_block = self.download_source[
            self.download_source.index("except InvoicePdfDownloadInvalidPath"):
            self.download_source.index("except Exception")
        ]
        unexpected_block = self.download_source[self.download_source.index("except Exception"):]

        self.assertIn("Invoice not found", invalid_path_block)
        self.assertNotIn("str(e)", unexpected_block)
        self.assertNotIn('"error":', unexpected_block)
        self.assertIn("logger.exception", unexpected_block)
        self.assertIn("An error occurred while downloading the invoice.", unexpected_block)


if __name__ == "__main__":
    unittest.main()
