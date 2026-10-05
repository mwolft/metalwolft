import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const guide = readFileSync(new URL("../components/catalog/NeedBasedProductGuide.tsx", import.meta.url), "utf8");
const filter = readFileSync(new URL("../components/catalog/CatalogTypeNavigation.tsx", import.meta.url), "utf8");
const page = readFileSync(new URL("../app/rejas-para-ventanas/page.tsx", import.meta.url), "utf8");
const styles = readFileSync(new URL("../app/globals.css", import.meta.url), "utf8");

const titles = [
  "No necesito abrirla",
  "Necesito poder abrirla",
  "Quiero evitar obra",
  "Quiero proteger a mi mascota",
];
assert.deepEqual(
  [...guide.matchAll(/title: "([^"]+)"/g)].map((match) => match[1]),
  titles
);
assert.match(guide, /¿Qué tipo de reja necesito\?/);
assert.match(guide, /Cada ventana y cada uso pueden necesitar una solución diferente\. Elige tu caso y te ayudamos a encontrar la opción adecuada\./);
assert.match(guide, /href: "\/rejas-para-ventanas\/abatibles"/);
assert.match(guide, /href: "\/rejas-para-ventanas-sin-obra"/);
assert.match(guide, /href: "\/rejas-para-ventanas\/reja-mascotas-ohio"/);
assert.match(guide, /<Link className="mw-need-guide__option" href=\{option\.href\}>/);
assert.match(guide, /<button className="mw-need-guide__option" type="button" aria-controls="catalog-product-grid" onClick=\{onSelectFixed\}>/);
assert.match(guide, /<aside className="mw-panel mw-need-guide" aria-labelledby="mw-need-guide-title">/);
assert.doesNotMatch(guide, /\?filter=|new URLSearchParams|window\.location|<ProductCard|<Image\b/);

assert.match(page, /<CatalogFilterProvider>/);
assert.match(page, /<CatalogTypeFilter>/);
assert.match(page, /<section className="mw-hero">[\s\S]*<NeedBasedProductGuide \/>[\s\S]*<\/section>/);
assert.equal(page.match(/<NeedBasedProductGuide \/>/g)?.length, 1);
assert.ok(page.indexOf("<NeedBasedProductGuide />") < page.indexOf('id="modelos-reales"'));
assert.doesNotMatch(page, /Resumen de compra|Resumen de la landing/);
assert.match(page, /<h2>Cómo elegir el diseño de tu reja<\/h2>/);
assert.match(page, /Al comparar los modelos, fíjate en la distribución de los barrotes/);
assert.doesNotMatch(page, /El modelo que elijas se fabricará adaptado a las medidas/);
assert.match(filter, /setActive\("fixed"\)/);
assert.match(filter, /fixedButtonRef\.current\?\.focus\(\{ preventScroll: true \}\)/);
assert.match(filter, /navRef\.current\?\.scrollIntoView/);
assert.match(filter, /prefers-reduced-motion: reduce/);
assert.match(filter, /\? "instant" : "smooth"/);
assert.match(filter, /aria-pressed=\{active === id\}/);
assert.match(filter, /data-filter=\{active\} id="catalog-product-grid"/);
assert.match(filter, /<CatalogFilterContext\.Provider value=\{\{ active, setActive, navRef, fixedButtonRef, showFixedProducts \}\}>/);
assert.match(guide, /useShowFixedProducts\(\)/);
assert.match(styles, /\.mw-need-guide__grid li \+ li\s*\{[^}]*border-top:\s*1px solid var\(--mw-border\)/s);
assert.match(styles, /\.mw-need-guide__option\s*\{[^}]*width:\s*100%;[^}]*background:\s*transparent/s);
assert.match(styles, /\.mw-need-guide__option:focus-visible\s*\{[^}]*outline:\s*3px solid var\(--mw-accent\)/s);

console.log("Need-based product guide assertions passed");
