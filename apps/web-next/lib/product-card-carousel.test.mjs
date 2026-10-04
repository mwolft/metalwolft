import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { buildProductCardImages } from "./product-images.ts";

const product = {
  nombre: "Reja Albany",
  imagen: "https://example.test/main.jpg",
  images: [
    { id: 1, product_id: 1, image_url: "https://example.test/secondary-1.jpg" },
    { id: 2, product_id: 1, image_url: "https://example.test/main.jpg" },
    { id: 3, product_id: 1, image_url: "https://example.test/secondary-2.jpg" },
    { id: 4, product_id: 1, image_url: "https://example.test/secondary-3.jpg" },
    { id: 5, product_id: 1, image_url: "https://example.test/secondary-4.jpg" },
  ],
};

assert.equal(buildProductCardImages({ ...product, images: [] }).length, 1);
assert.deepEqual(buildProductCardImages(product).map(({ src }) => src), [
  "https://example.test/main.jpg",
  "https://example.test/secondary-1.jpg",
  "https://example.test/secondary-2.jpg",
  "https://example.test/secondary-3.jpg",
]);
assert.deepEqual(buildProductCardImages({ ...product, imagen: null, images: [] }), []);

const card = readFileSync(new URL("../components/product/ProductCard.tsx", import.meta.url), "utf8");
const carousel = readFileSync(new URL("../components/product/ProductCardCarousel.tsx", import.meta.url), "utf8");
const styles = readFileSync(new URL("../app/globals.css", import.meta.url), "utf8");
const catalog = readFileSync(new URL("../app/rejas-para-ventanas/page.tsx", import.meta.url), "utf8");
const filters = readFileSync(new URL("../components/catalog/CatalogTypeNavigation.tsx", import.meta.url), "utf8");

assert.match(card, /const hasCarousel = cardImages\.length > 1/);
assert.match(card, /hasCarousel \? \(\s*<ProductCardCarousel images=\{cardImages\} productName=\{productName\} href=\{href\} \/>/);
assert.match(card, /<ProductCardImage alt=\{productName\} src=\{product\.imagen\} \/>/);
assert.match(card, /<Link className="mw-product-card__link" href=\{href\}/);
assert.equal((carousel.match(/<Image\b/g) || []).length, 1);
assert.match(carousel, /src=\{selectedImage\.src\}/);
assert.match(carousel, /href=\{href\}/);
assert.match(carousel, /event\.preventDefault\(\)/);
assert.match(carousel, /event\.pointerType !== "touch"/);
assert.match(carousel, /Math\.abs\(horizontalDistance\) <= Math\.abs\(verticalDistance\)/);
assert.match(carousel, /onPointerCancel=/);
assert.match(carousel, /Imagen anterior de \$\{productName\}/);
assert.match(carousel, /Imagen siguiente de \$\{productName\}/);
assert.match(carousel, /\{hasNavigation \? \(/);
assert.match(carousel, /aria-hidden="true"/);
assert.match(styles, /\.mw-product-card__media\s*\{[^}]*aspect-ratio:\s*9 \/ 10/s);
assert.match(styles, /\.mw-product-card__carousel\s*\{[^}]*touch-action:\s*pan-y/s);
assert.match(styles, /\.mw-product-card__carousel-control\s*\{[^}]*opacity:\s*0;[^}]*pointer-events:\s*none/s);
assert.match(styles, /\.mw-product-card__carousel-dot\[data-active="true"\]\s*\{[^}]*background:\s*var\(--mw-accent\)/s);
assert.match(catalog, /<CatalogTypeFilter>/);
assert.match(filters, /onFilterChange=\{setActive\}/);

console.log("ProductCard carousel assertions passed");
