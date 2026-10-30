import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const home = readFileSync(new URL("../app/page.tsx", import.meta.url), "utf8");
const metadata = readFileSync(new URL("./metadata.ts", import.meta.url), "utf8");
const organization = home.slice(home.indexOf("function buildOrganizationJsonLd"), home.indexOf("function buildWebPageJsonLd"));
const webPage = home.slice(home.indexOf("function buildWebPageJsonLd"), home.indexOf("function buildItemListJsonLd"));

assert.match(organization, /"@type": "OnlineStore"/);
assert.match(metadata, /organizationId = "https:\/\/www\.metalwolft\.com\/#organization"/);
assert.match(organization, /"@id": organizationId/);
assert.match(organization, /logo: absoluteUrl\("\/metalwolft-isotipo\.webp"\)/);
assert.doesNotMatch(organization, /"@type": "(?:Organization|LocalBusiness)"|legalName:|sameAs:|address:/);
assert.match(webPage, /about: \{ "@id": organizationId \}/);
assert.match(webPage, /"@id": absoluteUrl\("\/#website"\)/);
assert.match(webPage, /publisher: \{ "@id": organizationId \}/);
assert.equal((home.match(/<JsonLd data=\{buildOrganizationJsonLd\(\)\}/g) || []).length, 1);

assert.match(
  webPage,
  /primaryImageOfPage:\s*\{\s*"@type": "ImageObject",\s*url: absoluteUrl\(HERO_IMAGE_PATH\)\s*\}/
);
