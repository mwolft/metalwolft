const STORAGE_KEY = "mw_design_purchase_seed";
const MAX_AGE_MS = 10 * 60 * 1000;

export type DesignPurchaseSeed = {
  categorySlug: string;
  productSlug: string;
  heightCm: string;
  widthCm: string;
};

function validDimension(value: string) {
  return /^\d+(?:\.\d{1,2})?$/.test(value) && Number.isFinite(Number(value)) && Number(value) > 0;
}

function validSlug(value: string) {
  return /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(value);
}

export function isDesignPurchaseSeed(value: DesignPurchaseSeed) {
  return validSlug(value.categorySlug) && validSlug(value.productSlug) &&
    validDimension(value.heightCm) && validDimension(value.widthCm);
}

export function saveDesignPurchaseSeed(value: DesignPurchaseSeed) {
  if (!isDesignPurchaseSeed(value)) return false;
  try {
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ ...value, createdAt: Date.now() }));
    return true;
  } catch {
    return false;
  }
}

export function consumeDesignPurchaseSeed(categorySlug: string, productSlug: string): DesignPurchaseSeed | null {
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as DesignPurchaseSeed & { createdAt: number };
    if (!parsed || !Number.isFinite(parsed.createdAt) || Date.now() - parsed.createdAt > MAX_AGE_MS ||
        parsed.createdAt > Date.now() || !isDesignPurchaseSeed(parsed)) {
      window.sessionStorage.removeItem(STORAGE_KEY);
      return null;
    }
    if (parsed.categorySlug !== categorySlug || parsed.productSlug !== productSlug) return null;
    window.sessionStorage.removeItem(STORAGE_KEY);
    return parsed;
  } catch {
    try { window.sessionStorage.removeItem(STORAGE_KEY); } catch { /* Storage unavailable. */ }
    return null;
  }
}
