import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const page = readFileSync(join(process.cwd(), "app/condiciones-promocion-fotos/page.tsx"), "utf8");

assert.match(page, /const PATH = "\/condiciones-promocion-fotos"/);
assert.match(page, /export default function CustomerPhotoPromotionTermsPage/);
assert.match(page, /robots: \{ index: false, follow: false, noarchive: true \}/);
assert.match(page, /Borrador pendiente de aprobación/);
assert.match(page, /20 € por pedido elegible/);
assert.match(page, /SIMULACIÓN — SIN REEMBOLSO/);
assert.match(page, /mailto:admin@metalwolft\.com/);
assert.match(page, /href="\/politica-privacidad"/);

console.log("Customer photo promotion terms route assertions passed");
