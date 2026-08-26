import assert from "node:assert/strict";
import {
  DesignServiceClientError,
  createDesignServiceRequest,
  getDesignServiceCheckoutQuote,
  requestDesignServiceQuote
} from "./design-service-client.ts";

const items = [
  { product_id: 7, width_cm: 200, height_cm: 120 },
  { product_id: 7, width_cm: 150, height_cm: 120 },
  { product_id: 8, width_cm: 100, height_cm: 80 }
];

const quote = {
  checkout_kind: "design_service",
  currency: "EUR",
  requires_shipping: false,
  shipping_cost: "0.00",
  subtotal: "74.85",
  base_price_gross: "74.85",
  discount_amount: "15.00",
  total_amount: "59.85",
  tax_rate: "21.00",
  tax_base: "49.46",
  tax_amount: "10.39",
  lead_time_hours: 24,
  pricing_tier_min_design_count: 3,
  items: [
    { product_id: 7, product_name: "Maryland", width_cm: "200", height_cm: "120" },
    { product_id: 7, product_name: "Maryland", width_cm: "150", height_cm: "120" },
    { product_id: 8, product_name: "Vermont", width_cm: "100", height_cm: "80" }
  ]
};

{
  let request;
  const result = await requestDesignServiceQuote(items, {
    apiBaseUrl: "https://api.example.test/",
    fetcher: async (url, init) => {
      request = { url: String(url), init };
      return Response.json(quote);
    }
  });

  assert.equal(result.total_amount, "59.85");
  assert.equal(request.url, "https://api.example.test/api/design-requests/quote");
  assert.equal(request.init.headers.Authorization, undefined);
  assert.deepEqual(JSON.parse(request.init.body), { items });
}

{
  let request;
  const result = await getDesignServiceCheckoutQuote("jwt-token", 12, {
    apiBaseUrl: "https://api.example.test/",
    fetcher: async (url, init) => {
      request = { url: String(url), init };
      return Response.json({ ...quote, design_request_id: 12 });
    }
  });

  assert.equal(result.design_request_id, 12);
  assert.equal(request.url, "https://api.example.test/api/design-requests/12/checkout-quote");
  assert.equal(request.init.method, "POST");
  assert.equal(request.init.headers.Authorization, "Bearer jwt-token");
}

{
  let request;
  const result = await createDesignServiceRequest("jwt-token", items, "creation-key", {
    apiBaseUrl: "https://api.example.test",
    fetcher: async (_url, init) => {
      request = init;
      return Response.json({ id: 12, reference: "DR-12", status: "pending_payment", created: true });
    }
  });

  assert.equal(result.id, 12);
  assert.equal(request.headers.Authorization, "Bearer jwt-token");
  assert.equal(request.headers["Idempotency-Key"], "creation-key");
  assert.deepEqual(JSON.parse(request.body), { items });
}

await assert.rejects(
  requestDesignServiceQuote(items, {
    apiBaseUrl: "https://api.example.test",
    fetcher: async () => Response.json({ message: "Demasiadas solicitudes" }, { status: 429 })
  }),
  (error) => error instanceof DesignServiceClientError && error.kind === "rate_limited"
);

await assert.rejects(
  createDesignServiceRequest("jwt-token", items, "creation-key", {
    apiBaseUrl: "https://api.example.test",
    fetcher: async () => Response.json({ message: "Necesita autenticación" }, { status: 401 })
  }),
  (error) => error instanceof DesignServiceClientError && error.kind === "authentication"
);

await assert.rejects(
  getDesignServiceCheckoutQuote("jwt-token", 0, { apiBaseUrl: "https://api.example.test" }),
  (error) => error instanceof DesignServiceClientError && error.kind === "validation"
);

console.log("14 design service client assertions passed");
