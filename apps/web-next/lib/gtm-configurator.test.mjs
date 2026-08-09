import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [layout, analytics, gtm, configurator] = await Promise.all([
  readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
  readFile(new URL("./analytics.ts", import.meta.url), "utf8"),
  readFile(new URL("../components/analytics/GtmAnalytics.tsx", import.meta.url), "utf8"),
  readFile(new URL("../components/product/ProductConfigurator.tsx", import.meta.url), "utf8")
]);

assert.match(layout, /<GtmAnalytics \/>/);
assert.match(analytics, /ANALYTICS_CONSENT_STORAGE_KEY = "cookiesConsent"/);
assert.match(analytics, /storedConsent === "all"/);
assert.match(analytics, /storedConsent === "necessary" \|\| storedConsent === "essential"/);
assert.match(gtm, /NEXT_PUBLIC_GTM_ID.*GTM-P5Z39HKV/);
assert.match(gtm, /googletagmanager\.com\/gtm\.js/);
assert.match(configurator, /pushGtmEvent\(\{[\s\S]*?event: "calcular_precio"/);
for (const field of [
  "product_name: productName",
  "product_slug: productSlug",
  "height_cm: quote.alto",
  "width_cm: quote.ancho",
  "area_m2: (quote.alto * quote.ancho) / 10_000",
  "final_price: quote.unit_price.toFixed(2)"
]) {
  assert.match(configurator, new RegExp(field.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
}
assert.match(configurator, /lastTrackedQuoteKey/);
assert.doesNotMatch(configurator, /event: "purchase"/);

console.log("13 GTM configurator analytics assertions passed");
