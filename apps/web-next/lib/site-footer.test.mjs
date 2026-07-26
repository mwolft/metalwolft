import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [footer, styles, packageJson] = await Promise.all([
  readFile(new URL("../components/layout/SiteFooter.tsx", import.meta.url), "utf8"),
  readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
  readFile(new URL("../package.json", import.meta.url), "utf8")
]);

for (const content of [
  "Ubicación",
  "Carretera de Porzuna, km 1,8",
  "13005 · Ciudad Real",
  "Castilla-La Mancha · España",
  "Fabricamos y enviamos pedidos a toda España desde nuestro taller de Ciudad Real.",
  "Ver ubicación en Google Maps"
]) {
  assert.match(footer, new RegExp(content.replace(".", "\\.")));
}

assert.match(footer, /href="https:\/\/maps\.app\.goo\.gl\/jG5SvHQvDozB4puc7"/);
assert.match(footer, /rel="noopener noreferrer"/);
assert.match(footer, /target="_blank"/);
assert.match(footer, /<svg[\s\S]*?aria-hidden="true"[\s\S]*?focusable="false"[\s\S]*?className="mw-footer__location-icon"|<svg[\s\S]*?className="mw-footer__location-icon"[\s\S]*?focusable="false"/);
assert.match(footer, /<path d="M20 10c0 4\.993-[\s\S]*?<circle cx="12" cy="10" r="3"/);

const contactPosition = footer.indexOf('>Contacto<');
const locationPosition = footer.indexOf('>Ubicación<');
const legalPosition = footer.indexOf('>Legales<');
assert.ok(contactPosition < locationPosition && locationPosition < legalPosition);

assert.match(
  styles,
  /\.mw-footer__grid\s*{[^}]*grid-template-columns:\s*minmax\(0, 1\.35fr\) repeat\(5, minmax\(0, 1fr\)\)/s
);
assert.match(styles, /@media \(max-width:\s*900px\)[\s\S]*?\.mw-footer__grid\s*{[^}]*repeat\(2,/);
assert.match(styles, /@media \(max-width:\s*640px\)[\s\S]*?\.mw-footer__grid\s*{[^}]*grid-template-columns:\s*1fr/);

const dependencies = {
  ...JSON.parse(packageJson).dependencies,
  ...JSON.parse(packageJson).devDependencies
};
assert.equal(dependencies["lucide-react"], undefined);

console.log("Site footer assertions passed");
