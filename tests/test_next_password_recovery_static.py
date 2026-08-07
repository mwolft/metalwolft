from pathlib import Path
import unittest


ROOT_DIR = Path(__file__).resolve().parents[1]
WEB_NEXT_DIR = ROOT_DIR / "apps" / "web-next"


def read_web_next_file(relative_path):
    return (WEB_NEXT_DIR / relative_path).read_text(encoding="utf-8")


class NextPasswordRecoveryStaticTest(unittest.TestCase):
    def test_login_links_to_forgot_password(self):
        login_form = read_web_next_file("components/auth/LoginForm.tsx")

        self.assertIn('href="/forgot-password"', login_form)
        self.assertIn("¿Has olvidado tu contraseña?", login_form)

    def test_forgot_password_page_and_form_use_expected_contract(self):
        page = read_web_next_file("app/forgot-password/page.tsx")
        form = read_web_next_file("components/auth/ForgotPasswordForm.tsx")

        self.assertIn("ForgotPasswordForm", page)
        self.assertIn("FORGOT_PASSWORD_PATH", form)
        self.assertIn("buildForgotPasswordPayload(email)", form)
        self.assertIn("validateRecoveryEmail(email)", form)
        self.assertIn('autoComplete="email"', form)
        self.assertIn('type="email"', form)
        self.assertIn('disabled={isSubmitting}', form)
        self.assertNotIn("localStorage", form)
        self.assertNotIn("sessionStorage", form)

    def test_reset_password_page_reads_query_token_and_posts_expected_payload(self):
        page = read_web_next_file("app/reset-password/page.tsx")
        form = read_web_next_file("components/auth/ResetPasswordForm.tsx")

        self.assertIn("searchParams?.token", page)
        self.assertIn("ResetPasswordForm token={token}", page)
        self.assertIn("RESET_PASSWORD_PATH", form)
        self.assertIn("buildResetPasswordPayload(token!, password)", form)
        self.assertIn("validateResetPasswordInput", form)
        self.assertIn('autoComplete="new-password"', form)
        self.assertIn('type="password"', form)
        self.assertIn("password !== input.confirmPassword", read_web_next_file("lib/password-recovery.ts"))
        self.assertNotIn("localStorage", form)
        self.assertNotIn("sessionStorage", form)

    def test_password_recovery_helper_uses_real_backend_paths(self):
        helper = read_web_next_file("lib/password-recovery.ts")

        self.assertIn('FORGOT_PASSWORD_PATH = "/api/auth/forgot-password"', helper)
        self.assertIn('RESET_PASSWORD_PATH = "/api/auth/reset-password"', helper)
        self.assertIn("email: normalizeRecoveryEmail(email)", helper)
        self.assertIn("token,", helper)
        self.assertIn("password", helper)
        self.assertIn("internal server error", helper)


if __name__ == "__main__":
    unittest.main()
