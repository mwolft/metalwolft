import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { runInNewContext } from "node:vm";
import ts from "typescript";

const source = await readFile(new URL("./product-families.ts", import.meta.url), "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS },
}).outputText;
const exports = {};
runInNewContext(compiled, { exports });
const { getProductFamily, getProductAlternativeLinks } = exports;

const variants = (slug) => getProductFamily(slug)?.versions.map(({ version }) => version);
const links = (slug) => getProductAlternativeLinks(slug)?.map(({ label, href }) => [label, href]);

assert.deepEqual(Array.from(variants("reja-fija-albany")), ["fixed", "hinged", "door"]);
assert.equal(getProductFamily("reja-abatible-albany").currentVersion, "hinged");
assert.equal(getProductFamily("reja-puerta-albany").currentVersion, "door");
assert.equal(getProductFamily("reja-abatible-cortland").name, "Cortland");
assert.equal(getProductFamily("reja-puerta-maryland").name, "Maryland");
assert.deepEqual(Array.from(variants("reja-fija-essex")), ["fixed", "hinged"]);
assert.deepEqual(Array.from(variants("reja-fija-idaho")), ["fixed", "hinged"]);
assert.equal(getProductFamily("reja-fija-luton"), null);
assert.equal(getProductAlternativeLinks("reja-fija-luton"), undefined);

assert.deepEqual(Array.from(links("reja-fija-albany"), (entry) => Array.from(entry)), [
  ["También abatible", "/rejas-para-ventanas/reja-abatible-albany"],
  ["También para puerta", "/rejas-para-ventanas/reja-puerta-albany"],
]);
assert.deepEqual(Array.from(links("reja-abatible-albany"), (entry) => Array.from(entry)), [
  ["También fija", "/rejas-para-ventanas/reja-fija-albany"],
  ["También para puerta", "/rejas-para-ventanas/reja-puerta-albany"],
]);
assert.deepEqual(Array.from(links("reja-puerta-albany"), (entry) => Array.from(entry)), [
  ["También fija", "/rejas-para-ventanas/reja-fija-albany"],
  ["También abatible", "/rejas-para-ventanas/reja-abatible-albany"],
]);
assert.deepEqual(Array.from(links("reja-fija-maryland"), (entry) => Array.from(entry)), [
  ["También abatible", "/rejas-para-ventanas/reja-abatible-maryland-para-ventanas"],
  ["También para puerta", "/rejas-para-ventanas/reja-puerta-maryland"],
]);
assert.deepEqual(Array.from(links("reja-fija-essex"), (entry) => Array.from(entry)), [
  ["También abatible", "/rejas-para-ventanas/reja-abatible-essex"],
]);

const [page, card, styles] = await Promise.all([
  readFile(new URL("../app/[category_slug]/[product_slug]/page.tsx", import.meta.url), "utf8"),
  readFile(new URL("../components/product/ProductCard.tsx", import.meta.url), "utf8"),
  readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
]);
assert.match(page, /getProductFamily\(product\.slug\)/);
assert.match(page, /aria-label={`Versiones de \$\{productFamily\.name\}`}/);
assert.match(page, /aria-current="page"/);
assert.match(page, /slug === product\.slug \? \(/);
assert.match(page, /<Link className="mw-product-version-nav__option" href={href}/);
assert.ok(page.indexOf('className="mw-product-version-nav"') < page.indexOf('className="mw-product-purchase-layout"'));
assert.match(card, /<Link className="mw-product-card__link" href={href}/);
assert.match(card, /<\/Link>\s*{variants\.length > 0/);
assert.match(card, /<Link className="mw-product-card__variant mw-product-card__variant--link" href={variant\.href}/);
const cardTree = ts.createSourceFile("ProductCard.tsx", card, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
function assertNoNestedLinks(node, insideLink = false) {
  const isLink = ts.isJsxElement(node) && node.openingElement.tagName.getText(cardTree) === "Link";
  assert.ok(!(insideLink && isLink), "ProductCard must not nest links");
  ts.forEachChild(node, (child) => assertNoNestedLinks(child, insideLink || isLink));
}
assertNoNestedLinks(cardTree);
assert.match(styles, /\.mw-product-card__link::after\s*{[^}]*position:\s*absolute;[^}]*z-index:\s*1;/s);
assert.match(styles, /\.mw-product-card__variant--link\s*{[^}]*z-index:\s*2;[^}]*min-height:\s*36px;/s);
assert.match(styles, /\.mw-product-version-nav__options\s*{[^}]*flex-wrap:\s*wrap;/s);
assert.match(styles, /a\.mw-product-version-nav__option:focus-visible/);

console.log("Product family navigation assertions passed");
