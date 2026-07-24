import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  buildProductGalleryImages,
  getAdjacentProductImageSrc
} from "./product-images.ts";

const product = {
  nombre: "Reja Albany",
  imagen: "https://example.test/main.jpg",
  images: [
    { id: 1, product_id: 1, image_url: "https://example.test/secondary-a.jpg" },
    { id: 2, product_id: 1, image_url: "https://example.test/main.jpg" },
    { id: 3, product_id: 1, image_url: "https://example.test/secondary-b.jpg" }
  ]
};

const images = buildProductGalleryImages(product);
assert.equal(images.length, 3);
assert.deepEqual(images.map((image) => image.src), [
  "https://example.test/main.jpg",
  "https://example.test/secondary-a.jpg",
  "https://example.test/secondary-b.jpg"
]);
assert.equal(images[0].isPrimary, true);
assert.equal(images[1].isPrimary, false);
assert.equal(images[0].alt, "Reja Albany");
assert.equal(images[1].alt, "Vista adicional 1 de Reja Albany");

assert.deepEqual(
  buildProductGalleryImages({
    nombre: "Reja Essex",
    imagen: null,
    images: [{ id: 4, product_id: 2, image_url: "https://example.test/essex.jpg" }]
  }).map((image) => image.src),
  ["https://example.test/essex.jpg"]
);

assert.deepEqual(
  buildProductGalleryImages({ nombre: "Reja sin imagen", imagen: null, images: [] }),
  []
);

assert.equal(getAdjacentProductImageSrc(images, images[0].src, 1), images[1].src);
assert.equal(getAdjacentProductImageSrc(images, images[0].src, -1), images[2].src);
assert.equal(getAdjacentProductImageSrc(images, images[2].src, 1), images[0].src);
assert.equal(getAdjacentProductImageSrc(images, images[1].src, -1), images[0].src);
assert.equal(getAdjacentProductImageSrc(images, "missing", 1), images[1].src);
assert.equal(getAdjacentProductImageSrc([], "missing", 1), "");

const gallerySource = readFileSync(
  new URL("../components/product/ProductGallery.tsx", import.meta.url),
  "utf8"
);
const galleryStyles = readFileSync(new URL("../app/globals.css", import.meta.url), "utf8");
assert.match(gallerySource, /availableImages\.length > 1/);
assert.match(gallerySource, /Mostrar imagen anterior/);
assert.match(gallerySource, /Mostrar imagen siguiente/);
assert.match(gallerySource, /event\.key === "ArrowLeft"/);
assert.match(gallerySource, /event\.key === "ArrowRight"/);
assert.match(gallerySource, /aria-pressed=/);
assert.match(gallerySource, /Imagen no disponible/);
assert.doesNotMatch(gallerySource, /\bfetch\s*\(/);
assert.match(galleryStyles, /\.mw-product-gallery__control\s*{[^}]*width:\s*48px;[^}]*height:\s*48px;/s);
assert.match(galleryStyles, /@media \(max-width: 640px\)[\s\S]*?\.mw-product-gallery__control\s*{[^}]*width:\s*44px;[^}]*height:\s*44px;/);
assert.doesNotMatch(galleryStyles, /\.mw-product-gallery__control[^}]*overflow-x/s);

console.log("25 product gallery assertions passed");
