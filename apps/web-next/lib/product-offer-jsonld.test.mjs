import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [productPage, categoryPage] = await Promise.all([
  readFile(new URL("../app/[category_slug]/[product_slug]/page.tsx", import.meta.url), "utf8"),
  readFile(new URL("../app/[category_slug]/page.tsx", import.meta.url), "utf8")
]);

assert.match(productPage, /function buildProductJsonLd\(product: ApiProduct\)/);
assert.match(productPage, /offers:\s*\{[\s\S]*?"@type": "Offer"/);
assert.match(productPage, /priceCurrency: "EUR"/);
assert.match(productPage, /price: product\.precio_rebajado \?\? product\.precio/);
assert.match(productPage, /product\.available_for_sale[\s\S]*?https:\/\/schema\.org\/InStock[\s\S]*?https:\/\/schema\.org\/OutOfStock/);
assert.match(productPage, /offers:[\s\S]*?url: absoluteUrl\(canonicalPath\)/);
assert.doesNotMatch(productPage, /aggregateRating|review:/);
assert.doesNotMatch(categoryPage, /"@type": "Offer"/);

console.log("8 product Offer JSON-LD assertions passed");
