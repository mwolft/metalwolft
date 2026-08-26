import assert from "node:assert/strict";
import {
  builderInputsToDraftItems,
  isCompleteDesignServiceBuilderInput
} from "./design-service-builder.ts";

const products = [
  { id: 7, slug: "maryland", name: "Maryland" },
  { id: 8, slug: "vermont", name: "Vermont" }
];

const maryland = { id: "one", product_id: "7", width_cm: "200", height_cm: "120" };

assert.equal(isCompleteDesignServiceBuilderInput(maryland, products), true);
assert.equal(isCompleteDesignServiceBuilderInput({ ...maryland, width_cm: "" }, products), false);

const result = builderInputsToDraftItems(
  [
    maryland,
    { id: "duplicate", product_id: "7", width_cm: "200", height_cm: "120" },
    { id: "second", product_id: "7", width_cm: "150", height_cm: "120" },
    { id: "third", product_id: "8", width_cm: "100", height_cm: "80" }
  ],
  products
);

assert.equal(result.items.length, 3);
assert.equal(result.duplicateInputIds.has("duplicate"), true);
assert.equal(result.duplicateInputIds.has("one"), false);
assert.deepEqual(result.items.map((item) => item.product_name), ["Maryland", "Maryland", "Vermont"]);

console.log("6 design service builder assertions passed");
