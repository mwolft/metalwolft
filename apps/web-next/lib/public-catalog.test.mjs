import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { isPublicCatalogCategory } from "./public-catalog.ts";

const retiredCategories = [
  "vallados-metalicos-exteriores",
  "puertas-peatonales-metalicas",
  "puertas-correderas-interiores",
  "puertas-correderas-exteriores",
  "cerramientos-de-cocina-con-cristal"
];

assert.equal(isPublicCatalogCategory("rejas-para-ventanas"), true);
for (const slug of retiredCategories) {
  assert.equal(isPublicCatalogCategory(slug), false);
}

for (const page of [
  "../app/[category_slug]/page.tsx",
  "../app/[category_slug]/[product_slug]/page.tsx",
  "../app/sitemap.ts"
]) {
  assert.match(readFileSync(new URL(page, import.meta.url), "utf8"), /isPublicCatalogCategory\(/);
}

const sitemap = readFileSync(new URL("../../../static/sitemap.xml", import.meta.url), "utf8");
const urls = Array.from(sitemap.matchAll(/<loc>(https:\/\/www\.metalwolft\.com\/[^<]+)<\/loc>/g), (match) => match[1]);
const productUrls = urls.filter((url) => url.includes("/rejas-para-ventanas/"));

assert.equal(productUrls.length, 28);
assert.equal(urls.some((url) => url.endsWith("/reja-fija-delhi")), false);
assert.equal(retiredCategories.some((slug) => urls.some((url) => url.includes(`/${slug}`))), false);
for (const slug of ["albany", "cortland", "essex", "maryland"]) {
  assert.equal(productUrls.some((url) => url.endsWith(`/reja-puerta-${slug}`)), true);
}

console.log("Public catalog routing and sitemap assertions passed");
