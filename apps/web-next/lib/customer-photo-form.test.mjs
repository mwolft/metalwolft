import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import nextConfig from "../next.config.mjs";

const root = process.cwd();
const page = readFileSync(join(root, "app/fotos-clientes/page.tsx"), "utf8");
const form = readFileSync(join(root, "components/contact/CustomerPhotoForm.tsx"), "utf8");
const analytics = readFileSync(join(root, "components/analytics/GtmAnalytics.tsx"), "utf8");
const config = readFileSync(join(root, "next.config.mjs"), "utf8");

assert.match(page, /robots: \{ index: false, follow: false/);
assert.match(form, /window\.location\.hash\.slice\(1\)/);
assert.match(form, /window\.history\.replaceState/);
assert.match(form, /headers: \{ Authorization: `Bearer \$\{token\.current\}` \}/);
assert.match(form, /commercial_consent/);
assert.match(form, /type="checkbox" name="commercial-consent" checked=\{consent === "yes"\}/);
assert.match(form, /value="no"/);
assert.match(form, /info\.mode === "incentive" \? \(/);
assert.match(form, /type="radio" name="commercial-consent" value="no"/);
assert.match(form, /info\.mode === "incentive" && consent !== "yes"/);
assert.match(form, /Sin aceptar la licencia no puedes participar en la promoción de 20 €/);
assert.match(form, /licencia de explotación fotográfica es distinta del tratamiento de datos personales/);
assert.match(form, /identificar domicilios o terceros/);
assert.match(form, /href="\/politica-privacidad"/);
assert.match(form, /image\/jpeg,image\/png,image\/webp/);
assert.match(form, /MAX_IMAGES|info\.max_images/);
assert.match(form, /Fotografía frontal \(obligatoria\)/);
assert.match(form, /Fotografía lateral o en perspectiva \(obligatoria\)/);
assert.match(form, /Fotografías adicionales \(opcionales, hasta tres\)/);
assert.match(form, /30 días posteriores a la entrega/);
assert.match(form, /7 días naturales/);
assert.match(form, /body\.append\("front_photo"/);
assert.match(form, /body\.append\("perspective_photo"/);
assert.match(form, /body\.append\("additional_photos"/);
assert.match(form, /max_total_bytes/);
assert.match(form, /envían por correo/);
assert.match(form, /pending_confirmation/);
assert.match(form, /info\.is_simulation/);
assert.match(form, /SIMULACIÓN — SIN REEMBOLSO/);
assert.doesNotMatch(form, /consent\/revoke|Retirar autorización comercial<\/button>/);
assert.match(form, /mailto:admin@metalwolft\.com/);
assert.match(form, /\/api\/customer-photos\/opt-out/);
assert.match(form, /registrar tu oposición aquí/);
assert.match(form, /supresión/);
assert.match(analytics, /pathname === "\/fotos-clientes"/);
assert.match(config, /source: "\/fotos-clientes"/);
assert.match(config, /Referrer-Policy.*no-referrer/);
const redirects = await nextConfig.redirects();
const headers = await nextConfig.headers();
assert.equal(redirects.some((route) => route.source === "/fotos-clientes"), false);
assert.deepEqual(
  headers.find((route) => route.source === "/fotos-clientes")?.headers,
  [
    { key: "Referrer-Policy", value: "no-referrer" },
    { key: "X-Robots-Tag", value: "noindex, nofollow, noarchive" }
  ]
);

console.log("Customer photo form source assertions passed");
