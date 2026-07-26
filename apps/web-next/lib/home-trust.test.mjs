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
  "Instalación sencilla"
]) {
  assert.match(home, new RegExp(title));
}
assert.match(
  home,
  /Se instala fácilmente con un taladro y la tornillería especial incluida, sin\s+necesidad de realizar obra\./
);
assert.doesNotMatch(home, /Sin instalación incluida/);

for (const imagePath of [
  "/icons/rejas-a-medida.webp",
  "/icons/envios-peninsula.webp",
  "/icons/soporte- whatsApp.webp",
  "/icons/sin-obra.webp"
]) {
  assert.match(home, new RegExp(`src="${imagePath.replace(".", "\\.")}"`));
}
assert.equal((home.match(/className="mw-home-trust__icon"/g) || []).length, 4);
assert.equal((home.match(/alt=""/g) || []).length >= 4, true);
assert.equal((home.match(/width=\{84\}/g) || []).length, 4);
assert.equal((home.match(/height=\{56\}/g) || []).length, 4);
assert.doesNotMatch(home, /lucide-react/);
assert.match(home, /href=\{contactLinks\.whatsapp\}/);
assert.match(home, /rel="noopener noreferrer"/);
assert.match(home, /target="_blank"/);
assert.match(home, />\s*Hablar por WhatsApp\s*</);
assert.doesNotMatch(home, /^"use client";/);

assert.match(contact, /whatsapp:\s*`https:\/\/wa\.me\/\$\{contactDetails\.phoneRaw\}/);
assert.match(styles, /\.mw-home-trust__icon\s*{[^}]*width:\s*84px;[^}]*height:\s*56px;[^}]*object-fit:\s*contain/s);
assert.match(styles, /\.mw-home-trust__link\s*{[^}]*min-height:\s*44px/s);

const dependencies = {
  ...JSON.parse(packageJson).dependencies,
  ...JSON.parse(packageJson).devDependencies
};
assert.equal(Object.keys(dependencies).some((name) => /lucide|heroicons|tabler/i.test(name)), false);

console.log("Home trust assertions passed");
