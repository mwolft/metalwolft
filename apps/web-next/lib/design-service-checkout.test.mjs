import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "..");
const checkoutPage = fs.readFileSync(path.join(root, "app/diseno-previo/checkout/page.tsx"), "utf8");
const checkoutView = fs.readFileSync(
  path.join(root, "components/design-service/DesignServiceCheckoutView.tsx"),
  "utf8"
);
const paymentSection = fs.readFileSync(
  path.join(root, "components/design-service/DesignServicePaymentSection.tsx"),
  "utf8"
);
const confirmationPage = fs.readFileSync(
  path.join(root, "app/diseno-previo/confirmado/page.tsx"),
  "utf8"
);
const builder = fs.readFileSync(
  path.join(root, "components/design-service/DesignServiceBuilder.tsx"),
  "utf8"
);

assert.match(checkoutPage, /robots:\s*\{\s*index:\s*false,\s*follow:\s*false\s*\}/);
assert.match(checkoutPage, /design_request_id/);
assert.match(checkoutView, /getDesignServiceCheckoutQuote/);
assert.match(checkoutView, /\/login\?next=/);
assert.match(checkoutView, /Entrega del diseño/);
assert.match(checkoutView, /Enviaremos el diseño terminado a este correo electrónico cuando esté listo/);
assert.match(checkoutView, /DesignServicePaymentSection/);
assert.doesNotMatch(checkoutView, /CartProvider|shipping_cost|delivery_estimate/);
assert.match(paymentSection, /createDesignServiceStripePaymentIntent/);
assert.match(paymentSection, /createDesignServicePayPalOrder/);
assert.match(paymentSection, /No solicitamos dirección de envío/);
assert.match(paymentSection, /Pagar \$\{formatCurrency\(quote\.total_amount/);
assert.match(confirmationPage, /robots:\s*\{ index: false, follow: false \}/);
assert.match(builder, /createDesignServiceRequest/);
assert.match(builder, /requestDesignServiceQuote\(validItems\)/);
assert.match(builder, /getOrCreateDesignServiceCreationKey/);
assert.match(builder, /\/diseno-previo\/checkout\?design_request_id=/);

console.log("10 design checkout contract assertions passed");
