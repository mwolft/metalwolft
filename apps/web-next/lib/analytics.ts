export const ANALYTICS_CONSENT_STORAGE_KEY = "cookiesConsent";
export const ANALYTICS_CONSENT_CHANGED_EVENT = "mw:analytics-consent-changed";

export type AnalyticsConsent = "all" | "necessary";

type GtmEvent = {
  event: string;
  [key: string]: unknown;
};

type GoogleConsentStorage = "granted" | "denied";

type GoogleConsentSettings = {
  ad_storage: GoogleConsentStorage;
  analytics_storage: GoogleConsentStorage;
  ad_user_data: GoogleConsentStorage;
  ad_personalization: GoogleConsentStorage;
};

declare global {
  interface Window {
    dataLayer?: Array<GtmEvent | IArguments>;
    gtag?: (...args: unknown[]) => void;
    __mwGoogleConsentDefaultSet?: boolean;
  }
}

function googleConsentSettings(storage: GoogleConsentStorage): GoogleConsentSettings {
  return {
    ad_storage: storage,
    analytics_storage: storage,
    ad_user_data: storage,
    ad_personalization: storage
  };
}

function ensureGoogleTagFunction() {
  window.dataLayer = window.dataLayer || [];

  if (!window.gtag) {
    window.gtag = function gtag(..._args: unknown[]) {
      window.dataLayer?.push(arguments);
    };
  }
}

export function applyGoogleConsentMode(consent: AnalyticsConsent) {
  if (typeof window === "undefined") {
    return;
  }

  ensureGoogleTagFunction();

  if (!window.__mwGoogleConsentDefaultSet) {
    window.gtag?.("consent", "default", googleConsentSettings("denied"));
    window.__mwGoogleConsentDefaultSet = true;
  }

  const storage = consent === "all" ? "granted" : "denied";
  window.gtag?.("consent", "update", googleConsentSettings(storage));
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
  applyGoogleConsentMode(consent);
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
