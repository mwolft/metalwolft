import ast
import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
ROUTES_PATH = SRC_DIR / "api" / "routes.py"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def signup_source():
    source = ROUTES_PATH.read_text(encoding="utf-8")
    module = ast.parse(source)
    function = next(
        node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "signup"
    )
    return ast.get_source_segment(source, function)


class SignupWelcomeEmailTest(unittest.TestCase):
    def test_signup_reuses_renderer_without_changing_delivery_contract(self):
        source = signup_source()

        self.assertIn("render_account_welcome_email(", source)
        self.assertIn('login_url="https://www.metalwolft.com/login"', source)
        self.assertIn('subject="' + chr(0xA1) + 'Bienvenido a Metal Wolft!"', source)
        self.assertIn("recipients=[email]", source)
        self.assertIn("body=rendered_welcome_email.text", source)
        self.assertIn("html=rendered_welcome_email.html", source)


if __name__ == "__main__":
    unittest.main()
