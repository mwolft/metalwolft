import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const article = readFileSync(
  new URL("../app/instalation-rejas-para-ventanas/page.tsx", import.meta.url),
  "utf8"
);
const blog = readFileSync(new URL("./blog.ts", import.meta.url), "utf8");
const styles = readFileSync(new URL("../app/globals.css", import.meta.url), "utf8");

assert.match(blog, /slug: "instalation-rejas-para-ventanas"/);
assert.match(blog, /title: "Guía de instalación y manipulación de rejas para ventanas"/);
assert.match(
  blog,
  /metadataTitle: "Guía de instalación y manipulación de rejas para ventanas \| MetalWolft"/
);
assert.match(
  blog,
  /metadataDescription:\s*"Guía práctica para desembalar, manipular e instalar una reja para ventana: comprobaciones previas, anclajes, tornillería, fijación y revisión final\."/
);

for (const heading of [
  "Índice de instalación",
  "Revisa la reja antes de instalar",
  "Desembalaje y protección del acabado",
  "Cómo manipular la reja",
  "Instalación paso a paso",
  "Diferencias según el anclaje",
  "Revisión final después de instalar"
]) {
  assert.match(article, new RegExp(`<h2(?:[^>]*)?>${heading}</h2>`));
}

for (const href of [
  "/medir-hueco-rejas-para-ventanas",
  "/recepcion-pedidos-revisar-antes-firmar",
  "/politica-devolucion",
  "/formulario-incidencias",
  "/mantenimiento-acabado-rejas-metalicas",
  "/rejas-para-ventanas",
  "/rejas-para-ventanas-sin-obra"
]) {
  assert.match(article, new RegExp(`href="${href}"`));
}

assert.match(article, /Mantén el perfil protector inferior durante la presentación y colocación\./);
assert.match(article, /Una vez instalada y correctamente fijada la reja, retira el protector inferior\./);
assert.match(article, /Este sistema no utiliza tornillería y requiere fijación mediante obra\./);
assert.match(article, /La opción estándar utiliza\s+tornillos de 80 mm/);
assert.match(article, /La opción estándar\s+utiliza tornillos de 70 mm/);
assert.match(article, /tornillos de 150 mm/);
assert.match(article, /acabado con esmalte sintético antioxidante/);
assert.match(article, /Si el\s+esmalte se ha dañado, especialmente cuando deja el acero expuesto/i);
assert.match(article, /<video className="mw-video" controls>/);
assert.doesNotMatch(article, /lacado|termolacado|pintura al horno|Publicaremos una guía/i);
assert.match(styles, /\.mw-installation-toc/);
assert.match(styles, /\.mw-installation-callout/);

console.log("Installation guide contract assertions passed");
