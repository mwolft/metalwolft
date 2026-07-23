import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const sources = Object.fromEntries(
  await Promise.all(
    [
      ["page", "../app/thank-you/page.tsx"],
      ["status", "../components/cart/ThankYouStatus.tsx"],
      ["spinner", "../components/ui/MetalSpinner.tsx"],
      ["styles", "../app/globals.css"]
    ].map(async ([name, path]) => [name, await readFile(new URL(path, import.meta.url), "utf8")])
  )
);

assert.match(sources.spinner, /"inline" \| "block" \| "page"/);
assert.match(sources.spinner, /variant = "inline"/);
assert.match(sources.spinner, /role="status"/);
assert.match(sources.spinner, /aria-live="polite"/);
assert.match(sources.spinner, /mw-visually-hidden/);
assert.match(sources.spinner, /aria-hidden="true"/);
assert.match(sources.spinner, /mw-metal-spinner--\$\{variant\}/);
assert.doesNotMatch(sources.spinner, /from "(?!react)/);

assert.match(sources.page, /className="mw-thank-you-page"/);
assert.match(sources.page, /MetalSpinner variant="page" label="Comprobando pedido"/);
assert.match(sources.status, /MetalSpinner variant="block" label=\{title\}/);
assert.match(sources.status, /tone="success"/);
assert.match(sources.status, /Tu pedido se ha confirmado correctamente\./);
assert.match(sources.status, /statusData\.order\?\.locator \?/);
assert.match(sources.status, /`\/mi-cuenta\/pedidos\/\$\{statusData\.order\.id\}`/);
assert.match(sources.status, /"\/mi-cuenta\/pedidos"/);
assert.match(sources.status, /href="\/rejas-para-ventanas"/);
assert.match(sources.status, /aria-hidden="true"/);
assert.match(sources.status, /getCheckoutStatus\(token, identifiers\)/);
assert.match(sources.status, /clearStoredCheckoutDiscountCode\(\)/);

assert.match(sources.styles, /\.mw-site-main \{[\s\S]*?display: flex;/);
assert.match(sources.styles, /\.mw-thank-you-page \{[\s\S]*?flex: 1;/);
assert.match(sources.styles, /env\(safe-area-inset-top\)/);
assert.match(sources.styles, /env\(safe-area-inset-bottom\)/);
assert.match(sources.styles, /width: min\(100%, 700px\)/);
assert.match(sources.styles, /overflow: visible/);
assert.match(sources.styles, /@media \(prefers-reduced-motion: reduce\)[\s\S]*?\.mw-metal-spinner svg/);
assert.match(sources.styles, /@media \(max-width: 640px\)[\s\S]*?\.mw-thank-you-card \.mw-button/);

console.log("28 Thank You and MetalSpinner assertions passed");
