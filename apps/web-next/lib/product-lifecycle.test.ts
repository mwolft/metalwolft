import assert from "node:assert/strict";
import {
  PRODUCT_UNAVAILABLE_MESSAGE,
  isAvailableForSale
} from "./product-lifecycle";

assert.equal(isAvailableForSale({ available_for_sale: true }), true);
assert.equal(isAvailableForSale({ available_for_sale: false }), false);
assert.doesNotMatch(
  PRODUCT_UNAVAILABLE_MESSAGE,
  /stock|temporal|próximamente|reposición|avísame/i
);

console.log("3 product lifecycle frontend tests passed");
