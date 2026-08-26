import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [category, styles, marketing, productCard] = await Promise.all([
  readFile(new URL("../app/rejas-para-ventanas/page.tsx", import.meta.url), "utf8"),
  readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
  readFile(new URL("./design-service-marketing.ts", import.meta.url), "utf8"),
  readFile(new URL("../components/product/ProductCard.tsx", import.meta.url), "utf8")
]);

const catalogStart = category.indexOf('<div className="mw-product-grid">');
const catalogEnd = category.indexOf("</section>", catalogStart);
const catalogBlock = category.slice(catalogStart, catalogEnd);

assert.ok(catalogStart >= 0 && catalogEnd > catalogStart);
assert.match(catalogBlock, /data\.products\.map\(\(product, index\)/);
assert.match(catalogBlock, /index === 5/);
assert.equal((catalogBlock.match(/className="mw-category-design-service"/g) || []).length, 1);
assert.match(catalogBlock, /Comparar con diseño previo/);
assert.match(catalogBlock, /href="\/diseno-previo"/);
assert.match(catalogBlock, /¿Dudas entre varios modelos\?/);
assert.match(catalogBlock, /Descuento al añadir varios diseños/);
assert.doesNotMatch(catalogBlock, /producto=|ancho=|alto=|anclaje|color|torniller[ií]a|price=/i);
assert.match(category, /DESIGN_SERVICE_MARKETING/);
assert.match(marketing, /startingPrice: "Desde 24,95 € IVA incluido"/);
assert.doesNotMatch(category, /requestDesignServiceQuote/);
assert.match(styles, /\.mw-category-design-service\s*{[^}]*grid-column:\s*1 \/ -1/s);
assert.match(styles, /\.mw-category-design-service[\s\S]*?grid-template-columns:\s*1fr/s);
assert.match(productCard, /Ver modelo/);
assert.doesNotMatch(productCard, /Diseño previo/);

console.log("15 category design service assertions passed");
