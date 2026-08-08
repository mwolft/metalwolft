import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [configurator, legacyConfigurator, discountForm, styles] = await Promise.all([
  readFile(new URL("../components/product/ProductConfigurator.tsx", import.meta.url), "utf8"),
  readFile(new URL("../../../src/front/js/pages/ProductDetail.jsx", import.meta.url), "utf8"),
  readFile(new URL("../components/cart/CheckoutDiscountForm.tsx", import.meta.url), "utf8"),
  readFile(new URL("../app/globals.css", import.meta.url), "utf8")
]);

assert.doesNotMatch(configurator, /[ÁA]rea\s*&lt;\s*1\s*m/);
assert.doesNotMatch(configurator, /incrementa coste/i);
assert.doesNotMatch(legacyConfigurator, /[ÁA]rea\s*&lt;\s*1\s*m/);
assert.doesNotMatch(legacyConfigurator, /incrementa coste/i);
assert.match(discountForm, /className="mw-discount-form"/);
assert.match(discountForm, /htmlFor="checkout-discount-code"/);
assert.match(discountForm, /type="submit"/);
assert.match(styles, /\.mw-discount-form\s*{[^}]*gap:\s*0\.45rem;[^}]*padding:\s*0\.7rem;/s);
assert.match(styles, /\.mw-discount-form \.mw-field input\s*{[^}]*min-height:\s*40px;[^}]*font-size:\s*0\.9rem;/s);
assert.match(styles, /\.mw-discount-form__actions \.mw-button\s*{[^}]*min-height:\s*40px;[^}]*font-size:\s*0\.84rem;/s);

console.log("11 checkout discount UI assertions passed");
