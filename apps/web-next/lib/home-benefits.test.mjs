import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [home, styles] = await Promise.all([
  readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
  readFile(new URL("../app/globals.css", import.meta.url), "utf8")
]);

for (const imagePath of [
  "/icons/rejas-para-ventanas-de-seguridad.webp",
  "/icons/estetica-rejas-para-ventanas.webp",
  "/icons/fecha-entrega.webp",
  "/icons/tornilleria-incluida.webp"
]) {
  assert.match(home, new RegExp(`src="${imagePath.replace(".", "\\.")}"`));
}

for (const title of ["Seguridad", "Estética", "Producción optimizada", "Tornillería adaptada"]) {
  assert.match(home, new RegExp(`<h3>${title}</h3>`));
}

assert.doesNotMatch(home, /<h3>Fabricación a medida<\/h3>/);
assert.doesNotMatch(home, /<h3>Opciones de anclaje<\/h3>/);
assert.equal((home.match(/className="mw-home-benefit-card__icon"/g) || []).length, 4);
assert.match(
  styles,
  /\.mw-home-benefit-card__icon\s*{[^}]*width:\s*80px;[^}]*height:\s*72px;[^}]*object-fit:\s*contain/s
);
const iconStyles = styles.match(/\.mw-home-benefit-card__icon\s*{([^}]*)}/)?.[1] ?? "";
assert.doesNotMatch(iconStyles, /margin-bottom/);

console.log("Home benefits assertions passed");
