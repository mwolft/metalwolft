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
assert.match(sources.notification, /aria-live="polite"/);
assert.match(sources.notification, /notification\.dismissLabel/);
assert.match(sources.configurator, /title: "Añadido al carrito"/);
assert.match(sources.configurator, /dismissLabel: "Seguir comprando"/);
assert.match(sources.configurator, /cartStatus === "success"[\s\S]*?"Añadido"/);

console.log("34 cart feedback and hydration assertions passed");
