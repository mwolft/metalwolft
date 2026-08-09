import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [button, restoration, layout, styles] = await Promise.all([
  readFile(new URL("../components/layout/BackToTopButton.tsx", import.meta.url), "utf8"),
  readFile(new URL("../components/layout/ScrollRestoration.tsx", import.meta.url), "utf8"),
  readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
  readFile(new URL("../app/globals.css", import.meta.url), "utf8")
]);

assert.match(button, /const SCROLL_THRESHOLD = 480;/);
assert.match(button, /window\.addEventListener\("scroll", updateVisibility, \{ passive: true \}\)/);
assert.match(button, /window\.removeEventListener\("scroll", updateVisibility\)/);
assert.match(button, /aria-label="Volver arriba"/);
assert.match(button, /<svg aria-hidden="true" viewBox="0 0 24 24">/);
assert.match(button, /m6 14 6-6 6 6/);
assert.match(button, /prefers-reduced-motion: reduce/);
assert.match(button, /window\.scrollTo\(\{ top: 0, behavior \}\)/);
assert.match(restoration, /navigation\?\.type === "reload"/);
assert.match(restoration, /!window\.location\.hash/);
assert.doesNotMatch(restoration, /scrollRestoration/);
assert.match(layout, /<ScrollRestoration \/>/);
assert.match(layout, /<BackToTopButton \/>/);
assert.match(styles, /\.mw-back-to-top\s*\{[^}]*position:\s*fixed;[^}]*z-index:\s*50;/s);
assert.match(styles, /\.mw-back-to-top\s*\{[^}]*width:\s*2\.35rem;[^}]*background:\s*var\(--mw-accent-dark\);/s);

console.log("Scroll controls assertions passed");
