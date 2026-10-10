import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const page = readFileSync(join(process.cwd(), "app/condiciones-promocion-fotos/page.tsx"), "utf8");
const privacy = readFileSync(join(process.cwd(), "app/politica-privacidad/page.tsx"), "utf8");

assert.match(page, /const PATH = "\/condiciones-promocion-fotos"/);
assert.match(page, /export default function CustomerPhotoPromotionTermsPage/);
assert.match(page, /robots: \{ index: false, follow: false, noarchive: true \}/);
assert.doesNotMatch(page, /Borrador pendiente de aprobación/);
assert.match(page, /20 € una sola vez por pedido aprobado/);
assert.match(page, /30 días naturales desde la fecha\s+real de entrega/);
assert.match(page, /7 días naturales desde la recepción acreditada/);
assert.match(page, /una frontal y otra lateral o en/);
assert.match(page, /tres imágenes más/);
assert.match(page, /registrar\s+tu oposición/);
assert.match(page, /promoción remunerada exige su aceptación/);
assert.match(page, /mera recepción de imágenes no concede/);
assert.match(page, /no exclusiva/);
assert.match(page, /mundial/);
assert.match(page, /cinco años desde su aceptación/);
assert.match(page, /conserva la titularidad/);
assert.match(page, /recortar las fotografías/);
assert.match(page, /sin.*explotación comercial independiente/s);
assert.match(page, /RGPD/);
assert.match(page, /garantías de la compra/);
assert.match(page, /recepción acreditada/);
assert.match(page, /alternativa segura/);
assert.match(page, /digitales o impresos/);
assert.match(page, /canales bajo su control/);
assert.match(page, /derechos necesarios sobre las imágenes/);
assert.match(privacy, /Fotografías de clientes/);
assert.match(privacy, /adjuntos en nuestro correo de administración/);
assert.match(privacy, /href="\/condiciones-promocion-fotos"/);
assert.match(page, /mailto:admin@metalwolft\.com/);
assert.match(page, /href="\/politica-privacidad"/);

console.log("Customer photo promotion terms route assertions passed");
