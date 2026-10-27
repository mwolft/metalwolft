export const CHANGE_PASSWORD_PATH = "/api/auth/change-password";

export function validatePasswordChange(current: string, next: string, confirmation: string) {
  if (!current || !next || !confirmation) return "Completa los tres campos.";
  if (next !== confirmation) return "Las contraseñas nuevas no coinciden.";
  if (next === current) return "La contraseña nueva debe ser distinta de la actual.";
  const byteLength = new TextEncoder().encode(next).length;
  if (byteLength < 8 || byteLength > 72) {
    return "La contraseña nueva debe tener entre 8 y 72 bytes UTF-8.";
  }
  return null;
}

export function passwordChangeError(status: number) {
  switch (status) {
    case 400: return "Revisa la contraseña nueva e inténtalo de nuevo.";
    case 401: return "Tu sesión ha caducado. Inicia sesión de nuevo.";
    case 403: return "La contraseña actual es incorrecta.";
    case 409: return "La contraseña cambió durante la solicitud. Inicia sesión de nuevo.";
    case 429: return "Demasiados intentos. Inténtalo más tarde.";
    case 503: return "El servicio no está disponible temporalmente. Inténtalo más tarde.";
    default: return "No se pudo cambiar la contraseña. Inténtalo de nuevo.";
  }
}
