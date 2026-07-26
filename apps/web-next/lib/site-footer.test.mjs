import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [footer, styles, packageJson, legal, changesPolicy, mapThumbnail] = await Promise.all([
  readFile(new URL("../components/layout/SiteFooter.tsx", import.meta.url), "utf8"),
  readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
  readFile(new URL("../package.json", import.meta.url), "utf8"),
  readFile(new URL("./legal.ts", import.meta.url), "utf8"),
  readFile(new URL("../app/cambios-politica-cookies/page.tsx", import.meta.url), "utf8"),
  readFile(new URL("../public/metalwolft-location-map.jpg", import.meta.url))
]);

for (const content of [
  "Carretera de Porzuna, km 1,8",
  "13005 Ciudad Real · España"
]) {
  assert.match(footer, new RegExp(content.replace(".", "\\.")));
}

assert.match(footer, /href="https:\/\/maps\.app\.goo\.gl\/jG5SvHQvDozB4puc7"/);
assert.match(footer, /rel="noopener noreferrer"/);
assert.match(footer, /target="_blank"/);
assert.match(
  footer,
  /<svg\s+aria-hidden="true"\s+className="mw-footer__brand-location-icon"[\s\S]*?focusable="false"/
);
assert.match(footer, /<path d="M20 10c0 4\.993-[\s\S]*?<circle cx="12" cy="10" r="3"/);

const brandStart = footer.indexOf('className="mw-footer__brand"');
const catalogStart = footer.indexOf('aria-label="Catálogo de rejas"');
const brandBlock = footer.slice(brandStart, catalogStart);
assert.match(brandBlock, /className="mw-footer__brand-location"/);
assert.match(brandBlock, /aria-label="Ver ubicación de MetalWolft en Google Maps"/);
assert.match(brandBlock, /className="mw-footer__map-preview"/);
assert.match(
  brandBlock,
  /<Image\s+src="\/metalwolft-location-map\.jpg"\s+alt=""\s+width=\{880\}\s+height=\{495\}\s+sizes="\(max-width: 640px\) 100vw, 440px"/
);
assert.doesNotMatch(brandBlock, />\s*Ver ubicación en Google Maps\s*</);
assert.doesNotMatch(footer, /<iframe|maps\.googleapis\.com|maps\/api/);
assert.doesNotMatch(footer, /<p className="mw-footer__section-title">Ubicación<\/p>/);
assert.doesNotMatch(footer, /mw-footer__copy|Castilla-La Mancha/);
assert.doesNotMatch(footer, /legacyAdminUrl|showDevelopmentAdminLink|React Admin desarrollo/);

assert.match(
  styles,
  /\.mw-footer__grid\s*{[^}]*grid-template-columns:\s*minmax\(440px, 1\.35fr\) repeat\(4, minmax\(0, 1fr\)\)/s
);
assert.doesNotMatch(styles, /\.mw-footer__copy|\.mw-footer__location(?:\s|\{|-)/);
assert.match(styles, /@media \(max-width:\s*1100px\)[\s\S]*?\.mw-footer__grid\s*{[^}]*repeat\(2,/);
assert.match(styles, /@media \(max-width:\s*640px\)[\s\S]*?\.mw-footer__grid\s*{[^}]*grid-template-columns:\s*1fr/);
assert.match(
  styles,
  /\.mw-footer__map-preview\s*{[^}]*width:\s*min\(440px, 100%\);[^}]*aspect-ratio:\s*16 \/ 9;/s
);
assert.match(styles, /\.mw-footer__map-preview img\s*{[^}]*object-fit:\s*cover/s);
assert.doesNotMatch(styles, /\.mw-footer__map-preview[^}]*border-radius/s);
assert.doesNotMatch(
  styles,
  /\.mw-footer__map-preview:hover,\s*\.mw-footer__map-preview:focus-visible\s*{[^}]*transform:/s
);

assert.deepEqual([...mapThumbnail.subarray(0, 3)], [255, 216, 255]);

assert.match(legal, /href:\s*"\/cambios-politica-cookies"/);
assert.match(changesPolicy, /const PATH = "\/cambios-politica-cookies"/);

const dependencies = {
  ...JSON.parse(packageJson).dependencies,
  ...JSON.parse(packageJson).devDependencies
};
assert.equal(dependencies["lucide-react"], undefined);

console.log("Site footer assertions passed");
