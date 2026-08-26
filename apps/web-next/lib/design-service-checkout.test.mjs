import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "..");
const checkoutPage = fs.readFileSync(path.join(root, "app/diseno-previo/checkout/page.tsx"), "utf8");
const checkoutView = fs.readFileSync(
  path.join(root, "components/design-service/DesignServiceCheckoutView.tsx"),
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
assert.match(checkoutView, /No necesitamos dirección de envío/);
assert.match(checkoutView, /Prepararemos el pago seguro en el siguiente paso/);
assert.doesNotMatch(checkoutView, /CartProvider|shipping_cost|delivery_estimate/);
assert.match(builder, /createDesignServiceRequest/);
assert.match(builder, /requestDesignServiceQuote\(validItems\)/);
assert.match(builder, /getOrCreateDesignServiceCreationKey/);
assert.match(builder, /\/diseno-previo\/checkout\?design_request_id=/);

console.log("10 design checkout contract assertions passed");
