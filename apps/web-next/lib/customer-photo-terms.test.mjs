import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const page = readFileSync(join(process.cwd(), "app/condiciones-promocion-fotos/page.tsx"), "utf8");

assert.match(page, /const PATH = "\/condiciones-promocion-fotos"/);
assert.match(page, /export default function CustomerPhotoPromotionTermsPage/);
assert.match(page, /robots: \{ index: false, follow: false, noarchive: true \}/);
assert.match(page, /Borrador pendiente de aprobación/);
assert.match(page, /20 € una sola vez por pedido aprobado/);
assert.match(page, /30 días posteriores a la entrega/);
assert.match(page, /7 días naturales/);
assert.match(page, /una frontal y otra lateral o en/);
assert.match(page, /tres imágenes más/);
assert.match(page, /revisión jurídica/);
assert.match(page, /SIMULACIÓN — SIN REEMBOLSO/);
assert.match(page, /promoción remunerada exige su aceptación/);
assert.match(page, /mera recepción de imágenes no concede/);
assert.match(page, /no exclusiva/);
assert.match(page, /mundial/);
assert.match(page, /cinco años desde su aceptación/);
assert.match(page, /conserva la titularidad/);
assert.match(page, /recortar las fotografías/);
assert.match(page, /sin.*explotación comercial independiente/s);
assert.match(page, /RGPD/);
assert.match(page, /mailto:admin@metalwolft\.com/);
assert.match(page, /href="\/politica-privacidad"/);

console.log("Customer photo promotion terms route assertions passed");
