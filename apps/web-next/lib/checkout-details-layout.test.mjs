import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const detailsStepSource = readFileSync(
  new URL("../components/cart/CartDetailsStep.tsx", import.meta.url),
  "utf8"
);
const globalStylesSource = readFileSync(
  new URL("../app/globals.css", import.meta.url),
  "utf8"
);

assert.doesNotMatch(detailsStepSource, /Líneas verificadas/);
assert.match(detailsStepSource, /<h2 id="checkout-order-title">Tu pedido<\/h2>/);
assert.equal(
  [...detailsStepSource.matchAll(/mw-checkout-form-section--divided/g)].length,
  2
);
assert.match(globalStylesSource, /\.mw-checkout-form-section--divided\s*{/);
assert.match(
  globalStylesSource,
  /\.mw-checkout-form-section--divided\s*{[^}]*border-top:\s*1px solid/s
);

const formIndex = detailsStepSource.indexOf(
  '<form\n          className="mw-checkout-form"\n          id="mw-checkout-details-form"\n          onSubmit={handleContinueToPayment}\n        >'
);
const policyIndex = detailsStepSource.indexOf(
  '<label className="mw-checkout-option mw-checkout-option--policy">'
);
const orderIndex = detailsStepSource.indexOf(
  '<section className="mw-checkout-order" aria-labelledby="checkout-order-title">'
);
const linesIndex = detailsStepSource.indexOf("<CheckoutLines lines={quote.lines} />");
const submitIndex = detailsStepSource.indexOf(
  '<button\n            className="mw-button mw-button--primary mw-checkout-submit"\n            form="mw-checkout-details-form"\n            type="submit"\n          >'
);
const formEndIndex = detailsStepSource.indexOf("</form>", formIndex);
const summaryIndex = detailsStepSource.indexOf(
  '<aside className="mw-checkout-summary" aria-label="Resumen economico">'
);
const deliveryEstimateIndex = detailsStepSource.indexOf("{deliveryEstimate}");

for (const [label, index] of [
  ["form", formIndex],
  ["policy", policyIndex],
  ["order", orderIndex],
  ["lines", linesIndex],
  ["submit", submitIndex],
  ["form end", formEndIndex],
  ["summary", summaryIndex],
  ["delivery estimate", deliveryEstimateIndex]
]) {
  assert.notEqual(index, -1, `Missing ${label} markup`);
}

assert.ok(formIndex < policyIndex);
assert.ok(policyIndex < orderIndex);
assert.ok(orderIndex < linesIndex);
assert.ok(linesIndex < formEndIndex);
assert.ok(formEndIndex < summaryIndex);
assert.ok(summaryIndex < deliveryEstimateIndex);
assert.ok(deliveryEstimateIndex < submitIndex);

assert.match(detailsStepSource, /Particular \/ autónomo/);
assert.match(detailsStepSource, /value="company"/);
assert.match(detailsStepSource, /function CheckoutLines/);
assert.match(detailsStepSource, /onSubmit={handleContinueToPayment}/);

console.log("Checkout details layout assertions passed");
