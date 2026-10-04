import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { ABATIBLE_COLLECTION_SLUGS, selectAbatibleCollection } from "./abatible-collection.ts";
import { getProductCatalogType, isLocalCatalogFilter } from "./catalog-types.ts";

assert.deepEqual(ABATIBLE_COLLECTION_SLUGS, [
  "reja-abatible-albany",
  "reja-abatible-cortland",
  "reja-abatible-essex",
  "reja-abatible-idaho",
  "reja-abatible-maryland-para-ventanas",
]);

const products = [
  { id: 1, slug: "reja-fija-albany", opening_type: "fixed" },
  ...ABATIBLE_COLLECTION_SLUGS.map((slug, index) => ({ id: index + 2, slug, opening_type: "hinged" })).reverse(),
  { id: 7, slug: "reja-puerta-albany", opening_type: "fixed" },
];
assert.deepEqual(selectAbatibleCollection(products).map(({ slug }) => slug), ABATIBLE_COLLECTION_SLUGS);
assert.equal(selectAbatibleCollection(products.slice(0, 2)).length, 1);

assert.equal(getProductCatalogType(products[0]), "fixed");
assert.equal(getProductCatalogType(products[1]), "hinged");
assert.equal(getProductCatalogType(products[6]), "door");
assert.equal(getProductCatalogType({ slug: "reja-mascotas-cortland", opening_type: "fixed" }), "pets");
assert.equal(isLocalCatalogFilter("fixed"), true);
assert.equal(isLocalCatalogFilter("door"), true);
assert.equal(isLocalCatalogFilter("pets"), true);
assert.equal(isLocalCatalogFilter("hinged"), false);

const page = readFileSync(new URL("../app/rejas-para-ventanas/abatibles/page.tsx", import.meta.url), "utf8");
const parent = readFileSync(new URL("../app/rejas-para-ventanas/page.tsx", import.meta.url), "utf8");
const nav = readFileSync(new URL("../components/catalog/CatalogTypeNavigation.tsx", import.meta.url), "utf8");
const styles = readFileSync(new URL("../app/globals.css", import.meta.url), "utf8");
const sitemap = readFileSync(new URL("../app/sitemap.ts", import.meta.url), "utf8");

assert.match(page, /Rejas abatibles para ventanas a medida/);
assert.match(page, /Compara 5 rejas abatibles para ventanas fabricadas a medida/);
assert.match(page, /<CatalogTypeNavigation active="hinged" \/>/);
assert.match(page, /selectAbatibleCollection\(await fetchCategoryProducts\("rejas-para-ventanas"\)\)/);
assert.match(page, /href=\{CATEGORY_PATH \+ "\/" \+ product\.slug\}/);
assert.match(page, /<BreadcrumbJsonLd/);
assert.match(parent, /<CatalogTypeFilter>/);
assert.match(parent, /catalogType=\{getProductCatalogType\(product\)\}/);
assert.match(nav, /href=\{COLLECTION_PATH\}/);
assert.match(nav, /href=\{CATEGORY_PATH\} key=\{id\} onClick=\{\(\) => rememberFilter\(id\)\}/);
assert.match(nav, /sessionStorage\.removeItem\(CATALOG_FILTER_STORAGE_KEY\)/);
assert.match(nav, /<button[\s\S]*?onClick=\{\(\) => onFilterChange\(id\)\}/);
assert.doesNotMatch(nav, /\?filter=|new URLSearchParams/);
assert.match(styles, /\.mw-product-grid\[data-filter="fixed"\] > \.mw-product-card/);
assert.match(styles, /\.mw-catalog-type-nav\s*\{[^}]*overflow-x:\s*auto/s);
assert.match(sitemap, /path: "\/rejas-para-ventanas\/abatibles"/);

console.log("Abatible collection assertions passed");
