import assert from "node:assert/strict";
import {
  buildDesignServiceProductHref,
  buildDesignServiceSeedHref,
  parseDesignServiceOrigin,
  parseDesignServiceSeed,
  resolveDesignServiceReturnNavigation
} from "./design-service-seed.ts";

assert.deepEqual(
  parseDesignServiceSeed(new URLSearchParams("producto=maryland&ancho=200&alto=120")),
  { product_slug: "maryland", width_cm: 200, height_cm: 120 }
);
assert.deepEqual(
  parseDesignServiceSeed(new URLSearchParams("producto=maryland&ancho=200%2C5&alto=120")),
  { product_slug: "maryland", width_cm: 200.5, height_cm: 120 }
);

for (const query of [
  "producto=Maryland&ancho=200&alto=120",
  "producto=maryland&ancho=0&alto=120",
  "producto=maryland&ancho=200",
  "producto=maryland&ancho=2e2&alto=120",
  "producto=maryland&ancho=-1&alto=120"
]) {
  assert.equal(parseDesignServiceSeed(new URLSearchParams(query)), null);
}

assert.equal(
  buildDesignServiceSeedHref({ product_slug: "maryland", width_cm: 200, height_cm: 120 }),
  "/diseno-previo?producto=maryland&ancho=200&alto=120"
);
assert.equal(
  buildDesignServiceSeedHref({ product_slug: "essex", width_cm: 100, height_cm: 100 }, "cart"),
  "/diseno-previo?producto=essex&ancho=100&alto=100&from=cart"
);
assert.equal(
  buildDesignServiceSeedHref({ product_slug: "Maryland", width_cm: 200, height_cm: 120 }),
  null
);

assert.equal(parseDesignServiceOrigin(new URLSearchParams("from=configurator")), "configurator");
assert.equal(parseDesignServiceOrigin(new URLSearchParams("from=cart")), "cart");
assert.equal(parseDesignServiceOrigin(new URLSearchParams("from=direct")), "direct");
assert.equal(parseDesignServiceOrigin(new URLSearchParams("from=unknown")), "direct");
assert.equal(parseDesignServiceOrigin(new URLSearchParams()), null);

const marylandSeed = { product_slug: "maryland", width_cm: 200, height_cm: 120 };
assert.deepEqual(
  resolveDesignServiceReturnNavigation("configurator", marylandSeed, "rejas-para-ventanas"),
  { href: "/rejas-para-ventanas/maryland", label: "Volver al configurador" }
);
assert.deepEqual(
  resolveDesignServiceReturnNavigation("cart", marylandSeed, "rejas-para-ventanas"),
  { href: "/cart", label: "Volver al carrito" }
);
assert.equal(resolveDesignServiceReturnNavigation("direct", marylandSeed, "rejas-para-ventanas"), null);
assert.equal(resolveDesignServiceReturnNavigation("direct", null, "rejas-para-ventanas"), null);

assert.equal(
  buildDesignServiceProductHref("rejas-para-ventanas", {
    product_slug: "maryland",
    width_cm: 200,
    height_cm: 120
  }),
  "/rejas-para-ventanas/maryland"
);
assert.equal(
  buildDesignServiceProductHref("rejas-para-ventanas", {
    product_slug: "maryland?price=24.95",
    width_cm: 200,
    height_cm: 120
  }),
  null
);

console.log("11 design service seed assertions passed");
