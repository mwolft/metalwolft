import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [paymentStep, paypalForm, styles] = await Promise.all([
  readFile(new URL("../components/cart/CartPaymentStep.tsx", import.meta.url), "utf8"),
  readFile(new URL("../components/cart/PayPalPaymentForm.tsx", import.meta.url), "utf8"),
  readFile(new URL("../app/globals.css", import.meta.url), "utf8")
]);

assert.match(paymentStep, /<PaymentMethodIcon \/>/);
assert.match(paymentStep, /pp_cc_mark_37x23\.jpg/);
assert.match(
  paymentStep,
  /className="mw-payment-method-option mw-payment-method-option--paypal"/
);
assert.match(paymentStep, /aria-pressed=\{paymentMethod === "card"\}/);
assert.match(paymentStep, /aria-pressed=\{paymentMethod === "paypal"\}/);
assert.match(paymentStep, /onClick=\{\(\) => setPaymentMethod\("card"\)\}/);
assert.match(paymentStep, /onClick=\{\(\) => setPaymentMethod\("paypal"\)\}/);
assert.match(paymentStep, /paymentMethod === "paypal" && paypalClientId/);
assert.match(paymentStep, /PayPalScriptProvider/);
assert.match(paymentStep, /components: "buttons,messages"/);
assert.match(paymentStep, /<PayPalMessages/);
assert.match(paymentStep, /function useCompactPayPalMessage\(\)/);
assert.match(paymentStep, /color: isCompactPayPalMessage \? "grayscale" : "black"/);
assert.match(paymentStep, /size: isCompactPayPalMessage \? 10 : 12/);
assert.match(paymentStep, /forceReRender=\{\[isCompactPayPalMessage\]\}/);
assert.equal((paymentStep.match(/<PayPalMessages/g) || []).length, 1);
assert.doesNotMatch(paymentStep, /PayPal Sandbox/);

assert.match(paypalForm, /<PayPalButtons/);
assert.doesNotMatch(paypalForm, /PayPalMessages/);
assert.doesNotMatch(paypalForm, /Flask capture/);
assert.match(
  paypalForm,
  /Pagarás \{formatCurrency\(quote\.total_amount\)\} mediante PayPal\. Tu pedido se confirmará\s+automáticamente cuando el pago se complete\./
);
assert.doesNotMatch(paypalForm, /PayPal Sandbox/);

for (const selector of [
  ".mw-payment-method-option",
  ".mw-payment-method__icon",
  ".mw-payment-method__paypal-logo",
  ".mw-paypal-pay-later"
]) {
  assert.match(styles, new RegExp(`\\${selector}`));
}
assert.match(styles, /--mw-payment-method-height: 48px/);
assert.match(styles, /height: var\(--mw-payment-method-height\)/);
const paymentStylesOffset = styles.lastIndexOf(".mw-payment-methods {");
const mobilePaymentStyles = styles.slice(
  styles.indexOf("@media (max-width: 640px)", paymentStylesOffset),
  styles.indexOf(".mw-stripe-card", paymentStylesOffset)
);
assert.match(mobilePaymentStyles, /\.mw-payment-method-option--paypal/);
assert.doesNotMatch(mobilePaymentStyles, /grid-column: 1 \/ -1/);

console.log("12 cart payment method assertions passed");
