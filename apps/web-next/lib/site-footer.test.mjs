import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [footer, styles, packageJson, legal, changesPolicy, mapThumbnail] = await Promise.all([
  readFile(new URL("../components/layout/SiteFooter.tsx", import.meta.url), "utf8"),
  readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
  readFile(new URL("../package.json", import.meta.url), "utf8"),
  readFile(new URL("./legal.ts", import.meta.url), "utf8"),
  readFile(new URL("../app/cambios-politica-cookies/page.tsx", import.meta.url), "utf8"),
  readFile(new URL("../public/metalwolft-location-map.png", import.meta.url))
]);

assert.match(footer, /Carretera de Porzuna, km 1,8/);
assert.match(
  footer,
  /<svg\s+aria-hidden="true"\s+className="mw-footer__brand-location-icon"[\s\S]*?focusable="false"/
);
assert.match(footer, /<path d="M20 10c0 4\.993-[\s\S]*?<circle cx="12" cy="10" r="3"/);

const brandStart = footer.indexOf('className="mw-footer__brand"');
const catalogStart = footer.indexOf('<nav className="mw-footer__section" aria-label=');
const brandBlock = footer.slice(brandStart, catalogStart);
assert.match(brandBlock, /className="mw-footer__brand-location"/);
assert.match(brandBlock, /<div aria-hidden="true" className="mw-footer__map-preview">/);
assert.match(
  brandBlock,
  /<Image\s+src="\/metalwolft-location-map\.png"\s+alt=""\s+width=\{612\}\s+height=\{344\}\s+sizes="\(max-width: 640px\) 100vw, 306px"/
);
assert.doesNotMatch(brandBlock, /<a\b|href=|target=|rel=/);
assert.doesNotMatch(footer, /maps\.app\.goo\.gl|Google Maps|<iframe|maps\.googleapis\.com|maps\/api/);
assert.doesNotMatch(footer, /legacyAdminUrl|showDevelopmentAdminLink|React Admin desarrollo/);

assert.match(
  styles,
  /\.mw-footer__grid\s*{[^}]*grid-template-columns:\s*minmax\(306px, 1\.35fr\) repeat\(4, minmax\(0, 1fr\)\)/s
);
assert.match(styles, /@media \(max-width:\s*1100px\)[\s\S]*?\.mw-footer__grid\s*{[^}]*repeat\(2,/);
assert.match(styles, /@media \(max-width:\s*640px\)[\s\S]*?\.mw-footer__grid\s*{[^}]*grid-template-columns:\s*1fr/);
assert.match(
  styles,
  /\.mw-footer__map-preview\s*{[^}]*grid-column:\s*1 \/ -1;[^}]*width:\s*min\(306px, 100%\);[^}]*aspect-ratio:\s*16 \/ 9;[^}]*pointer-events:\s*none/s
);
assert.match(styles, /\.mw-footer__map-preview img\s*{[^}]*object-fit:\s*cover/s);
assert.doesNotMatch(styles, /\.mw-footer__brand-location a\s*{|\.mw-footer__map-preview:hover|\.mw-footer__map-preview:focus-visible/);
assert.deepEqual([...mapThumbnail.subarray(0, 4)], [137, 80, 78, 71]);

assert.match(legal, /href:\s*"\/cambios-politica-cookies"/);
assert.match(changesPolicy, /const PATH = "\/cambios-politica-cookies"/);

const dependencies = {
  ...JSON.parse(packageJson).dependencies,
  ...JSON.parse(packageJson).devDependencies
};
assert.equal(dependencies["lucide-react"], undefined);

console.log("Footer location assertions passed");
