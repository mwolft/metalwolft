import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import {
  addCartItem,
  clearCart,
  countCartLines,
  deleteCartItem,
  getCart,
  subscribeToCartSnapshotChanges,
  updateCartItemQuantity
} from "./cart-client.ts";
import { getCheckoutQuote } from "./checkout-client.ts";

const line = (id, overrides = {}) => ({
  id,
  usuario_id: 7,
  producto_id: id,
  nombre: `Producto ${id}`,
  descripcion: "",
  imagen: null,
  slug: `producto-${id}`,
  category_slug: "rejas-para-ventanas",
  alto: 100,
  ancho: 80,
  anclaje: "pletinas",
  color: "negro",
  screw_option: "standard",
  screw_length_mm: 70,
  screw_supplement: 0,
  precio_total: 100,
  quantity: 1,
  added_at: "2026-07-23T10:00:00",
  available_for_sale: true,
  ...overrides
});

const oneLineWithThreeUnits = [line(1, { quantity: 3 })];
const twoConfigurations = [line(1), line(2, { alto: 120 })];
assert.equal(countCartLines([]), 0);
assert.equal(countCartLines(oneLineWithThreeUnits), 1);
assert.equal(countCartLines(twoConfigurations), 2);

const originalWindow = globalThis.window;
const originalFetch = globalThis.fetch;
const originalApiUrl = process.env.NEXT_PUBLIC_API_URL;
const browserEvents = new EventTarget();
globalThis.window = browserEvents;
process.env.NEXT_PUBLIC_API_URL = "https://api.example.test";

const changes = [];
const unsubscribe = subscribeToCartSnapshotChanges((change) => changes.push(change));

try {
  const quoteRequests = [];
  const quoteResponses = [
    {
      lines: [],
      subtotal: 100,
      shipping_cost: 21,
      discount_code: null,
      discount_code_valid: false,
      discount_percent: 0,
      discount_amount: 0,
      total_amount: 121
    },
    {
      lines: [],
      subtotal: 180,
      shipping_cost: 0,
      discount_code: null,
      discount_code_valid: false,
      discount_percent: 0,
      discount_amount: 0,
      total_amount: 180
    }
  ];
  globalThis.fetch = async (url, init) => {
    quoteRequests.push({ url: String(url), method: init?.method });
    return Response.json(quoteResponses.shift());
  };
  const belowFreeShippingThreshold = await getCheckoutQuote("token");
  assert.equal(belowFreeShippingThreshold.shipping_cost, 21);
  assert.equal(belowFreeShippingThreshold.total_amount, 121);
  const aboveFreeShippingThreshold = await getCheckoutQuote("token");
  assert.equal(aboveFreeShippingThreshold.shipping_cost, 0);
  assert.equal(aboveFreeShippingThreshold.total_amount, 180);
  assert.match(quoteRequests[0].url, /\/api\/checkout\/quote$/);
  assert.equal(quoteRequests[0].method, "POST");

  globalThis.fetch = async (url, init) => {
    return Response.json({
      lines: [],
      subtotal: 200,
      shipping_cost: 39.95,
      discount_code: null,
      discount_code_valid: false,
      discount_percent: 0,
      discount_amount: 0,
      total_amount: 239.95
    });
  };
  const authoritativeQuote = await getCheckoutQuote("token");
  assert.equal(authoritativeQuote.shipping_cost, 39.95);
  assert.equal(authoritativeQuote.total_amount, 239.95);

  globalThis.fetch = async () => Response.json(twoConfigurations);
  assert.deepEqual(await getCart("token"), twoConfigurations);
  assert.deepEqual(changes.at(-1), { items: twoConfigurations, reason: "sync" });

  const publishedChanges = changes.length;
  const hydratedCart = await getCart("token", { publishSnapshot: false });
  assert.equal(countCartLines(hydratedCart), 2);
  assert.equal(changes.length, publishedChanges);

  globalThis.fetch = async () => Response.json([line(1, { quantity: 4 })]);
  assert.equal(countCartLines(await getCart("token", { publishSnapshot: false })), 1);
  assert.equal(changes.length, publishedChanges);

  globalThis.fetch = async () => Response.json([]);
  assert.equal(countCartLines(await getCart("token", { publishSnapshot: false })), 0);
  assert.equal(changes.length, publishedChanges);

  globalThis.fetch = async () => {
    throw new TypeError("network unavailable");
  };
  await assert.rejects(getCart("token", { publishSnapshot: false }));
  assert.equal(changes.length, publishedChanges);

  globalThis.fetch = async () => Response.json(twoConfigurations);
  assert.deepEqual(
    await addCartItem("token", {
      product_id: 2,
      alto: 120,
      ancho: 80,
      anclaje: "pletinas",
      color: "negro",
      screw_option: "standard",
      quantity: 1
    }),
    twoConfigurations
  );
  assert.equal(changes.at(-1).reason, "mutation");

  await updateCartItemQuantity("token", twoConfigurations[0], 3);
  assert.deepEqual(changes.at(-1).items, twoConfigurations);

  globalThis.fetch = async () => Response.json({ updated_cart: oneLineWithThreeUnits });
  await deleteCartItem("token", twoConfigurations[1]);
  assert.deepEqual(changes.at(-1), { items: oneLineWithThreeUnits, reason: "mutation" });

  globalThis.fetch = async () => Response.json({ message: "ok" });
  await clearCart("token");
  assert.deepEqual(changes.at(-1), { items: [], reason: "mutation" });
} finally {
  unsubscribe();
  globalThis.fetch = originalFetch;
  globalThis.window = originalWindow;
  if (originalApiUrl === undefined) {
    delete process.env.NEXT_PUBLIC_API_URL;
  } else {
    process.env.NEXT_PUBLIC_API_URL = originalApiUrl;
  }
}

