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
assert.match(page, /Mira las proporciones de tu reja antes de encargarla/);
assert.match(page, /El diseño previo es\s+un servicio opcional, especialmente útil si tienes dudas sobre la estética o las proporciones de\s+tu reja con las medidas elegidas\./);
assert.match(page, /parseDesignServiceOrigin/);
assert.match(page, /resolveDesignServiceReturnNavigation/);
assert.match(page, /explicitOrigin,/);
assert.match(page, /DESIGN_CATEGORY_SLUG/);
assert.doesNotMatch(page, /history\.back/);
const pageMarkup = page.slice(page.indexOf("return ("));
assert.ok(pageMarkup.indexOf("<DesignServiceBuilder") < pageMarkup.indexOf('className="mw-design-page__return"'));
assert.match(pageMarkup, /<nav className="mw-design-page__return" aria-label="Navegación de retorno">/);
assert.match(pageMarkup, /className="mw-design-page__return-link"/);
assert.match(pageMarkup, /<svg aria-hidden="true" focusable="false" viewBox="0 0 20 20">/);
assert.match(styles, /\.mw-design-page__return\s*{[^}]*justify-content:\s*center;/s);
assert.match(styles, /\.mw-design-page__return-link\s*{[^}]*color:\s*#64748b;/s);
assert.doesNotMatch(styles.match(/\.mw-design-page__return-link\s*{[^}]*}/)?.[0] ?? "", /accent|underline/);
assert.match(sitemap, /path: "\/diseno-previo"/);
assert.match(builder, /requestDesignServiceQuote/);
assert.match(builder, /startDesignServiceDraft/);
assert.match(builder, /\/diseno-previo\?resume=auth/);
assert.match(builder, /saveDesignServiceDraft\(validItems\)/);
assert.match(builder, /clearDesignServiceDraft\(\)/);
assert.match(builder, /Este diseño ya está incluido en tu solicitud/);
assert.match(builder, /Añade diseños diferentes y obtén un mejor precio por diseño\./);
assert.match(builder, /Si necesitas varias rejas del mismo modelo y medidas, basta con solicitar un único diseño\./);
assert.match(builder, /Un único diseño te sirve para todas las rejas del mismo modelo y medidas\./);
assert.match(builder, /disabled/);
assert.doesNotMatch(builder, /anclaje|torniller[ií]a|color|env[ií]o/i);

console.log("Design service page contract assertions passed");
