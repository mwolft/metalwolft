import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import {
  fetchDeliveryEstimate,
  formatCartDeliveryDateRangeEs,
  formatCivilDateEs,
  formatCivilDateRangeCompactEs,
  formatCivilDateRangeEs,
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
assert.equal(
  formatCivilDateRangeEs("2026-08-17", "2026-08-21"),
  "Del 17 al 21 de agosto de 2026"
);
assert.equal(
  formatCivilDateRangeEs("2026-12-29", "2027-01-05"),
  "Del 29 de diciembre de 2026 al 5 de enero de 2027"
);
assert.equal(
  formatCivilDateRangeCompactEs("2026-08-24", "2026-08-28"),
  "24–28 de agosto de 2026"
);
assert.equal(
  formatCivilDateRangeCompactEs("2026-08-24", "2026-09-02"),
  "24 de agosto–2 de septiembre de 2026"
);
assert.equal(
  formatCivilDateRangeCompactEs("2026-12-29", "2027-01-05"),
  "29 de diciembre de 2026–5 de enero de 2027"
);
assert.equal(
  formatCivilDateRangeCompactEs("2026-08-24", "2026-08-24"),
  "24 de agosto de 2026"
);
assert.equal(formatCivilDateRangeCompactEs("2026-08-28", "2026-08-24"), null);
assert.equal(
  formatCartDeliveryDateRangeEs("2026-08-31", "2026-09-04", 2026),
  "31 ago–4 sep"
);
assert.equal(
  formatCartDeliveryDateRangeEs("2026-12-29", "2027-01-05", 2026),
  "29 dic–5 ene 2027"
);
assert.equal(
  formatCartDeliveryDateRangeEs("2025-08-31", "2025-09-04", 2026),
  "31 ago–4 sep 2025"
);

const sources = Object.fromEntries(
  await Promise.all(
    [
      ["component", "components/product/DeliveryEstimate.tsx"],
      ["styles", "app/globals.css"],
      ["mainCategory", "app/rejas-para-ventanas/page.tsx"],
      ["dynamicCategory", "app/[category_slug]/page.tsx"],
      ["cartPage", "app/cart/page.tsx"],
      ["cartFlow", "components/cart/CartFlow.tsx"],
      ["cartClient", "lib/cart-client.ts"],
      ["cartView", "components/cart/CartView.tsx"],
      ["details", "components/cart/CartDetailsStep.tsx"],
      ["payment", "components/cart/CartPaymentStep.tsx"],
      ["productConfigurator", "components/product/ProductConfigurator.tsx"],
      ["thankYou", "app/thank-you/page.tsx"],
      ["account", "app/mi-cuenta/page.tsx"]
    ].map(async ([name, path]) => [name, await readFile(new URL(`../${path}`, import.meta.url), "utf8")])
  )
);

for (const variant of ["default", "banner", "category", "compact"]) {
  assert.match(sources.component, new RegExp(`"${variant}"`));
}
assert.match(sources.component, /if \(!estimate\) \{\s*return null;/);
assert.match(sources.component, /variant === "default" \|\| variant === "compact"/);
assert.match(sources.component, /mw-delivery-estimate__compact-label">Entrega estimada:/);
assert.match(sources.component, /mw-delivery-estimate__compact-range">\{compactDateRange\}/);
assert.match(sources.component, /estimate\.adjustments && estimate\.adjustments\.length > 0/);
assert.match(sources.component, /ⓘ<\/span> \{adjustment\.message\}/);
assert.match(sources.component, /Plazo calculado para los productos de tu carrito\./);
assert.doesNotMatch(sources.component, /Puede variar según el tipo de reja y la cantidad del pedido\./);
assert.match(sources.component, /Puede variar según la configuración y el destino\./);
assert.doesNotMatch(sources.component, /Entrega orientativa entre/);
assert.equal(
  (sources.component.match(/Previsión orientativa para pedidos realizados hoy/g) || []).length,
  1
);
assert.match(
  sources.styles,
  /\.mw-delivery-estimate--default,\s*\.mw-delivery-estimate--compact\s*{[^}]*padding:\s*0;[^}]*border:\s*0;[^}]*border-radius:\s*0;[^}]*background:\s*transparent;/s
);
assert.match(sources.styles, /\.mw-delivery-estimate__compact-range\s*\{[^}]*font-size:\s*1rem;[^}]*font-weight:\s*700;/s);
assert.match(sources.component, /Los plazos pueden variar según el modelo, la configuración y el destino\./);

for (const categorySource of [sources.mainCategory, sources.dynamicCategory]) {
  assert.equal((categorySource.match(/fetchDeliveryEstimate\(\)/g) || []).length, 1);
}
assert.equal((sources.mainCategory.match(/variant="category"/g) || []).length, 1);
assert.equal((sources.dynamicCategory.match(/variant="banner"/g) || []).length, 1);
assert.match(sources.component, /src="\/icons\/plazos-de-entrega\.webp"/);
assert.doesNotMatch(sources.component, /PLAZO ESTIMADO ACTUALIZADO/);
assert.match(sources.component, /Entrega estimada para pedidos realizados hoy/);
assert.match(sources.component, /\{dateRange\}/);
assert.match(sources.component, /Previsión calculada según la carga actual del taller\./);
assert.match(sources.component, /Puede ampliarse en pedidos de/);
assert.match(sources.component, /grandes dimensiones o para determinados destinos\./);
assert.match(sources.component, /href="\/plazos-entrega-rejas-a-medida"/);
assert.match(sources.component, />\s*Leer más\s*<\/Link>/);
assert.doesNotMatch(sources.component, /Incluye la fabricación a medida/);
assert.doesNotMatch(sources.component, /y la entrega en domicilio, y puede variar según la configuración y el destino\./);
assert.doesNotMatch(sources.component, /entrega garantizada|fecha garantizada/i);
assert.equal((sources.cartPage.match(/fetchDeliveryEstimate\(\)/g) || []).length, 1);
assert.match(sources.cartPage, /<CartFlow deliveryEstimate=\{deliveryEstimate\} \/>/);
assert.match(sources.cartFlow, /getCartDeliveryEstimate/);
assert.match(sources.cartFlow, /subscribeToCartSnapshotChanges/);
assert.match(sources.cartFlow, /<DeliveryEstimate estimate=\{contextualEstimate\} variant="compact" \/>/);
assert.match(sources.cartFlow, /<CartView deliveryEstimate=\{contextualDeliveryEstimate\} \/>/);
assert.match(sources.cartFlow, /<CartPaymentStep deliveryEstimate=\{contextualDeliveryEstimate\} \/>/);
assert.match(sources.cartFlow, /<CartDetailsStep deliveryEstimate=\{contextualDeliveryEstimate\} \/>/);
assert.match(sources.cartView, /\{deliveryEstimate\}/);
assert.match(sources.details, /<CheckoutTotals quote=\{quote\} \/>\s*\{deliveryEstimate\}/);
assert.match(sources.payment, /\{deliveryEstimate\}/);
assert.match(sources.cartClient, /"\/api\/cart\/delivery-estimate"/);
assert.match(sources.cartClient, /cache:\s*"no-store"/);

for (const clientSource of [
  sources.cartFlow,
  sources.cartView,
  sources.details,
  sources.payment,
  sources.productConfigurator
]) {
  assert.doesNotMatch(clientSource, /fetchDeliveryEstimate/);
}
assert.doesNotMatch(sources.thankYou, /DeliveryEstimate/);
assert.doesNotMatch(sources.account, /DeliveryEstimate/);

console.log("Delivery estimate assertions passed");
