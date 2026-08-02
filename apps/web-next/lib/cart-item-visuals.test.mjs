import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [cartView, styles, configuratorVisuals] = await Promise.all([
  readFile(new URL("../components/cart/CartView.tsx", import.meta.url), "utf8"),
  readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
  readFile(new URL("./configurator-options.ts", import.meta.url), "utf8")
]);

assert.match(configuratorVisuals, /satinado_blanco:\s*\{ hex: "#ffffff" \}/);
assert.match(
  configuratorVisuals,
  /forja_negro:\s*\{ hex: "#1a1a1a", swatchClass: "forja" \}/
);
assert.match(configuratorVisuals, /satinado_verde:\s*\{ hex: "#183022" \}/);
assert.match(configuratorVisuals, /export function getColorVisual/);

assert.match(cartView, /import Image from "next\/image"/);
assert.equal((cartView.match(/<Image/g) || []).length, 3);
assert.match(cartView, /src="\/icons\/alto\.webp"[\s\S]*?<span>Alto<\/span>/);
assert.match(cartView, /src="\/icons\/ancho\.webp"[\s\S]*?<span>Ancho<\/span>/);
assert.match(cartView, /src="\/icons\/anclaje\.webp"[\s\S]*?<span>Instalación<\/span>/);
assert.equal((cartView.match(/alt=""/g) || []).length, 3);
assert.match(cartView, /getColorVisual\(item\.color \?\? ""\)/);
assert.match(cartView, /colorVisual\.swatchClass === "forja"/);
assert.match(cartView, /"--mw-cart-config-color": colorVisual\.hex/);
assert.match(cartView, /aria-hidden="true"[\s\S]*?mw-cart-config__color-swatch/);
assert.match(cartView, /<span>Color<\/span>[\s\S]*?<dd>\{formatColor\(item\.color\)\}<\/dd>/);
assert.doesNotMatch(cartView, /src="\/icons\/[^\"]*color/i);

assert.match(
  styles,
  /\.mw-cart-config__icon,\s*\.mw-cart-config__color-swatch\s*{[^}]*width:\s*20px;[^}]*height:\s*20px;[^}]*flex:\s*0 0 20px;/s
);
assert.match(
  styles,
  /\.mw-cart-config__color-swatch\s*{[^}]*border:\s*1px solid[^}]*border-radius:\s*999px;[^}]*background-color:\s*var\(--mw-cart-config-color\);/s
);
assert.match(
  styles,
  /\.mw-configurator-swatch--forja \.mw-configurator-swatch__dot,\s*\.mw-cart-config__color-swatch--forja\s*{[^}]*background-image:/s
);

console.log("19 cart item visual assertions passed");
