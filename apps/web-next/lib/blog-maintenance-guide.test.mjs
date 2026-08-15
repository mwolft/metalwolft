import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const article = readFileSync(
  new URL("../app/mantenimiento-retoque-rejas-metalicas/page.tsx", import.meta.url),
  "utf8"
);
const blog = readFileSync(new URL("./blog.ts", import.meta.url), "utf8");
const sitemap = readFileSync(new URL("../app/sitemap.ts", import.meta.url), "utf8");
const installationGuide = readFileSync(
  new URL("../app/instalation-rejas-para-ventanas/page.tsx", import.meta.url),
  "utf8"
);

assert.match(blog, /slug: "mantenimiento-retoque-rejas-metalicas"/);
assert.match(blog, /title: "Mantenimiento y retoque del acabado de rejas metálicas"/);
assert.match(blog, /metadataTitle: "Mantenimiento y retoque de rejas metálicas \| MetalWolft"/);
assert.match(
  blog,
  /metadataDescription:\s*"Cómo limpiar, revisar y retocar pequeños roces, desconchados o puntos localizados de corrosión en rejas metálicas con acabado de esmalte sintético antioxidante\."/
);
assert.match(
  sitemap,
  /\{ path: "\/mantenimiento-retoque-rejas-metalicas", changeFrequency: "monthly", priority: 0\.75 \}/
);

for (const heading of [
  "Índice de mantenimiento",
  "Antes de intervenir",
  "Limpieza ordinaria",
  "Revisión periódica",
  "Retoque de un pequeño roce o desconchado",
  "Acero expuesto y corrosión localizada",
  "Protección durante obras posteriores",
  "Preguntas frecuentes"
]) {
  assert.match(article, new RegExp(`<h2(?:[^>]*)?>${heading}</h2>`));
}

for (const href of [
  "/instalation-rejas-para-ventanas",
  "/recepcion-pedidos-revisar-antes-firmar",
  "/politica-devolucion",
  "/formulario-incidencias",
  "/rejas-para-ventanas"
]) {
  assert.match(article, new RegExp(`href="${href}"`));
}

assert.match(article, /No intervenir todavía/);
assert.match(article, /P320–P400/);
assert.match(article, /elimina completamente el polvo/i);
assert.match(article, /superficie debe quedar limpia y seca/i);
assert.match(article, /TITAN Oxirón/);
assert.match(article, /esmalte de retoque correspondiente al color y acabado\s+original de la reja/i);
assert.match(article, /directo sobre acero u óxido/);
assert.match(article, /¿Por qué conviene retocar un pequeño desconchado\?/);
assert.match(article, /protege el acero frente a la exposición ambiental/i);
assert.match(article, /No\. Es un acabado liso\./);
assert.match(article, /frecuencia de revisión dependerá de la exposición, el entorno y el uso de la reja/i);
assert.match(article, /Contacta con MetalWolft para\s+valorar el estado antes de intervenir\./);
assert.doesNotMatch(article, /lacado|termolacado|pintura al horno|No se debe fijar una periodicidad artificial/i);
assert.match(installationGuide, /href="\/mantenimiento-retoque-rejas-metalicas"/);

console.log("Maintenance guide contract assertions passed");
