import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [contact, home, metadata] = await Promise.all([
  readFile(new URL("../app/contact/page.tsx", import.meta.url), "utf8"),
  readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
  readFile(new URL("./metadata.ts", import.meta.url), "utf8")
]);

assert.match(metadata, /organizationId = "https:\/\/www\.metalwolft\.com\/#organization"/);
assert.match(home, /"@type": "OnlineStore",\s*"@id": organizationId/);
assert.match(contact, /"@type": "OnlineStore",\s*"@id": organizationId/);
assert.match(contact, /logo: absoluteUrl\("\/metalwolft-isotipo\.webp"\)/);
assert.match(contact, /publisher: \{ "@id": organizationId \}/);
assert.match(contact, /about: \{ "@id": organizationId \}/);
assert.doesNotMatch(contact, /"@type": "Organization"|logo: siteConfig\.defaultOgImage/);
assert.match(contact, /email: contactDetails\.email/);
assert.match(contact, /telephone: contactDetails\.phoneDisplay/);

console.log("Contact identity schema assertions passed");
