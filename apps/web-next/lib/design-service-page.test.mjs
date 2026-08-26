import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "..");
const page = fs.readFileSync(path.join(root, "app/diseno-previo/page.tsx"), "utf8");
const builder = fs.readFileSync(
  path.join(root, "components/design-service/DesignServiceBuilder.tsx"),
  "utf8"
);
const sitemap = fs.readFileSync(path.join(root, "app/sitemap.ts"), "utf8");

assert.match(page, /path: "\/diseno-previo"/);
assert.match(page, /parseDesignServiceSeed/);
assert.match(page, /resumeDraftAfterAuth/);
assert.match(page, /Visualiza tu reja antes de encargarla/);
assert.match(sitemap, /path: "\/diseno-previo"/);
assert.match(builder, /requestDesignServiceQuote/);
assert.match(builder, /startDesignServiceDraft/);
assert.match(builder, /\/diseno-previo\?resume=auth/);
assert.match(builder, /saveDesignServiceDraft\(validItems\)/);
assert.match(builder, /clearDesignServiceDraft\(\)/);
assert.match(builder, /Este diseño ya está incluido en tu solicitud/);
assert.match(builder, /disabled/);
assert.doesNotMatch(builder, /anclaje|torniller[ií]a|color|env[ií]o/i);

console.log("8 design service page contract assertions passed");
