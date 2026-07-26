import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";

const sources = Object.fromEntries(
  await Promise.all(
    [
      ["component", "../components/catalog/CategoryFeatureGrid.tsx"],
      ["category", "../app/rejas-para-ventanas/page.tsx"],
      ["styles", "../app/globals.css"]
    ].map(async ([name, path]) => [name, await readFile(new URL(path, import.meta.url), "utf8")])
  )
);

const expectedContent = [
  [
    "Medidas personalizadas",
    "Indica el alto y el ancho necesarios para adaptar la fabricación al hueco de tu ventana."
  ],
  [
    "Colores y acabados",
    "Selecciona entre las opciones habilitadas para el modelo durante la configuración."
  ],
  [
    "Opciones de anclaje",
    "Elige el sistema de fijación adecuado entre las alternativas disponibles al configurar la reja."
  ],
  [
    "Presupuesto calculado",
    "El precio se calcula según el modelo, las medidas, el anclaje y la cantidad seleccionada."
  ]
];

const expectedIcons = [
  ["Medidas personalizadas", "/icons/rejas-a-medida-sin-obra.webp"],
  ["Colores y acabados", "/icons/acabados-en-rejas-para-ventanas.webp"],
  ["Opciones de anclaje", "/icons/rejas-sin-obra.webp"],
  ["Presupuesto calculado", "/icons/precio-de-rejas-para-ventanas.webp"]
];

assert.match(sources.component, /export type CategoryFeatureItem/);
assert.match(sources.component, /items: readonly CategoryFeatureItem\[\]/);
assert.match(sources.component, /iconSrc: string/);
assert.match(sources.component, /if \(items\.length === 0\)/);
assert.match(sources.component, /<Image alt="" height=\{80\} src=\{item\.iconSrc\} width=\{80\} \/>/);
assert.match(sources.component, /<h3>{item\.title}<\/h3>/);
assert.doesNotMatch(
  sources.component,
  /"use client"|<Link\b|<a\b|<button\b|\bfetch\s*\(|lucide|placeholder/i
);

assert.match(sources.category, /title="Configura tu reja a medida"/);
assert.match(
  sources.category,
  /introduction="Cada modelo se adapta a las medidas y opciones elegidas al realizar el pedido\."/
);
for (const [title, description] of expectedContent) {
  assert.ok(sources.category.includes(title));
  assert.ok(sources.category.includes(description));
}
for (const [title, iconSrc] of expectedIcons) {
  assert.ok(sources.category.indexOf(title) < sources.category.indexOf(iconSrc));
  await access(new URL(`../public${iconSrc}`, import.meta.url));
}

assert.equal((sources.category.match(/<CategoryFeatureGrid\b/g) || []).length, 1);
assert.equal((sources.category.match(/<h1\b/g) || []).length, 1);
assert.equal((sources.category.match(/data\.products\.map/g) || []).length, 1);
assert.ok(sources.category.indexOf('id="modelos-reales"') < sources.category.indexOf("<CategoryFeatureGrid"));
assert.ok(
  sources.category.indexOf("<CategoryFeatureGrid") <
    sources.category.indexOf("Cómo elegir una reja para tu ventana")
);

assert.match(
  sources.styles,
  /\.mw-category-feature-grid\s*{[^}]*grid-template-columns:\s*repeat\(2, minmax\(0, 1fr\)\)/s
);
assert.match(
  sources.styles,
  /\.mw-category-feature-grid__icon\s*{[^}]*width:\s*72px;[^}]*height:\s*72px;/s
);
assert.match(
  sources.styles,
  /\.mw-category-feature-grid__icon img\s*{[^}]*object-fit:\s*contain;/s
);
assert.match(
  sources.styles,
  /@media \(max-width: 640px\)[\s\S]*?\.mw-category-feature-grid__icon\s*{[^}]*width:\s*56px;[^}]*height:\s*56px;[\s\S]*?\.mw-category-feature-grid\s*{[^}]*grid-template-columns:\s*1fr/s
);

console.log("CategoryFeatureGrid assertions passed");
