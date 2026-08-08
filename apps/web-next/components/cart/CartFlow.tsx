"use client";

import { useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import type { ReactNode } from "react";
import { CartDetailsStep } from "@/components/cart/CartDetailsStep";
import { CartView } from "@/components/cart/CartView";

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

export function CartFlow({ deliveryEstimate }: { deliveryEstimate?: ReactNode }) {
  const searchParams = useSearchParams();
  const currentStep = normalizeStep(searchParams.get("step"));

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
        <CartDetailsStep deliveryEstimate={deliveryEstimate} />
      ) : currentStep === "payment" ? (
        <CartPaymentStep deliveryEstimate={deliveryEstimate} />
      ) : (
        <CartView deliveryEstimate={deliveryEstimate} />
      )}
    </>
  );
}
