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
  /Con un taladro y la tornillería especial incluida, sin necesidad de realizar obra\./
);
assert.doesNotMatch(home, /Sin instalación incluida/);
assert.doesNotMatch(home, /Se instala fácilmente/);
const trustSection = home.match(/<section className="mw-home-trust"[\s\S]*?<\/section>/)?.[0] ?? "";

for (const imagePath of [
  "/icons/rejas-a-medida.webp",
  "/icons/envios-peninsula.webp",
  "/icons/soporte- whatsApp.webp",
  "/icons/sin-obra.webp"
]) {
  assert.match(home, new RegExp(`src="${imagePath.replace(".", "\\.")}"`));
}
assert.equal((home.match(/className="mw-home-trust__icon"/g) || []).length, 4);
assert.equal((trustSection.match(/width=\{84\}/g) || []).length, 4);
assert.equal((trustSection.match(/height=\{56\}/g) || []).length, 4);
assert.doesNotMatch(home, /lucide-react/);
assert.equal((trustSection.match(/alt=""/g) || []).length, 4);
assert.match(trustSection, /href=\{contactLinks\.whatsapp\}/);
assert.match(trustSection, /rel="noopener noreferrer"/);
assert.match(trustSection, /target="_blank"/);
assert.match(trustSection, /<strong>\s*<a[\s\S]*?>\s*Ayuda por WhatsApp\s*<\/a>\s*<\/strong>/);
assert.doesNotMatch(trustSection, />\s*Hablar por WhatsApp\s*</);
assert.doesNotMatch(home, /^"use client";/);

assert.match(contact, /whatsapp:\s*`https:\/\/wa\.me\/\$\{contactDetails\.phoneRaw\}/);
assert.match(styles, /\.mw-home-trust__icon\s*{[^}]*width:\s*84px;[^}]*height:\s*56px;[^}]*object-fit:\s*contain/s);
const trustLinkStyles = styles.match(/\.mw-home-trust__link\s*{([^}]*)}/)?.[1] ?? "";
assert.doesNotMatch(trustLinkStyles, /min-height|margin-top|padding-top/);

const dependencies = {
  ...JSON.parse(packageJson).dependencies,
  ...JSON.parse(packageJson).devDependencies
};
assert.equal(Object.keys(dependencies).some((name) => /lucide|heroicons|tabler/i.test(name)), false);

console.log("Home trust assertions passed");
