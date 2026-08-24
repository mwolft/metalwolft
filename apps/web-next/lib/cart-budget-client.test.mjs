import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [client, cartView] = await Promise.all([
  readFile(new URL("./cart-budget-client.ts", import.meta.url), "utf8"),
  readFile(new URL("../components/cart/CartView.tsx", import.meta.url), "utf8")
]);

assert.match(client, /"\/api\/cart\/budget\/pdf"/);
assert.match(client, /Authorization: `Bearer \$\{token\}`/);
assert.match(client, /JSON\.stringify\(discountCode \? \{ discount_code: discountCode \} : \{\}\)/);
assert.doesNotMatch(client, /line_total|shipping_cost|total_amount|precio_total/);
assert.match(cartView, /downloadCartBudget\(/);
assert.match(cartView, /loadStoredCheckoutDiscountCode\(\)/);
assert.match(cartView, /Descargar presupuesto en PDF/);
assert.match(cartView, /mw-cart-budget-download/);
assert.match(cartView, /<svg aria-hidden="true"/);
assert.match(cartView, /checkoutQuote !== null/);

console.log("10 cart budget client assertions passed");
