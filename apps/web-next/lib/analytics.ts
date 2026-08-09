export const ANALYTICS_CONSENT_STORAGE_KEY = "cookiesConsent";
export const ANALYTICS_CONSENT_CHANGED_EVENT = "mw:analytics-consent-changed";

export type AnalyticsConsent = "all" | "necessary";

type GtmEvent = {
  event: string;
  [key: string]: unknown;
};

declare global {
  interface Window {
    dataLayer?: GtmEvent[];
  }
}

export function getAnalyticsConsent(): AnalyticsConsent | null {
  if (typeof window === "undefined") {
    return null;
  }

  const storedConsent = window.localStorage.getItem(ANALYTICS_CONSENT_STORAGE_KEY);
  if (storedConsent === "all") {
    return "all";
  }

  // "essential" was the legacy opt-out value.
  if (storedConsent === "necessary" || storedConsent === "essential") {
    return "necessary";
  }

  return null;
}

export function hasAnalyticsConsent() {
  return getAnalyticsConsent() === "all";
}

export function setAnalyticsConsent(consent: AnalyticsConsent) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(ANALYTICS_CONSENT_STORAGE_KEY, consent);
  const storage = consent === "all" ? "granted" : "denied";
  window.dataLayer = window.dataLayer || [];
  window.dataLayer.push({
    event: "consent_update",
    ad_storage: storage,
    analytics_storage: storage,
    ad_user_data: storage,
    ad_personalization: storage
  });
  window.dispatchEvent(new Event(ANALYTICS_CONSENT_CHANGED_EVENT));
}

export function pushGtmEvent(event: GtmEvent) {
  if (!hasAnalyticsConsent()) {
    return false;
  }

  window.dataLayer = window.dataLayer || [];
  window.dataLayer.push(event);
  return true;
}
