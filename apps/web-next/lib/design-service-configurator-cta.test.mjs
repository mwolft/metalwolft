import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const configurator = await readFile(
  new URL("../components/product/ProductConfigurator.tsx", import.meta.url),
  "utf8"
);

assert.match(configurator, /dimensionsReadyForQuote/);
assert.match(configurator, /buildDesignServiceSeedHref/);
assert.match(configurator, /product_slug: productSlug/);
assert.match(configurator, /width_cm: designPreviewWidth/);
assert.match(configurator, /height_cm: designPreviewHeight/);
assert.match(configurator, /requestDesignServiceQuote/);
assert.match(configurator, /designPreviewHref \? \(/);
assert.match(configurator, /Ver diseño previo/);
assert.match(configurator, /¿Quieres ver cómo quedará tu reja\?/);
assert.match(configurator, /designPreviewHeight} × {designPreviewWidth} cm/);
assert.match(configurator, /src="\/icons\/diseno-previo-rejas\.webp"/);
assert.match(configurator, /aria-hidden="true"/);
assert.match(configurator, /designServiceQuote\.total_amount/);
assert.doesNotMatch(configurator, /anclaje.*designPreviewHref|color.*designPreviewHref|screw_option.*designPreviewHref/);
assert.doesNotMatch(configurator, /pushGtmEvent\(\{[\s\S]*?design_preview/);

console.log("10 design service configurator CTA assertions passed");
