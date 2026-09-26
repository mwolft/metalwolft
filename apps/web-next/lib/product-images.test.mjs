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
assert.match(gallerySource, /const SWIPE_THRESHOLD_PX = 50/);
assert.match(gallerySource, /horizontalDistance < 0 \? 1 : -1/);
assert.match(gallerySource, /Math\.abs\(horizontalDistance\) <= Math\.abs\(verticalDistance\)/);
assert.match(gallerySource, /onPointerCancel={resetPointerGesture}/);
assert.match(gallerySource, /suppressNextClick\(\)/);
assert.match(gallerySource, /consumeSuppressedClick\(\)/);
assert.match(gallerySource, /onClick={consumeSuppressedClick}/);
assert.match(gallerySource, /imageRatios\[selectedImage\.src\]/);
assert.match(gallerySource, /style=\{selectedRatio \? \{ aspectRatio: selectedRatio \} : undefined\}/);
assert.match(gallerySource, /event\.currentTarget\.naturalWidth/);
assert.match(gallerySource, /event\.currentTarget\.naturalHeight/);
assert.match(gallerySource, /Math\.min\(MAX_IMAGE_RATIO, Math\.max\(MIN_IMAGE_RATIO, width \/ height\)\)/);
assert.match(gallerySource, /const MIN_IMAGE_RATIO = 0\.65/);
assert.match(gallerySource, /const MAX_IMAGE_RATIO = 2/);
assert.match(gallerySource, /event\.stopPropagation\(\)/);
assert.match(gallerySource, /mw-product-gallery__hit-zone--previous/);
assert.match(gallerySource, /mw-product-gallery__hit-zone--next/);
assert.match(gallerySource, /aria-hidden="true"/);
assert.match(gallerySource, /\{hasNavigation \? \(/);
assert.doesNotMatch(gallerySource, /\bfetch\s*\(/);
assert.match(galleryStyles, /\.mw-product-gallery__control\s*{[^}]*width:\s*48px;[^}]*height:\s*48px;/s);
assert.match(galleryStyles, /\.mw-product-gallery__control\s*{[^}]*border:\s*0;[^}]*background:\s*transparent;[^}]*box-shadow:\s*none;/s);
assert.match(galleryStyles, /\.mw-product-gallery__control svg\s*{[^}]*width:\s*50px;[^}]*height:\s*50px;/s);
assert.match(galleryStyles, /drop-shadow\(/);
assert.match(galleryStyles, /@media \(max-width: 640px\)[\s\S]*?\.mw-product-gallery__control\s*{[^}]*width:\s*44px;[^}]*height:\s*44px;/);
assert.match(galleryStyles, /\.mw-product-gallery__hit-zone\s*{[^}]*width:\s*30%;/s);
assert.match(galleryStyles, /touch-action:\s*pan-y/);
assert.match(galleryStyles, /\.mw-product-gallery__stage\s*\{[^}]*aspect-ratio:\s*9 \/ 10;[^}]*min-height:\s*180px;[^}]*max-height:\s*min\(90vh, 900px\);/s);
assert.match(galleryStyles, /\.mw-product-gallery__stage img,[\s\S]*?object-fit:\s*contain;/);
assert.doesNotMatch(galleryStyles, /\.mw-product-gallery__control[^}]*overflow-x/s);

console.log("Product gallery assertions passed");
