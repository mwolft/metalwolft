import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "..");
const page = fs.readFileSync(path.join(root, "app/diseno-previo/page.tsx"), "utf8");
const builder = fs.readFileSync(
  path.join(root, "components/design-service/DesignServiceBuilder.tsx"),
  "utf8"
);
const styles = fs.readFileSync(path.join(root, "app/globals.css"), "utf8");
const sitemap = fs.readFileSync(path.join(root, "app/sitemap.ts"), "utf8");

assert.match(page, /path: "\/diseno-previo"/);
assert.match(page, /parseDesignServiceSeed/);
assert.match(page, /resumeDraftAfterAuth/);
assert.match(page, /Visualiza tu reja antes de encargarla/);
assert.match(page, /Volver al configurador/);
assert.match(page, /buildDesignServiceProductHref/);
assert.match(page, /returnToConfiguratorHref/);
assert.match(page, /DESIGN_CATEGORY_SLUG/);
assert.doesNotMatch(page, /history\.back/);
const pageMarkup = page.slice(page.indexOf("return ("));
assert.ok(pageMarkup.indexOf("<DesignServiceBuilder") < pageMarkup.indexOf('className="mw-design-page__return"'));
assert.match(pageMarkup, /<nav className="mw-design-page__return" aria-label="Navegación de retorno">/);
assert.match(styles, /\.mw-design-page__return\s*{[^}]*justify-content:\s*center;/s);
assert.match(styles, /\.mw-design-page__return a\s*{[^}]*color:\s*var\(--mw-muted\);/s);
assert.doesNotMatch(styles.match(/\.mw-design-page__return a\s*{[^}]*}/)?.[0] ?? "", /accent/);
assert.match(sitemap, /path: "\/diseno-previo"/);
assert.match(builder, /requestDesignServiceQuote/);
assert.match(builder, /startDesignServiceDraft/);
assert.match(builder, /\/diseno-previo\?resume=auth/);
assert.match(builder, /saveDesignServiceDraft\(validItems\)/);
assert.match(builder, /clearDesignServiceDraft\(\)/);
assert.match(builder, /Este diseño ya está incluido en tu solicitud/);
assert.match(builder, /disabled/);
assert.doesNotMatch(builder, /anclaje|torniller[ií]a|color|env[ií]o/i);

console.log("Design service page contract assertions passed");
