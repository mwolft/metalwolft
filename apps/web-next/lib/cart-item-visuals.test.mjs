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
assert.match(cartView, /<span>Alto<\/span>[\s\S]*?src="\/icons\/alto\.webp"/);
assert.match(cartView, /<span>Ancho<\/span>[\s\S]*?src="\/icons\/ancho\.webp"/);
assert.match(cartView, /<span>Instalación<\/span>[\s\S]*?src="\/icons\/anclaje\.webp"/);
assert.equal((cartView.match(/height=\{35\}/g) || []).length, 3);
assert.equal((cartView.match(/width=\{35\}/g) || []).length, 3);
assert.equal((cartView.match(/alt=""/g) || []).length, 3);
assert.match(cartView, /getColorVisual\(item\.color \?\? ""\)/);
assert.match(cartView, /colorVisual\.swatchClass === "forja"/);
assert.match(cartView, /"--mw-cart-config-color": colorVisual\.hex/);
assert.match(cartView, /aria-hidden="true"[\s\S]*?mw-cart-config__color-swatch/);
assert.match(
  cartView,
  /<dt>Color<\/dt>\s*<dd>[\s\S]*?\{formatColor\(item\.color\)\}[\s\S]*?Acabado: esmalte sintético[\s\S]*?<\/dd>[\s\S]*?mw-cart-config__color-swatch/
);
assert.doesNotMatch(cartView, /src="\/icons\/[^\"]*color/i);
assert.match(cartView, /Longitud tornillos: \$\{screwLength\.toLocaleString\("es-ES"\)\} mm/);
assert.match(cartView, /screwLength > 0/);
assert.doesNotMatch(cartView, /className="mw-cart-config__screws"/);

assert.match(
  styles,
  /\.mw-cart-config__icon,\s*\.mw-cart-config__color-swatch\s*{[^}]*width:\s*35px;[^}]*height:\s*35px;[^}]*flex:\s*0 0 35px;/s
);
assert.match(
  styles,
  /\.mw-cart-config\s*{[^}]*grid-template-columns:\s*minmax\(0, 0\.9fr\)\s*minmax\(0, 0\.9fr\)\s*minmax\(0, 1\.2fr\)\s*minmax\(0, 1fr\);/s
);
assert.match(
  styles,
  /@media \(max-width: 1170px\)\s*{\s*\.mw-cart-config\s*{[^}]*grid-template-columns:\s*repeat\(2, minmax\(0, 1fr\)\);/s
);
assert.match(
  styles,
  /\.mw-cart-steps li::after\s*{[^}]*border-top:\s*1px solid var\(--mw-cart-step-border\);[^}]*border-right:\s*1px solid var\(--mw-cart-step-border\);[^}]*transform:\s*translateY\(-50%\) rotate\(45deg\);/s
);
assert.match(
  styles,
  /\.mw-cart-config__color-swatch\s*{[^}]*border:\s*1px solid[^}]*border-radius:\s*999px;[^}]*background-color:\s*var\(--mw-cart-config-color\);/s
);
assert.match(
  styles,
  /\.mw-cart-config__secondary\s*{[^}]*color:\s*var\(--mw-muted\);[^}]*font-size:\s*0\.74rem;/s
);
assert.match(
  styles,
  /\.mw-configurator-swatch--forja \.mw-configurator-swatch__dot,\s*\.mw-cart-config__color-swatch--forja\s*{[^}]*background-image:/s
);

console.log("27 cart item visual assertions passed");
