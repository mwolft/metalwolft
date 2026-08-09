"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  ANALYTICS_CONSENT_CHANGED_EVENT,
  getAnalyticsConsent,
  setAnalyticsConsent
} from "@/lib/analytics";

export function CookieConsentBanner() {
  const [isReady, setIsReady] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    setIsOpen(getAnalyticsConsent() === null);
    setIsReady(true);

    const openSettings = () => {
      setIsOpen(true);
    };

    window.addEventListener(ANALYTICS_CONSENT_CHANGED_EVENT, openSettings);
    return () => {
      window.removeEventListener(ANALYTICS_CONSENT_CHANGED_EVENT, openSettings);
    };
  }, []);

  if (!isReady || !isOpen) {
    return null;
  }

  function saveConsent(consent: "all" | "necessary") {
    setAnalyticsConsent(consent);
    setIsOpen(false);
  }

  return (
    <section aria-labelledby="mw-cookie-consent-title" className="mw-cookie-consent" role="region">
      <div className="mw-cookie-consent__content">
        <p id="mw-cookie-consent-title">
          Usamos cookies anal&iacute;ticas para entender c&oacute;mo se utiliza MetalWolft y mejorar la web.{" "}
          <Link href="/politica-de-cookies">Pol&iacute;tica de cookies</Link>
        </p>
        <div className="mw-cookie-consent__actions">
          <button className="mw-button mw-button--primary" onClick={() => saveConsent("all")} type="button">
            Aceptar
          </button>
          <button className="mw-button mw-button--secondary" onClick={() => saveConsent("necessary")} type="button">
            Rechazar
          </button>
        </div>
      </div>
    </section>
  );
}
