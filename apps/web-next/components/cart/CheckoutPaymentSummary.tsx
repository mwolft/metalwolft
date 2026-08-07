import type { CheckoutQuote } from "@/lib/checkout-client";
import type { CheckoutCustomerDetails } from "@/lib/checkout-details";

function formatCurrency(value: number) {
  return new Intl.NumberFormat("es-ES", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value);
}

export function CheckoutPaymentSummary({
  customerDetails,
  quote
}: {
  customerDetails: CheckoutCustomerDetails;
  quote: CheckoutQuote;
}) {
  return (
    <>
      <div className="mw-checkout-fiscal-summary" aria-label="Identidad de facturación">
        <span>Facturación</span>
        <strong>{customerDetails.legal_name}</strong>
        {customerDetails.tax_id ? <span>{customerDetails.tax_id}</span> : null}
      </div>
      <div className="mw-checkout-totals" aria-live="polite">
        <div className="mw-checkout-total-row">
          <span>Subtotal</span>
          <strong>{formatCurrency(quote.subtotal)}</strong>
        </div>
        <div className="mw-checkout-total-row">
          <span>Envío</span>
          <strong>
            {quote.shipping_cost === 0 ? "GRATIS" : formatCurrency(quote.shipping_cost)}
          </strong>
        </div>
        {quote.discount_amount > 0 ? (
          <div className="mw-checkout-total-row mw-checkout-total-row--discount">
            <span>Descuento {quote.discount_code ? `(${quote.discount_code})` : ""}</span>
            <strong>-{formatCurrency(quote.discount_amount)}</strong>
          </div>
        ) : null}
        <div className="mw-checkout-total-row mw-checkout-total-row--final">
          <span>Total</span>
          <strong>{formatCurrency(quote.total_amount)}</strong>
        </div>
      </div>
    </>
  );
}
