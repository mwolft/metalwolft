import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [home, styles, marketing] = await Promise.all([
  readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
  readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
  readFile(new URL("./design-service-marketing.ts", import.meta.url), "utf8")
]);

const featuredModelsIndex = home.indexOf('id="modelos-destacados"');
const designServiceIndex = home.indexOf('className="mw-section mw-home-design-service"');
const howItWorksIndex = home.indexOf("Comprar una reja a medida es más fácil cuando sigues el orden correcto");
const designServiceBlock = home.slice(designServiceIndex, howItWorksIndex);

assert.ok(featuredModelsIndex >= 0 && designServiceIndex > featuredModelsIndex);
assert.ok(howItWorksIndex > designServiceIndex);
assert.match(designServiceBlock, /Diseño previo a medida/);
assert.match(designServiceBlock, /Visualiza tu reja antes de encargarla/);
assert.match(designServiceBlock, /Preparar mi diseño/);
assert.match(designServiceBlock, /href="\/diseno-previo"/);
assert.match(designServiceBlock, /No es un plano técnico ni una simulación exacta de la instalación\./);
assert.match(designServiceBlock, /src="\/icons\/diseno-previo-rejas\.webp"/);
assert.doesNotMatch(designServiceBlock, /producto=|ancho=|alto=|checkout|payment|cart/i);
assert.match(marketing, /startingPrice: "Desde 24,95 € IVA incluido"/);
assert.match(styles, /\.mw-home-design-service__box\s*{[^}]*grid-template-columns:/s);
assert.match(styles, /\.mw-home-design-service__box[\s\S]*?grid-template-columns:\s*1fr/s);

console.log("12 home design service assertions passed");