const sources = Object.fromEntries(
  await Promise.all(
    [
      ["header", "../components/layout/HeaderCartLink.tsx"],
      ["provider", "../components/cart/CartProvider.tsx"],
      ["cartView", "../components/cart/CartView.tsx"],
      ["notification", "../components/notifications/NotificationProvider.tsx"],
      ["configurator", "../components/product/ProductConfigurator.tsx"]
    ].map(async ([name, path]) => [name, await readFile(new URL(path, import.meta.url), "utf8")])
  )
);

assert.match(sources.header, /lineCount > 99 \? "99\+" : lineCount/);
assert.match(sources.header, /aria-hidden="true"/);
assert.match(sources.header, /Carrito,.*configuraci/);
assert.doesNotMatch(sources.provider, /fetch\(|localStorage|sessionStorage/);
assert.match(sources.provider, /items: readonly CartItem\[\]/);
assert.match(sources.provider, /getCart\(token, \{ publishSnapshot: false \}\)/);
assert.match(sources.provider, /snapshotVersion\.current === versionAtStart/);
assert.match(sources.provider, /isActive &&/);
assert.match(sources.provider, /pendingInitialHydration\?\.token === token/);
assert.match(sources.provider, /promise\.then\(resetInitialHydration, resetInitialHydration\)/);
assert.match(sources.provider, /\.catch\(\(\) =>/);
assert.match(sources.cartView, /getCheckoutQuote\(token\)/);
assert.match(sources.cartView, /quote\.shipping_cost/);
assert.match(sources.cartView, /quote\.total_amount/);
assert.match(sources.cartView, /setCheckoutQuote\(hasValidAmounts \? quote : null\)/);
assert.match(sources.cartView, /checkoutQuote\.shipping_cost === 0/);
assert.match(sources.cartView, /formatCurrency\(checkoutQuote\.total_amount\)/);
assert.match(sources.cartView, /checkoutQuote !== null/);
assert.match(sources.cartView, /Envío calculado en el checkout\./);
assert.match(sources.cartView, /Total calculado en el checkout\./);
assert.match(sources.cartView, /checkoutQuoteRequestVersion\.current === requestVersion/);
assert.match(sources.cartView, /updatedCart\.length > 0/);
assert.doesNotMatch(sources.cartView, /checkoutQuote\.subtotal\s*\+\s*checkoutQuote\.shipping_cost/);
assert.doesNotMatch(sources.cartView, /subtotal\s*\+\s*(checkoutQuote\.)?shipping/);
assert.match(sources.notification, /aria-live="polite"/);
assert.match(sources.notification, /notification\.dismissLabel/);
assert.match(sources.configurator, /title: "Añadido al carrito"/);
assert.match(sources.configurator, /dismissLabel: "Seguir comprando"/);
assert.match(sources.configurator, /cartStatus === "success"[\s\S]*?"Añadido"/);

console.log("55 cart feedback, hydration, shipping, and total assertions passed");
