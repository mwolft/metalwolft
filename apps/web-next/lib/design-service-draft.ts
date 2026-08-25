export const DESIGN_SERVICE_DRAFT_STORAGE_KEY = "mw:design-service-draft:v1";
export const DESIGN_SERVICE_DRAFT_VERSION = 1;

export type DesignServiceDraftItem = {
  product_id: number;
  product_slug: string;
  product_name: string;
  width_cm: number;
  height_cm: number;
};

type StoredDesignServiceDraft = {
  version: number;
  items: DesignServiceDraftItem[];
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isPositiveNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value) && value > 0;
}

function isSlug(value: unknown): value is string {
  return typeof value === "string" && /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(value) && value.length <= 160;
}

function isProductName(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0 && value.length <= 255;
}

function normalizeItem(value: unknown): DesignServiceDraftItem | null {
  if (!isRecord(value)) {
    return null;
  }

  if (
    !Number.isInteger(value.product_id) ||
    typeof value.product_id !== "number" ||
    value.product_id <= 0 ||
    !isSlug(value.product_slug) ||
    !isProductName(value.product_name) ||
    !isPositiveNumber(value.width_cm) ||
    !isPositiveNumber(value.height_cm)
  ) {
    return null;
  }

  return {
    product_id: value.product_id,
    product_slug: value.product_slug,
    product_name: value.product_name.trim(),
    width_cm: value.width_cm,
    height_cm: value.height_cm
  };
}

function itemKey(item: DesignServiceDraftItem) {
  return `${item.product_id}:${item.width_cm}:${item.height_cm}`;
}

export function normalizeDesignServiceDraftItems(items: unknown): DesignServiceDraftItem[] {
  if (!Array.isArray(items)) {
    return [];
  }

  const seen = new Set<string>();
  const normalized: DesignServiceDraftItem[] = [];
  for (const rawItem of items) {
    const item = normalizeItem(rawItem);
    if (!item || seen.has(itemKey(item))) {
      continue;
    }
    seen.add(itemKey(item));
    normalized.push(item);
  }
  return normalized;
}

function canUseSessionStorage() {
  return typeof window !== "undefined" && Boolean(window.sessionStorage);
}

export function loadDesignServiceDraft(): DesignServiceDraftItem[] {
  if (!canUseSessionStorage()) {
    return [];
  }

  const raw = window.sessionStorage.getItem(DESIGN_SERVICE_DRAFT_STORAGE_KEY);
  if (!raw) {
    return [];
  }

  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!isRecord(parsed) || parsed.version !== DESIGN_SERVICE_DRAFT_VERSION) {
      window.sessionStorage.removeItem(DESIGN_SERVICE_DRAFT_STORAGE_KEY);
      return [];
    }

    return normalizeDesignServiceDraftItems(parsed.items);
  } catch {
    window.sessionStorage.removeItem(DESIGN_SERVICE_DRAFT_STORAGE_KEY);
    return [];
  }
}

export function saveDesignServiceDraft(items: unknown): DesignServiceDraftItem[] {
  const normalized = normalizeDesignServiceDraftItems(items);
  if (!canUseSessionStorage()) {
    return normalized;
  }

  const payload: StoredDesignServiceDraft = {
    version: DESIGN_SERVICE_DRAFT_VERSION,
    items: normalized
  };
  window.sessionStorage.setItem(DESIGN_SERVICE_DRAFT_STORAGE_KEY, JSON.stringify(payload));
  return normalized;
}

export function clearDesignServiceDraft() {
  if (canUseSessionStorage()) {
    window.sessionStorage.removeItem(DESIGN_SERVICE_DRAFT_STORAGE_KEY);
  }
}
