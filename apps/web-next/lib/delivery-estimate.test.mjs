import assert from "node:assert/strict";
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

console.log("15 delivery estimate tests passed");
