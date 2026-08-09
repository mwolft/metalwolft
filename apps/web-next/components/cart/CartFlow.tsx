"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import { CartDetailsStep } from "@/components/cart/CartDetailsStep";
import { CartView } from "@/components/cart/CartView";
import { DeliveryEstimate } from "@/components/product/DeliveryEstimate";
import { getToken } from "@/lib/auth-client";
import {
  getCartDeliveryEstimate,
  subscribeToCartSnapshotChanges
} from "@/lib/cart-client";
import type { DeliveryEstimate as DeliveryEstimateData } from "@/lib/delivery-estimate";

const CartPaymentStep = dynamic(
  () => import("@/components/cart/CartPaymentStep").then((module) => module.CartPaymentStep),
  { ssr: false }
);

type CartStep = "review" | "details" | "payment";

function normalizeStep(value: string | null): CartStep {
  if (value === "details" || value === "payment") {
    return value;
  }

  return "review";
}

const steps: Array<{ id: CartStep; label: string }> = [
  { id: "review", label: "Carrito" },
  { id: "details", label: "Datos" },
  { id: "payment", label: "Pago" }
];

export function CartFlow({ deliveryEstimate }: { deliveryEstimate: DeliveryEstimateData | null }) {
  const searchParams = useSearchParams();
  const currentStep = normalizeStep(searchParams.get("step"));
  const [contextualEstimate, setContextualEstimate] = useState<DeliveryEstimateData | null>(
    deliveryEstimate
  );

  useEffect(() => {
    const token = getToken();
    if (!token) {
      return;
    }

    let isActive = true;
    const refreshEstimate = async () => {
      try {
        const estimate = await getCartDeliveryEstimate(token);
        if (isActive) {
          setContextualEstimate(estimate);
        }
      } catch {
        // Keep the global estimate when the private cart estimate is unavailable.
      }
    };

    void refreshEstimate();
    return subscribeToCartSnapshotChanges(() => {
      void refreshEstimate();
    });
  }, []);

  const contextualDeliveryEstimate = (
    <DeliveryEstimate estimate={contextualEstimate} variant="compact" />
  );

  return (
    <>
      <nav className="mw-cart-steps" aria-label="Pasos del carrito">
        <ol>
          {steps.map((step, index) => (
            <li
              aria-current={currentStep === step.id ? "step" : undefined}
              className={currentStep === step.id ? "is-current" : undefined}
              key={step.id}
            >
              <span>{index + 1}</span>
              {step.label}
            </li>
          ))}
        </ol>
      </nav>

      {currentStep === "details" ? (
        <CartDetailsStep deliveryEstimate={contextualDeliveryEstimate} />
      ) : currentStep === "payment" ? (
        <CartPaymentStep deliveryEstimate={contextualDeliveryEstimate} />
      ) : (
        <CartView deliveryEstimate={contextualDeliveryEstimate} />
      )}
    </>
  );
}
