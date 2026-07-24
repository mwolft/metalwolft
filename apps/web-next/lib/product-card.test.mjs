import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const sources = Object.fromEntries(
  await Promise.all(
    [
      ["card", "../components/product/ProductCard.tsx"],
      ["explicitCategory", "../app/rejas-para-ventanas/page.tsx"],
      ["dynamicCategory", "../app/[category_slug]/page.tsx"],
      ["styles", "../app/globals.css"]
    ].map(async ([name, path]) => [name, await readFile(new URL(path, import.meta.url), "utf8")])
  )
);

assert.match(sources.card, /import Image from "next\/image"/);
assert.match(sources.card, /product\.imagen \? \(/);
assert.match(sources.card, /Imagen no disponible/);
assert.match(sources.card, /product\.h1_seo \|\| product\.nombre/);
assert.match(sources.card, /product\.descripcion_seo\?\.trim\(\)/);
assert.match(sources.card, />\s*Ver modelo\s*</);
assert.match(sources.card, /aria-label={`Ver modelo \$\{productName\}`}/);
assert.equal((sources.card.match(/<Link\b/g) || []).length, 1);
assert.match(sources.card, /fill/);
assert.match(sources.card, /sizes={PRODUCT_IMAGE_SIZES}/);
assert.doesNotMatch(sources.card, /\bprecio(?:_rebajado)?\b/);
assert.doesNotMatch(sources.card, /"use client"/);
assert.doesNotMatch(sources.card, /\bfetch\s*\(|\buseState\s*\(|\buseEffect\s*\(/);

for (const page of [sources.explicitCategory, sources.dynamicCategory]) {
  assert.match(page, /import { ProductCard } from "@\/components\/product\/ProductCard"/);
  assert.match(page, /className="mw-product-grid"/);
  assert.match(page, /<ProductCard href={productHref} key={product\.id} product={product} \/>/);
  assert.doesNotMatch(page, /<article className="mw-card"/);
}

assert.match(
  sources.styles,
  /\.mw-product-grid\s*{[^}]*grid-template-columns:\s*repeat\(auto-fill, minmax\(min\(100%, 280px\), 1fr\)\)/s
);
assert.match(sources.styles, /\.mw-product-card__media\s*{[^}]*aspect-ratio:\s*9 \/ 10/s);
assert.match(sources.styles, /\.mw-product-card__media img\s*{[^}]*object-fit:\s*contain/s);
assert.match(sources.styles, /\.mw-product-card__title\s*{[^}]*-webkit-line-clamp:\s*2/s);
assert.match(sources.styles, /\.mw-product-card__description\s*{[^}]*-webkit-line-clamp:\s*2/s);
assert.match(sources.styles, /\.mw-product-card__cta\s*{[^}]*white-space:\s*nowrap/s);
assert.match(sources.styles, /\.mw-product-card__link:focus-visible/);
assert.match(sources.styles, /@media \(prefers-reduced-motion: reduce\)[\s\S]*?\.mw-product-card/);

console.log("ProductCard catalog assertions passed");
