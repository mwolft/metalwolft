import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const configuration = JSON.parse(
  readFileSync(new URL("./configurator-configuration-fallback.json", import.meta.url), "utf8")
);
const source = readFileSync(
  new URL("../components/product/ProductConfigurator.tsx", import.meta.url),
  "utf8"
);
const styles = readFileSync(new URL("../app/globals.css", import.meta.url), "utf8");

const enabledColors = configuration.colors.filter((option) => option.enabled);
const colorsByFinish = Object.groupBy(enabledColors, (option) => option.finish);

assert.equal(enabledColors.length, 10);
assert.equal(colorsByFinish.liso.length, 4);
assert.equal(colorsByFinish.forja.length, 6);
assert.deepEqual(
  enabledColors.map((option) => option.value),
  [
    "satinado_blanco",
    "satinado_negro",
    "satinado_gris",
    "satinado_verde",
    "forja_negro",
    "forja_gris",
    "forja_marron",
    "forja_azul",
    "forja_verde",
    "forja_dorado"
  ]
);

assert.match(source, /groups\.get\(option\.finish\)/);
assert.match(source, /label: option\.finish_label/);
assert.match(source, /<fieldset className="mw-configurator-colors">/);
assert.match(source, /<legend>Color<\/legend>/);
assert.match(source, /type="button"/);
assert.match(source, /aria-pressed={color === option\.value}/);
assert.match(source, /className="mw-visually-hidden">{option\.label}/);
assert.match(source, /setColor\(option\.value\)/);
assert.match(source, /invalidateCalculatedPrice\(\)/);
assert.match(source, /color,/);
assert.match(source, /onMouseEnter=\{\(\) => setPreviewColor\(option\.value\)\}/);
assert.match(source, /onFocus=\{\(\) => setPreviewColor\(option\.value\)\}/);
assert.match(source, /onMouseLeave=\{\(\) => setPreviewColor\(null\)\}/);
assert.match(source, /onBlur=\{\(\) => setPreviewColor\(null\)\}/);
assert.match(source, /className={`mw-configurator-color-preview/);
assert.match(source, /selectedColor\?\.label \?\? "Cargando\.\.\."/);
assert.doesNotMatch(source, /Seleccionado:/);

assert.match(styles, /\.mw-configurator-swatches\s*{[^}]*display:\s*flex;[^}]*flex-wrap:\s*wrap;/s);
assert.match(styles, /\.mw-configurator-swatch\s*{[^}]*width:\s*44px;[^}]*height:\s*44px;/s);
assert.match(styles, /\.mw-configurator-swatch__dot\s*{[^}]*width:\s*36px;[^}]*height:\s*36px;/s);
assert.match(styles, /\.mw-configurator-swatch\.is-selected \.mw-configurator-swatch__dot\s*{[^}]*box-shadow:/s);
assert.match(styles, /\.mw-configurator-color-preview\s*{[^}]*width:\s*100%;[^}]*height:\s*72px;/s);
assert.match(styles, /\.mw-configurator-selected-color\s*{[^}]*display:\s*grid;[^}]*gap:\s*0\.4rem;/s);

console.log("25 product color selector assertions passed");
