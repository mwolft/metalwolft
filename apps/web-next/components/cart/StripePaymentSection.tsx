"use client";

import { Elements } from "@stripe/react-stripe-js";
import { loadStripe } from "@stripe/stripe-js";
import type { CheckoutQuote } from "@/lib/checkout-client";
import type { CheckoutCustomerDetails } from "@/lib/checkout-details";
import { StripePaymentForm } from "@/components/cart/StripePaymentForm";

const stripePublishableKey = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY?.trim();
const stripePromise = stripePublishableKey ? loadStripe(stripePublishableKey) : null;

type StripePaymentSectionProps = {
  customerDetails: CheckoutCustomerDetails;
  discountCode: string | null;
  initialQuote: CheckoutQuote;
  onQuoteUpdated: (quote: CheckoutQuote, requestedDiscountCode?: string | null) => void;
  onSessionExpired: () => void;
};

export function StripePaymentSection({
  customerDetails,
  discountCode,
  initialQuote,
  onQuoteUpdated,
  onSessionExpired
}: StripePaymentSectionProps) {
  if (!stripePromise) {
    return (
      <p className="mw-alert mw-alert--error">
        La clave p&uacute;blica de Stripe no est&aacute; configurada en este entorno.
      </p>
    );
  }

  return (
    <Elements stripe={stripePromise}>
      <StripePaymentForm
        customerDetails={customerDetails}
        discountCode={discountCode}
        initialQuote={initialQuote}
        onQuoteUpdated={onQuoteUpdated}
        onSessionExpired={onSessionExpired}
      />
    </Elements>
  );
}
