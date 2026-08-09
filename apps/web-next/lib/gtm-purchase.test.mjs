import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [status, client, purchase] = await Promise.all([
  readFile(new URL("../components/cart/ThankYouStatus.tsx", import.meta.url), "utf8"),
  readFile(new URL("./checkout-client.ts", import.meta.url), "utf8"),
  readFile(new URL("../components/analytics/ThankYouPurchaseEvent.tsx", import.meta.url), "utf8")
]);

assert.match(status, /statusData\?\.state === "confirmed"/);
assert.match(status, /<ThankYouPurchaseEvent purchase=\{statusData\.purchase\} \/>/);
assert.match(client, /purchase\?: CheckoutPurchase \| null/);
assert.match(client, /transaction_id: string/);
assert.match(client, /currency: "EUR"/);
assert.match(purchase, /event: "purchase"/);
assert.match(purchase, /ecommerce: purchase/);
assert.match(purchase, /mw:gtm-purchase:\$\{transactionId\}/);
assert.match(purchase, /hasTrackedPurchase/);
assert.match(purchase, /markPurchaseTracked/);
assert.match(purchase, /pushGtmEvent/);
assert.match(purchase, /ANALYTICS_CONSENT_CHANGED_EVENT/);
assert.doesNotMatch(purchase, /CartProvider|checkout_summary|total_amount/);

console.log("12 GTM purchase assertions passed");
