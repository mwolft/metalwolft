import assert from "node:assert/strict";
import { fetchSitemapProducts } from "./api";

const originalFetch = globalThis.fetch;
let requestedUrl = "";

async function run() {
  globalThis.fetch = async (input) => {
    requestedUrl = String(input);
    return new Response(
      JSON.stringify([
        { category_slug: "rejas-para-ventanas", slug: "reja-disponible" },
        { category_slug: "rejas-para-ventanas", slug: "reja-retirada" }
      ]),
      { status: 200, headers: { "Content-Type": "application/json" } }
    );
  };

  const products = await fetchSitemapProducts();

  assert.equal(requestedUrl.endsWith("/api/sitemap/products"), true);
  assert.deepEqual(products, [
    { category_slug: "rejas-para-ventanas", slug: "reja-disponible" },
    { category_slug: "rejas-para-ventanas", slug: "reja-retirada" }
  ]);
  assert.equal("published" in products[0], false);
  assert.equal("available_for_sale" in products[0], false);
  console.log("4 sitemap API contract assertions passed");
}

run()
  .finally(() => {
    globalThis.fetch = originalFetch;
  })
  .catch((error) => {
    console.error(error);
    process.exitCode = 1;
  });
