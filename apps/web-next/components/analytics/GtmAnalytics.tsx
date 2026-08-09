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
    <Script id="mw-gtm" strategy="afterInteractive">
      {`window.dataLayer = window.dataLayer || [];
(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);})(window,document,'script','dataLayer','${gtmId}');`}
    </Script>
  );
}
