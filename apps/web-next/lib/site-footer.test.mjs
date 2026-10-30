import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [footer, map, styles, nextConfig, packageJson, legal, changesPolicy] = await Promise.all([
  readFile(new URL("../components/layout/SiteFooter.tsx", import.meta.url), "utf8"),
  readFile(new URL("../components/layout/SiteLocationMap.tsx", import.meta.url), "utf8"),
  readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
  readFile(new URL("../next.config.mjs", import.meta.url), "utf8"),
  readFile(new URL("../package.json", import.meta.url), "utf8"),
  readFile(new URL("./legal.ts", import.meta.url), "utf8"),
  readFile(new URL("../app/cambios-politica-cookies/page.tsx", import.meta.url), "utf8")
]);

assert.match(footer, /Taller de fabricación · Ciudad Real/);
assert.match(footer, /Calle Socuéllamos 14, nave 1/);
assert.match(footer, /Próxima ubicación · Venta online · Visitas solo con cita previa/);
assert.doesNotMatch(footer, /Carretera de Porzuna/);
assert.doesNotMatch(footer, /Sin atención presencial/);
assert.match(
  footer,
  /<svg\s+aria-hidden="true"\s+className="mw-footer__brand-location-icon"[\s\S]*?focusable="false"/
);
assert.match(footer, /<path d="M20 10c0 4\.993-[\s\S]*?<circle cx="12" cy="10" r="3"/);

const brandStart = footer.indexOf('className="mw-footer__brand"');
const catalogStart = footer.indexOf('<nav className="mw-footer__section" aria-label=');
const brandBlock = footer.slice(brandStart, catalogStart);
assert.match(brandBlock, /className="mw-footer__brand-location"/);
assert.match(brandBlock, /<SiteLocationMap \/>/);
assert.match(map, /https:\/\/maps\.app\.goo\.gl\/m6hyDrRwTSzptAkDA/);
assert.match(map, /className="mw-footer__map-link"/);
assert.match(map, /Ver ubicación en Google Maps/);
assert.doesNotMatch(map, /useState|<iframe|maps\/embed|<button/);
assert.doesNotMatch(nextConfig, /frame-src [^\n]*https:\/\/www\.google\.com/);
assert.doesNotMatch(footer, /legacyAdminUrl|showDevelopmentAdminLink|React Admin desarrollo/);

assert.match(
  styles,
  /\.mw-footer__grid\s*{[^}]*grid-template-columns:\s*minmax\(280px, 1\.15fr\) repeat\(2, minmax\(0, 0\.8fr\)\) minmax\(200px, 1fr\) minmax\(150px, 0\.85fr\)/s
);
assert.match(styles, /\.mw-footer__links a\[href\^="mailto:"\]\s*{[^}]*white-space:\s*nowrap/s);
assert.match(styles, /@media \(max-width:\s*1100px\)[\s\S]*?\.mw-footer__grid\s*{[^}]*repeat\(2,/);
assert.match(styles, /@media \(max-width:\s*640px\)[\s\S]*?\.mw-footer__grid\s*{[^}]*grid-template-columns:\s*1fr/);
assert.match(
  styles,
  /\.mw-footer__map-link\s*{[^}]*grid-column:\s*2;[^}]*display:\s*inline-flex/s
);
assert.match(styles, /\.mw-footer__map-link:hover,\s*\.mw-footer__map-link:focus-visible\s*{[^}]*outline:\s*2px solid #ffffff/s);

assert.match(legal, /href:\s*"\/cambios-politica-cookies"/);
assert.match(changesPolicy, /const PATH = "\/cambios-politica-cookies"/);

const dependencies = {
  ...JSON.parse(packageJson).dependencies,
  ...JSON.parse(packageJson).devDependencies
};
assert.equal(dependencies["lucide-react"], undefined);

console.log("Footer location assertions passed");
