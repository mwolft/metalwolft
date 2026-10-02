import assert from "node:assert/strict";
import nextConfig from "../next.config.mjs";

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
console.log("Historical reja redirects are permanent and direct in Next");
