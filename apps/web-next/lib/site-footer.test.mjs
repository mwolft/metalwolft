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

assert.match(footer, /Próxima ubicación del taller de fabricación/);
assert.match(footer, /Calle Socuéllamos 14, nave 1/);
assert.match(footer, /Venta exclusivamente online · Sin atención presencial al público/);
assert.doesNotMatch(footer, /Carretera de Porzuna/);
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
assert.match(map, /useState\(false\)/);
assert.match(map, /https:\/\/maps\.app\.goo\.gl\/m6hyDrRwTSzptAkDA/);
assert.match(map, /https:\/\/www\.google\.com\/maps\/embed\?pb=/);
assert.match(map, /loading="lazy"/);
assert.match(map, /title="Mapa de la próxima ubicación del taller/);
assert.match(nextConfig, /frame-src 'self' https:\/\/accounts\.google\.com https:\/\/www\.google\.com/);
assert.doesNotMatch(footer, /legacyAdminUrl|showDevelopmentAdminLink|React Admin desarrollo/);

assert.match(
  styles,
  /\.mw-footer__grid\s*{[^}]*grid-template-columns:\s*minmax\(306px, 1\.35fr\) repeat\(4, minmax\(0, 1fr\)\)/s
);
assert.match(styles, /@media \(max-width:\s*1100px\)[\s\S]*?\.mw-footer__grid\s*{[^}]*repeat\(2,/);
assert.match(styles, /@media \(max-width:\s*640px\)[\s\S]*?\.mw-footer__grid\s*{[^}]*grid-template-columns:\s*1fr/);
assert.match(
  styles,
  /\.mw-footer__map-preview\s*{[^}]*grid-column:\s*1 \/ -1;[^}]*width:\s*min\(306px, 100%\)/s
);
assert.match(styles, /\.mw-footer__map-preview button,\s*\.mw-footer__map-preview iframe\s*{[^}]*aspect-ratio:\s*16 \/ 9/s);

assert.match(legal, /href:\s*"\/cambios-politica-cookies"/);
assert.match(changesPolicy, /const PATH = "\/cambios-politica-cookies"/);

const dependencies = {
  ...JSON.parse(packageJson).dependencies,
  ...JSON.parse(packageJson).devDependencies
};
assert.equal(dependencies["lucide-react"], undefined);

console.log("Footer location assertions passed");
