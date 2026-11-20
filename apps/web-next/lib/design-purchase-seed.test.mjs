import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { consumeDesignPurchaseSeed, isDesignPurchaseSeed, saveDesignPurchaseSeed } from "./design-purchase-seed.ts";

const values = new Map();
globalThis.window = {
  sessionStorage: {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
    removeItem: (key) => values.delete(key)
  }
};

const seed = { categorySlug: "rejas-para-ventanas", productSlug: "reja-fija-albany", heightCm: "95.25", widthCm: "80" };
assert.equal(isDesignPurchaseSeed(seed), true);
assert.equal(isDesignPurchaseSeed({ ...seed, heightCm: "0" }), false);
assert.equal(isDesignPurchaseSeed({ ...seed, widthCm: "Infinity" }), false);
assert.equal(saveDesignPurchaseSeed(seed), true);
values.set("mw_pending_product_config", "previous-configuration");
assert.equal(consumeDesignPurchaseSeed(seed.categorySlug, "otro-modelo"), null);
const consumed = consumeDesignPurchaseSeed(seed.categorySlug, seed.productSlug);
assert.equal(consumed?.heightCm, seed.heightCm);
assert.equal(consumed?.widthCm, seed.widthCm);
assert.equal(consumeDesignPurchaseSeed(seed.categorySlug, seed.productSlug), null);
assert.equal(values.get("mw_pending_product_config"), "previous-configuration");
values.set("mw_design_purchase_seed", JSON.stringify({ ...seed, createdAt: Date.now() - 11 * 60 * 1000 }));
assert.equal(consumeDesignPurchaseSeed(seed.categorySlug, seed.productSlug), null);

const configurator = readFileSync(new URL("../components/product/ProductConfigurator.tsx", import.meta.url), "utf8");
const card = readFileSync(new URL("../components/account/DesignPurchaseCard.tsx", import.meta.url), "utf8");
assert.ok(configurator.indexOf("consumeDesignPurchaseSeed(") < configurator.indexOf("readPendingProductConfig(productId, categorySlug, productSlug);"));
assert.match(configurator, /setHeight\(seed\.heightCm\)/);
assert.match(configurator, /setWidth\(seed\.widthCm\)/);
assert.match(card, /available_for_sale/);
assert.match(card, /desde_diseno=1/);

console.log("Design purchase seed assertions passed");
