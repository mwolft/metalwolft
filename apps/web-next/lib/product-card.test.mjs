import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const sources = Object.fromEntries(
  await Promise.all(
    [
      ["card", "../components/product/ProductCard.tsx"],
      ["image", "../components/product/ProductCardImage.tsx"],
      ["explicitCategory", "../app/rejas-para-ventanas/page.tsx"],
      ["dynamicCategory", "../app/[category_slug]/page.tsx"],
      ["styles", "../app/globals.css"]
    ].map(async ([name, path]) => [name, await readFile(new URL(path, import.meta.url), "utf8")])
  )
);

assert.match(sources.card, /import { ProductCardImage }/);
assert.match(sources.card, /<ProductCardImage alt={productName} src={product\.imagen} \/>/);
assert.match(sources.card, /product\.h1_seo \|\| product\.nombre/);
assert.match(sources.card, /product\.descripcion_seo\?\.trim\(\)/);
assert.match(sources.card, />\s*Ver modelo\s*</);
assert.match(sources.card, /aria-label={`Ver modelo \$\{productName\}`}/);
assert.equal((sources.card.match(/<Link\b/g) || []).length, 1);
assert.doesNotMatch(sources.card, /\bprecio(?:_rebajado)?\b/);
assert.doesNotMatch(sources.card, /"use client"/);
assert.doesNotMatch(sources.card, /\bfetch\s*\(|\buseState\s*\(|\buseEffect\s*\(/);

assert.match(sources.image, /^"use client";/);
assert.match(sources.image, /import Image from "next\/image"/);
assert.match(sources.image, /if \(!src \|\| failed\)/);
assert.match(sources.image, /Imagen no disponible/);
assert.match(sources.image, /role="img"/);
assert.match(sources.image, /fill/);
assert.match(sources.image, /sizes={PRODUCT_IMAGE_SIZES}/);
assert.match(sources.image, /unoptimized={isAvifUrl\(src\)}/);
assert.match(sources.image, /onError=\{\(\) => setFailed\(true\)\}/);
assert.doesNotMatch(sources.image, /\bfetch\s*\(|\buseEffect\s*\(/);

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
assert.match(sources.styles, /\.mw-product-card__media\s*{[^}]*aspect-ratio:\s*5 \/ 4/s);
assert.match(sources.styles, /\.mw-product-card__media img\s*{[^}]*object-fit:\s*contain/s);
assert.match(sources.styles, /\.mw-product-card__title\s*{[^}]*-webkit-line-clamp:\s*2/s);
assert.match(sources.styles, /\.mw-product-card__description\s*{[^}]*-webkit-line-clamp:\s*2/s);
assert.match(sources.styles, /\.mw-product-card__cta\s*{[^}]*white-space:\s*nowrap/s);
assert.match(sources.styles, /\.mw-product-card__link:focus-visible/);
assert.match(sources.styles, /@media \(prefers-reduced-motion: reduce\)[\s\S]*?\.mw-product-card/);

console.log("ProductCard catalog assertions passed");
