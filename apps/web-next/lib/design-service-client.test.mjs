import assert from "node:assert/strict";
import {
  DesignServiceClientError,
  createDesignServiceStripePaymentIntent,
  createDesignServiceRequest,
  getDesignServiceConfirmation,
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

{
  let request;
  const result = await createDesignServiceStripePaymentIntent(
    "jwt-token",
    12,
    {
      payment_method_id: "pm_test",
      idempotency_key: "payment-key",
      customer_data: {
        firstname: "Ana", lastname: "Cliente", email: "ana@example.test", phone: "600000000",
        legal_name: "Ana Cliente", tax_id: "00000000T", billing_address: "Calle 1",
        billing_city: "Ciudad Real", billing_postal_code: "13001"
      }
    },
    {
      apiBaseUrl: "https://api.example.test",
      fetcher: async (url, init) => {
        request = { url, init };
        return Response.json({
          clientSecret: "pi_secret",
          paymentIntent: { id: "pi_1", status: "requires_payment_method" },
          amount_used_cents: 5985,
          checkout_session_id: 8,
          checkout_session_status: "pending_payment",
          payment_provider: "stripe",
          payment_intent_id: "pi_1",
          provider_order_id: null,
          provider_capture_id: null,
          provider_status: "requires_payment_method",
          public_checkout_token: "token",
          checkout_summary: { ...quote, design_request_id: 12 }
        });
      }
    }
  );
  assert.equal(result.amount_used_cents, 5985);
  assert.equal(request.url, "https://api.example.test/api/design-requests/12/stripe/payment-intent");
  assert.equal(JSON.parse(request.init.body).total_amount, undefined);
}

{
  const result = await getDesignServiceConfirmation("jwt-token", 12, {
    apiBaseUrl: "https://api.example.test",
    fetcher: async () => Response.json({
      id: 12, reference: "DR-12", status: "pending", lead_time_hours: 24,
      total_amount: "59.85", currency: "EUR", items: [], order: { id: 7, locator: "AB1234" },
      checkout_status: "order_created"
    })
  });
  assert.equal(result.reference, "DR-12");
}

console.log("18 design service client assertions passed");
