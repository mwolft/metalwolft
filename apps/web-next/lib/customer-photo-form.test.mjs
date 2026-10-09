import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import nextConfig from "../next.config.mjs";

const root = process.cwd();
const page = readFileSync(join(root, "app/fotos-clientes/page.tsx"), "utf8");
const form = readFileSync(join(root, "components/contact/CustomerPhotoForm.tsx"), "utf8");
const analytics = readFileSync(join(root, "components/analytics/GtmAnalytics.tsx"), "utf8");
const config = readFileSync(join(root, "next.config.mjs"), "utf8");

assert.match(page, /robots: \{ index: false, follow: false/);
assert.match(form, /window\.location\.hash\.slice\(1\)/);
assert.match(form, /window\.history\.replaceState/);
assert.match(form, /headers: \{ Authorization: `Bearer \$\{token\.current\}` \}/);
assert.match(form, /commercial_consent/);
assert.match(form, /value="yes"/);
assert.match(form, /value="no"/);
assert.match(form, /image\/jpeg,image\/png,image\/webp/);
assert.match(form, /MAX_IMAGES|info\.max_images/);
assert.match(analytics, /pathname === "\/fotos-clientes"/);
assert.match(config, /source: "\/fotos-clientes"/);
assert.match(config, /Referrer-Policy.*no-referrer/);
const redirects = await nextConfig.redirects();
const headers = await nextConfig.headers();
assert.equal(redirects.some((route) => route.source === "/fotos-clientes"), false);
assert.deepEqual(
  headers.find((route) => route.source === "/fotos-clientes")?.headers,
  [
    { key: "Referrer-Policy", value: "no-referrer" },
    { key: "X-Robots-Tag", value: "noindex, nofollow, noarchive" }
  ]
);

console.log("Customer photo form source assertions passed");
