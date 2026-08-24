"use client";

import Script from "next/script";
import { useEffect, useState } from "react";
import {
  ANALYTICS_CONSENT_CHANGED_EVENT,
  hasAnalyticsConsent
} from "@/lib/analytics";

const gtmId = process.env.NEXT_PUBLIC_GTM_ID?.trim() || "GTM-P5Z39HKV";

export function GtmAnalytics() {
  const [isEnabled, setIsEnabled] = useState(false);

  useEffect(() => {
    const updateConsent = () => {
      setIsEnabled(hasAnalyticsConsent());
    };

    updateConsent();
    window.addEventListener(ANALYTICS_CONSENT_CHANGED_EVENT, updateConsent);

    return () => {
      window.removeEventListener(ANALYTICS_CONSENT_CHANGED_EVENT, updateConsent);
    };
  }, []);

  if (!isEnabled || !gtmId) {
    return null;
  }

  return (
    <Script
      id="mw-gtm-bootstrap"
      src="/scripts/gtm-bootstrap.js"
      strategy="afterInteractive"
      data-gtm-id={gtmId}
    />
  );
}
