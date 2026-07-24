import assert from "node:assert/strict";
import { buildProductGalleryImages } from "./product-images.ts";

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

console.log("8 product image assertions passed");
