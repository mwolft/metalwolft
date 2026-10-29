import assert from "node:assert/strict";
import nextConfig from "../next.config.mjs";
import { readFileSync } from "node:fs";

const redirects = await nextConfig.redirects();
const rejaRedirects = redirects.filter((entry) =>
  entry.source.startsWith("/rejas/rejas-para-ventanas-")
);

const expected = new Map([
  ["pittsburgh", "reja-fija-pittsburgh"],
  ["livingston", "reja-fija-livingston"],
  ["lancaster", "reja-fija-lancaster"],
  ["essex", "reja-fija-essex"]
]);

assert.equal(rejaRedirects.length, expected.size);
for (const [oldSlug, newSlug] of expected) {
  const source = `/rejas/rejas-para-ventanas-${oldSlug}`;
  const destination = `/rejas-para-ventanas/${newSlug}`;
  const matching = rejaRedirects.filter((entry) => entry.source === source);

  assert.equal(matching.length, 1);
  assert.equal(matching[0].destination, destination);
  assert.equal(matching[0].permanent, true);
  assert.equal(redirects.some((entry) => entry.source === destination), false);
}

assert.equal(redirects.some((entry) => entry.source.includes("delhi")), false);
const poole = redirects.find((entry) => entry.source === "/rejas-para-ventanas/reja-fija-poole");
assert.equal(poole?.destination, "/rejas-para-ventanas/reja-fija-essex");
assert.equal(poole?.statusCode, 301);
assert.equal(redirects.some((entry) => entry.source === poole.destination), false);
const sitemapSource = readFileSync(new URL("../app/sitemap.ts", import.meta.url), "utf8");
assert.match(sitemapSource, /product\.slug !== "reja-fija-poole"/);
console.log("Historical reja redirects are permanent and direct in Next");
