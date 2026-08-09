"use client";

import { ANALYTICS_CONSENT_CHANGED_EVENT } from "@/lib/analytics";

export function CookieConsentSettingsButton() {
  return (
    <button
      className="mw-footer__cookie-settings"
      onClick={() => window.dispatchEvent(new Event(ANALYTICS_CONSENT_CHANGED_EVENT))}
      type="button"
    >
      Configurar cookies
    </button>
  );
}
