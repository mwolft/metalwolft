"use client";

import { useSearchParams } from "next/navigation";
import { CartDetailsStep } from "@/components/cart/CartDetailsStep";
import { CartPaymentStep } from "@/components/cart/CartPaymentStep";
import { CartView } from "@/components/cart/CartView";

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

export function CartFlow() {
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
        <CartDetailsStep />
      ) : currentStep === "payment" ? (
        <CartPaymentStep />
      ) : (
        <CartView />
      )}
    </>
  );
}
