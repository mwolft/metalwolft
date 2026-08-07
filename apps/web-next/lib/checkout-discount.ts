export const CHECKOUT_DISCOUNT_STORAGE_KEY = "mw_checkout_discount";

export function normalizeCheckoutDiscountCode(value: string) {
  return value.trim().toUpperCase();
}

export function loadStoredCheckoutDiscountCode() {
  if (typeof window === "undefined") {
    return null;
  }

  const storedCode = window.sessionStorage.getItem(CHECKOUT_DISCOUNT_STORAGE_KEY);
  const normalizedCode = normalizeCheckoutDiscountCode(storedCode || "");
  return normalizedCode || null;
}

export function saveStoredCheckoutDiscountCode(code: string) {
  if (typeof window === "undefined") {
    return;
  }

  const normalizedCode = normalizeCheckoutDiscountCode(code);
  if (!normalizedCode) {
    window.sessionStorage.removeItem(CHECKOUT_DISCOUNT_STORAGE_KEY);
    return;
  }

  window.sessionStorage.setItem(CHECKOUT_DISCOUNT_STORAGE_KEY, normalizedCode);
}

export function clearStoredCheckoutDiscountCode() {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.removeItem(CHECKOUT_DISCOUNT_STORAGE_KEY);
}
