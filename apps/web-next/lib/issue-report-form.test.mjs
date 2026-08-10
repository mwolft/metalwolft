import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const pageSource = readFileSync(
  new URL("../app/formulario-incidencias/page.tsx", import.meta.url),
  "utf8"
);
const formSource = readFileSync(
  new URL("../components/contact/IssueReportForm.tsx", import.meta.url),
  "utf8"
);
const policySource = readFileSync(
  new URL("../app/politica-devolucion/page.tsx", import.meta.url),
  "utf8"
);

assert.match(pageSource, /export const metadata: Metadata/);
assert.match(pageSource, /robots: \{ index: false, follow: false \}/);
assert.match(pageSource, /<IssueReportForm\s*\/>/);
assert.match(formSource, /new FormData\(\)/);
assert.match(formSource, /body\.append\("name", values\.name\)/);
assert.match(formSource, /body\.append\("email", values\.email\)/);
assert.match(formSource, /body\.append\("order_number", values\.order_number\)/);
assert.match(formSource, /body\.append\("issue_type", values\.issue_type\)/);
assert.match(formSource, /body\.append\("message", values\.message\)/);
assert.match(formSource, /body\.append\("images", image\.file\)/);
assert.match(formSource, /\/api\/email\/report-issue/);
assert.match(formSource, /Pintura o acabado/);
assert.match(formSource, /Medidas o encaje/);
assert.match(formSource, /Transporte o embalaje/);
assert.match(formSource, /MAX_IMAGES = 3/);
assert.match(formSource, /URL\.createObjectURL/);
assert.match(formSource, /URL\.revokeObjectURL/);
assert.match(formSource, /function removeImage/);
assert.match(formSource, /Incidencia enviada correctamente\. Te contactaremos en breve\./);
assert.match(formSource, /if \(!response\.ok\)/);
assert.match(formSource, /type: "error"/);
assert.match(formSource, /aria-live="polite"/);
assert.equal(
  [...policySource.matchAll(/href="\/formulario-incidencias"/g)].length,
  2
);

console.log("Issue report form assertions passed");
