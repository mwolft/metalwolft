import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const detailsStepSource = readFileSync(
  new URL("../components/cart/CartDetailsStep.tsx", import.meta.url),
  "utf8"
).replace(/\r\n/g, "\n");
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
const validationSummaryIndex = detailsStepSource.indexOf(
  'className="mw-checkout-validation-summary"'
);

for (const [label, index] of [
  ["form", formIndex],
  ["policy", policyIndex],
  ["order", orderIndex],
  ["lines", linesIndex],
  ["submit", submitIndex],
  ["form end", formEndIndex],
  ["summary", summaryIndex],
  ["delivery estimate", deliveryEstimateIndex],
  ["validation summary", validationSummaryIndex]
]) {
  assert.notEqual(index, -1, `Missing ${label} markup`);
}

assert.ok(formIndex < policyIndex);
assert.ok(policyIndex < orderIndex);
assert.ok(orderIndex < linesIndex);
assert.ok(linesIndex < formEndIndex);
assert.ok(formEndIndex < summaryIndex);
assert.ok(summaryIndex < deliveryEstimateIndex);
assert.ok(deliveryEstimateIndex < validationSummaryIndex);
assert.ok(validationSummaryIndex < submitIndex);
assert.ok(deliveryEstimateIndex < submitIndex);

assert.match(detailsStepSource, /Particular \/ autónomo/);
assert.match(detailsStepSource, /value="company"/);
assert.match(detailsStepSource, /function CheckoutLines/);
assert.match(detailsStepSource, /<strong>Alto:<\/strong>/);
assert.match(detailsStepSource, /<strong>Ancho:<\/strong>/);
assert.match(detailsStepSource, /<strong>Instalación:<\/strong>/);
assert.match(
  detailsStepSource,
  /<strong>Tornillos:<\/strong> \{screwLength\.toLocaleString\("es-ES"\)\} mm/
);
assert.match(detailsStepSource, /const hasScrewLength = Number\.isFinite\(screwLength\) && screwLength > 0/);
assert.match(
  detailsStepSource,
  /<strong>Color:<\/strong> \{formatColor\(line\.color\)\} · <strong>Acabado:<\/strong>/
);
assert.match(detailsStepSource, /Esmalte sintético/);
assert.match(
  globalStylesSource,
  /\.mw-checkout-line p\.mw-checkout-line__technical\s*{[^}]*font-size:\s*0\.74rem;[^}]*font-weight:\s*400;/s
);
assert.match(detailsStepSource, /onSubmit={handleContinueToPayment}/);
assert.match(detailsStepSource, /setHasAttemptedContinue\(true\)/);
assert.match(detailsStepSource, /role="alert"/);
assert.match(detailsStepSource, /aria-label="Campos pendientes"/);
assert.doesNotMatch(detailsStepSource, /Revisa estos datos antes de continuar/);
assert.doesNotMatch(detailsStepSource, /mw-checkout-validation-summary__heading/);
assert.match(detailsStepSource, /mw-checkout-validation-summary__icon/);
assert.match(detailsStepSource, /focusCheckoutField\(item\.field\)/);
assert.doesNotMatch(detailsStepSource, /<span className="mw-field-error"/);
assert.match(
  detailsStepSource,
  /hasAttemptedContinue\s*\?\s*validateCheckoutDetails\(details\)\.errors/
);
assert.match(
  detailsStepSource,
  /aria-invalid=\{Boolean\(currentDetailsErrors\.acceptedPolicy\)\}/
);
assert.match(
  globalStylesSource,
  /\.mw-checkout-form \.mw-field input\[aria-invalid="true"\]\s*\{/s
);
assert.match(
  globalStylesSource,
  /\.mw-checkout-form \.mw-checkout-option input\[aria-invalid="true"\]\s*\{/s
);
assert.match(
  globalStylesSource,
  /\.mw-checkout-validation-summary\s*\{[^}]*display:\s*flex;[^}]*align-items:\s*center;[^}]*margin-top:\s*0\.65rem;[^}]*padding:\s*0;/s
);
assert.match(
  globalStylesSource,
  /\.mw-checkout-validation-summary__icon\s*\{[^}]*border-radius:\s*50%;[^}]*background:\s*var\(--mw-accent-dark\);/s
);
assert.doesNotMatch(
  globalStylesSource,
  /\.mw-checkout-validation-summary\s*\{[^}]*\b(?:border|background)\s*:/s
);

console.log("Checkout details layout assertions passed");
