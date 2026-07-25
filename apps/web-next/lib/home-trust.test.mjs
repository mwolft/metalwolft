import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [home, styles, contact, packageJson] = await Promise.all([
  readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
  readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
  readFile(new URL("./contact.ts", import.meta.url), "utf8"),
  readFile(new URL("../package.json", import.meta.url), "utf8")
]);

for (const title of [
  "Fabricación a medida",
  "Envío peninsular",
  "Ayuda por WhatsApp",
  "Sin instalación incluida"
]) {
  assert.match(home, new RegExp(title));
}

assert.equal((home.match(/<HomeTrustIcon name=/g) || []).length, 4);
assert.match(home, /aria-hidden="true"/);
assert.match(home, /width="28"/);
assert.match(home, /height="28"/);
assert.match(home, /href=\{contactLinks\.whatsapp\}/);
assert.match(home, /rel="noopener noreferrer"/);
assert.match(home, /target="_blank"/);
assert.match(home, />\s*Hablar por WhatsApp\s*</);
assert.doesNotMatch(home, /^"use client";/);

assert.match(contact, /whatsapp:\s*`https:\/\/wa\.me\/\$\{contactDetails\.phoneRaw\}/);
assert.match(styles, /\.mw-home-trust__icon\s*{[^}]*width:\s*28px;[^}]*height:\s*28px/s);
assert.match(styles, /\.mw-home-trust__link\s*{[^}]*min-height:\s*44px/s);

const dependencies = {
  ...JSON.parse(packageJson).dependencies,
  ...JSON.parse(packageJson).devDependencies
};
assert.equal(Object.keys(dependencies).some((name) => /lucide|heroicons|tabler/i.test(name)), false);

console.log("Home trust assertions passed");
