"use client";

import { useEffect } from "react";
import {
  ANALYTICS_CONSENT_CHANGED_EVENT,
  pushGtmEvent,
} from "@/lib/analytics";
import type { CheckoutPurchase } from "@/lib/checkout-client";

function purchaseStorageKey(transactionId: string) {
  return `mw:gtm-purchase:${transactionId}`;
}

function hasTrackedPurchase(transactionId: string) {
  return window.localStorage.getItem(purchaseStorageKey(transactionId)) === "1";
}

function markPurchaseTracked(transactionId: string) {
  window.localStorage.setItem(purchaseStorageKey(transactionId), "1");
}

export function ThankYouPurchaseEvent({ purchase }: { purchase: CheckoutPurchase | null | undefined }) {
  useEffect(() => {
    if (!purchase?.transaction_id) {
      return;
    }

    const trackPurchase = () => {
      if (hasTrackedPurchase(purchase.transaction_id)) {
        return;
      }

      if (
        pushGtmEvent({
          event: "purchase",
          ecommerce: purchase,
        })
      ) {
        markPurchaseTracked(purchase.transaction_id);
      }
    };

    trackPurchase();
    window.addEventListener(ANALYTICS_CONSENT_CHANGED_EVENT, trackPurchase);
    return () => {
      window.removeEventListener(ANALYTICS_CONSENT_CHANGED_EVENT, trackPurchase);
    };
  }, [purchase]);

  return null;
}
