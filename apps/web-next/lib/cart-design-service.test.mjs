import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [cartView, cartClient, marketing, styles] = await Promise.all([
  readFile(new URL("../components/cart/CartView.tsx", import.meta.url), "utf8"),
  readFile(new URL("./cart-client.ts", import.meta.url), "utf8"),
  readFile(new URL("./design-service-marketing.ts", import.meta.url), "utf8"),
  readFile(new URL("../app/globals.css", import.meta.url), "utf8")
]);

assert.match(cartView, /buildDesignServiceSeedHref/);
assert.match(cartView, /product_slug: item\.slug/);
assert.match(cartView, /width_cm: item\.ancho/);
assert.match(cartView, /height_cm: item\.alto/);
assert.match(cartView, /\}, "cart"\);/);
assert.match(cartView, /¿Quieres verla antes de encargarla\?/);
assert.match(cartView, /Diseño previo \{designPreviewDimensions\}/);
assert.match(cartView, /Preparar diseño previo/);
assert.match(cartView, /mw-cart-design-preview__separator/);
assert.match(cartView, /DESIGN_SERVICE_MARKETING\.startingPrice\.replace/);
assert.doesNotMatch(cartView, /Descuento al añadir varios/);
assert.doesNotMatch(cartView, /mw-cart-design-preview__icon/);
assert.match(cartView, /item\.line_type !== undefined && item\.line_type !== "physical"/);
assert.match(cartClient, /line_type\?: "physical" \| "design_service"/);
assert.doesNotMatch(cartView, /requestDesignServiceQuote|createDesignServiceRequest|DesignRequest/);
assert.match(styles, /\.mw-cart-design-preview\s*{[^}]*padding:\s*0;[^}]*border:\s*0;[^}]*background:\s*transparent;/s);
assert.doesNotMatch(styles, /\.mw-cart-design-preview__icon/);
assert.match(styles, /\.mw-cart-design-preview__heading\s*{[^}]*gap:\s*0\.4rem;/s);
assert.match(styles, /\.mw-cart-design-preview__separator\s*{[^}]*color:\s*var\(--mw-muted\);/s);
assert.match(styles, /\.mw-cart-design-preview__link:focus-visible/);

console.log("13 cart design service assertions passed");
