type DesignServiceRequestItem = {
  product_id: number;
  width_cm: number;
  height_cm: number;
};

export const DESIGN_SERVICE_REQUEST_STORAGE_KEY = "mw:design-service-request:v1";
export const DESIGN_SERVICE_REQUEST_STORAGE_VERSION = 1;

type StoredRequest = {
  version: number;
  user_id: number;
  draft_key: string;
  creation_key: string;
  design_request_id?: number;
};

function canUseSessionStorage() {
  return typeof window !== "undefined" && Boolean(window.sessionStorage);
}

function isPositiveInteger(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value) && value > 0;
}

function isStoredRequest(value: unknown): value is StoredRequest {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<StoredRequest>;
  return (
    candidate.version === DESIGN_SERVICE_REQUEST_STORAGE_VERSION &&
    isPositiveInteger(candidate.user_id) &&
    typeof candidate.draft_key === "string" &&
    candidate.draft_key.length > 0 &&
    typeof candidate.creation_key === "string" &&
    candidate.creation_key.length > 0 &&
    (candidate.design_request_id === undefined || isPositiveInteger(candidate.design_request_id))
  );
}

function createKey() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export function designServiceDraftKey(items: readonly DesignServiceRequestItem[]) {
  return items
    .map((item) => `${item.product_id}:${item.width_cm}:${item.height_cm}`)
    .sort()
    .join("|");
}

function readStoredRequest(): StoredRequest | null {
  if (!canUseSessionStorage()) return null;
  const raw = window.sessionStorage.getItem(DESIGN_SERVICE_REQUEST_STORAGE_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (isStoredRequest(parsed)) return parsed;
  } catch {
    // Remove malformed data below.
  }
  window.sessionStorage.removeItem(DESIGN_SERVICE_REQUEST_STORAGE_KEY);
  return null;
}

function writeStoredRequest(value: StoredRequest) {
  if (canUseSessionStorage()) {
    window.sessionStorage.setItem(DESIGN_SERVICE_REQUEST_STORAGE_KEY, JSON.stringify(value));
  }
}

export function getOrCreateDesignServiceCreationKey(
  userId: number,
  items: readonly DesignServiceRequestItem[]
) {
  const draftKey = designServiceDraftKey(items);
  const stored = readStoredRequest();
  if (stored && stored.user_id === userId && stored.draft_key === draftKey) {
    return stored;
  }

  const next: StoredRequest = {
    version: DESIGN_SERVICE_REQUEST_STORAGE_VERSION,
    user_id: userId,
    draft_key: draftKey,
    creation_key: createKey()
  };
  writeStoredRequest(next);
  return next;
}

export function rememberDesignServiceRequest(
  userId: number,
  items: readonly DesignServiceRequestItem[],
  designRequestId: number
) {
  const stored = getOrCreateDesignServiceCreationKey(userId, items);
  const next: StoredRequest = { ...stored, design_request_id: designRequestId };
  writeStoredRequest(next);
  return next;
}
