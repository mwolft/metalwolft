import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [home, styles] = await Promise.all([
  readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
  readFile(new URL("../app/globals.css", import.meta.url), "utf8")
]);

const editorialStart = home.indexOf("const HOME_FEATURED_MODELS");
const editorialEnd = home.indexOf("] as const;", editorialStart);
const editorialBlock = home.slice(editorialStart, editorialEnd);
const slugs = [
  "reja-fija-albany",
  "reja-fija-idaho",
  "reja-abatible-essex"
];

assert.ok(editorialStart >= 0 && editorialEnd > editorialStart);
assert.deepEqual(
  slugs.map((slug) => editorialBlock.indexOf(`slug: "${slug}"`)),
  [...slugs].map((slug) => editorialBlock.indexOf(`slug: "${slug}"`)).sort((a, b) => a - b)
);

for (const content of [
  "Minimalista",
  "Robusta",
  "Abatible",
  "Ideal para estilos modernos",
  "Ideal para líneas rectas y robustas",
  "Ideal si necesitas acceso a la ventana"
]) {
  assert.match(editorialBlock, new RegExp(content));
}

assert.match(home, /Encuentra el modelo que mejor encaja con tu vivienda/);
assert.match(
  home,
  /Compara algunos de nuestros modelos más destacados y elige el diseño que mejor encaja\s+con el estilo de tu vivienda\./
);
assert.match(home, /HOME_FEATURED_MODELS\.flatMap/);
assert.match(home, /products\.find\(\(candidate\) => candidate\.slug === editorial\.slug\)/);
assert.match(home, /aria-label={`Ver modelo \$\{product\.title\}`}/);
assert.match(home, />\s*Ver modelo\s*<\/Link>/);
assert.doesNotMatch(home, /Modelo a medida|Más vendido/);
assert.doesNotMatch(home, /^"use client";/);
assert.match(home, /function buildItemListJsonLd/);

assert.match(
  styles,
  /@media \(hover: hover\) and \(pointer: fine\)[\s\S]*?\.mw-home-product-card:hover,[\s\S]*?translateY\(-4px\)/
);
assert.match(styles, /\.mw-home-product-card:hover \.mw-home-product-card__media img,[\s\S]*?scale\(1\.02\)/);
assert.match(
  styles,
  /@media \(prefers-reduced-motion: reduce\)[\s\S]*?\.mw-home-product-card__media img[\s\S]*?transition:\s*none/
);
assert.match(styles, /\.mw-home-product-card__body \.mw-actions\s*{[^}]*margin-top:\s*auto/s);

console.log("Home featured products assertions passed");
