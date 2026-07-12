const TOKEN_STORAGE_KEY = "token";
const USER_STORAGE_KEY = "user";

export type AuthUser = {
  id: number;
  email: string;
  firstname?: string | null;
  lastname?: string | null;
  is_active?: boolean;
  is_admin?: boolean;
  shipping_address?: string | null;
  shipping_city?: string | null;
  shipping_postal_code?: string | null;
  billing_address?: string | null;
  billing_city?: string | null;
  billing_postal_code?: string | null;
  CIF?: string | null;
};

export function saveSession(accessToken: string, user: AuthUser) {
  window.localStorage.setItem(TOKEN_STORAGE_KEY, accessToken);
  window.localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
}

export function getToken() {
  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function getStoredUser(): AuthUser | null {
  const rawUser = window.localStorage.getItem(USER_STORAGE_KEY);
  if (!rawUser || rawUser === "undefined") {
    return null;
  }

  try {
    const parsed = JSON.parse(rawUser) as unknown;
    return parsed && typeof parsed === "object" ? (parsed as AuthUser) : null;
  } catch {
    clearSession();
    return null;
  }
}

export function clearSession() {
  window.localStorage.removeItem(TOKEN_STORAGE_KEY);
  window.localStorage.removeItem(USER_STORAGE_KEY);
}

export function getSafeInternalPath(value: string | null | undefined) {
  const trimmed = value?.trim();
  if (!trimmed || !trimmed.startsWith("/") || trimmed.startsWith("//") || trimmed.includes("\\")) {
    return "/";
  }

  try {
    const parsed = new URL(trimmed, window.location.origin);
    return parsed.origin === window.location.origin
      ? `${parsed.pathname}${parsed.search}${parsed.hash}`
      : "/";
  } catch {
    return "/";
  }
}
