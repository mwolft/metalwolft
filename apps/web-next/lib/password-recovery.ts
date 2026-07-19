export type PasswordRecoveryResponse = {
  error?: string;
  message?: string;
};

export const FORGOT_PASSWORD_PATH = "/api/auth/forgot-password";
export const RESET_PASSWORD_PATH = "/api/auth/reset-password";

export function normalizeRecoveryEmail(email: string) {
  return email.trim().toLowerCase();
}

export function validateRecoveryEmail(email: string) {
  const normalizedEmail = normalizeRecoveryEmail(email);
  return normalizedEmail.length > 0 && normalizedEmail.includes("@");
}

export function buildForgotPasswordPayload(email: string) {
  return {
    email: normalizeRecoveryEmail(email)
  };
}

export function buildResetPasswordPayload(token: string, password: string) {
  return {
    token,
    password
  };
}

export function validateResetPasswordInput(input: {
  token: string | null | undefined;
  password: string;
  confirmPassword: string;
}) {
  if (!input.token) {
    return "El enlace de recuperación no es válido. Solicita uno nuevo.";
  }

  if (!input.password) {
    return "Introduce una nueva contraseña.";
  }

  if (input.password !== input.confirmPassword) {
    return "Las contraseñas no coinciden.";
  }

  return "";
}

export function getSafePasswordRecoveryMessage(
  payload: PasswordRecoveryResponse | null,
  fallback: string
) {
  const message = payload?.message || payload?.error;
  if (!message || /internal server error/i.test(message)) {
    return fallback;
  }

  return message;
}
