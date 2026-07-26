import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

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

assert.match(sources.component, /export type CategoryFeatureItem/);
assert.match(sources.component, /items: readonly CategoryFeatureItem\[\]/);
assert.match(sources.component, /if \(items\.length === 0\)/);
assert.match(sources.component, /<h3>{item\.title}<\/h3>/);
assert.doesNotMatch(sources.component, /"use client"|<Link\b|<a\b|<button\b|\bfetch\s*\(/);

assert.match(sources.category, /title="Configura tu reja a medida"/);
assert.match(
  sources.category,
  /introduction="Cada modelo se adapta a las medidas y opciones elegidas al realizar el pedido\."/
);
for (const [title, description] of expectedContent) {
  assert.ok(sources.category.includes(title));
  assert.ok(sources.category.includes(description));
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
  /@media \(max-width: 640px\)[\s\S]*?\.mw-category-feature-grid\s*{[^}]*grid-template-columns:\s*1fr/s
);

console.log("CategoryFeatureGrid assertions passed");
