import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import {
  fetchDeliveryEstimate,
  formatCivilDateEs,
  parseDeliveryEstimate
} from "./delivery-estimate.ts";

const validEstimate = {
  start_date: "2026-12-29",
  end_date: "2027-01-05",
  is_active: true
};

{
  let capturedUrl = "";
  let capturedInit;
  const estimate = await fetchDeliveryEstimate({
    apiBaseUrl: "https://api.example.test/",
    fetcher: async (url, init) => {
      capturedUrl = String(url);
      capturedInit = init;
      return Response.json(validEstimate);
    }
  });

  assert.deepEqual(estimate, validEstimate);
  assert.equal(capturedUrl, "https://api.example.test/api/delivery-estimate");
  assert.deepEqual(capturedInit.next, { revalidate: 300 });
}

for (const status of [404, 500, 503]) {
  const estimate = await fetchDeliveryEstimate({
    apiBaseUrl: "https://api.example.test",
    fetcher: async () => Response.json({ is_active: false }, { status })
  });
  assert.equal(estimate, null);
}

{
  const estimate = await fetchDeliveryEstimate({
    apiBaseUrl: "https://api.example.test",
    fetcher: async () => {
      throw new TypeError("network unavailable");
    }
  });
  assert.equal(estimate, null);
}

{
  const estimate = await fetchDeliveryEstimate({
    apiBaseUrl: "https://api.example.test",
    fetcher: async () => new Response("{invalid", { status: 200 })
  });
  assert.equal(estimate, null);
}

assert.equal(await fetchDeliveryEstimate({ apiBaseUrl: null }), null);

{
  const previousApiUrl = process.env.API_URL;
  const previousPublicApiUrl = process.env.NEXT_PUBLIC_API_URL;
  process.env.API_URL = "https://server-api.example.test/";
  process.env.NEXT_PUBLIC_API_URL = "https://public-api.example.test";
  let capturedUrl = "";

  try {
    await fetchDeliveryEstimate({
      fetcher: async (url) => {
        capturedUrl = String(url);
        return Response.json(validEstimate);
      }
    });
  } finally {
    if (previousApiUrl === undefined) {
      delete process.env.API_URL;
    } else {
      process.env.API_URL = previousApiUrl;
    }
    if (previousPublicApiUrl === undefined) {
      delete process.env.NEXT_PUBLIC_API_URL;
    } else {
      process.env.NEXT_PUBLIC_API_URL = previousPublicApiUrl;
    }
  }

  assert.equal(capturedUrl, "https://server-api.example.test/api/delivery-estimate");
}

assert.equal(parseDeliveryEstimate({ ...validEstimate, is_active: false }), null);
assert.equal(parseDeliveryEstimate({ ...validEstimate, start_date: "2026-02-30" }), null);
assert.equal(parseDeliveryEstimate({ ...validEstimate, start_date: "29-12-2026" }), null);
assert.equal(
  parseDeliveryEstimate({ ...validEstimate, start_date: "2027-01-06" }),
  null
);
assert.equal(formatCivilDateEs("2026-12-29"), "29 de diciembre de 2026");
assert.equal(formatCivilDateEs("2027-01-05"), "5 de enero de 2027");
assert.equal(formatCivilDateEs("2026-02-30"), null);

const sources = Object.fromEntries(
  await Promise.all(
    [
      ["component", "components/product/DeliveryEstimate.tsx"],
      ["mainCategory", "app/rejas-para-ventanas/page.tsx"],
      ["dynamicCategory", "app/[category_slug]/page.tsx"],
      ["cartPage", "app/cart/page.tsx"],
      ["cartFlow", "components/cart/CartFlow.tsx"],
      ["cartView", "components/cart/CartView.tsx"],
      ["payment", "components/cart/CartPaymentStep.tsx"],
      ["productConfigurator", "components/product/ProductConfigurator.tsx"],
      ["thankYou", "app/thank-you/page.tsx"],
      ["account", "app/mi-cuenta/page.tsx"]
    ].map(async ([name, path]) => [name, await readFile(new URL(`../${path}`, import.meta.url), "utf8")])
  )
);

for (const variant of ["default", "banner", "compact"]) {
  assert.match(sources.component, new RegExp(`"${variant}"`));
}
assert.match(sources.component, /if \(!estimate\) \{\s*return null;/);
assert.match(sources.component, /Los plazos pueden variar según el modelo, la configuración y el destino\./);
assert.match(sources.component, /Entrega orientativa entre el/);
assert.match(sources.component, /Puede variar según la configuración y el destino\./);

for (const categorySource of [sources.mainCategory, sources.dynamicCategory]) {
  assert.equal((categorySource.match(/fetchDeliveryEstimate\(\)/g) || []).length, 1);
  assert.equal((categorySource.match(/variant="banner"/g) || []).length, 1);
}
assert.equal((sources.cartPage.match(/fetchDeliveryEstimate\(\)/g) || []).length, 1);
assert.equal((sources.cartPage.match(/variant="compact"/g) || []).length, 1);
assert.match(sources.cartFlow, /<CartView deliveryEstimate=\{deliveryEstimate\} \/>/);
assert.match(sources.cartFlow, /<CartPaymentStep deliveryEstimate=\{deliveryEstimate\} \/>/);
assert.doesNotMatch(sources.cartFlow, /<CartDetailsStep deliveryEstimate=/);
assert.match(sources.cartView, /\{deliveryEstimate\}/);
assert.match(sources.payment, /\{deliveryEstimate\}/);

for (const clientSource of [
  sources.cartFlow,
  sources.cartView,
  sources.payment,
  sources.productConfigurator
]) {
  assert.doesNotMatch(clientSource, /fetchDeliveryEstimate/);
}
assert.doesNotMatch(sources.thankYou, /DeliveryEstimate/);
assert.doesNotMatch(sources.account, /DeliveryEstimate/);

console.log("41 delivery estimate assertions passed");
