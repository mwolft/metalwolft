import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import {
  DEFAULT_SCREW_OPTION,
  formatScrewConfiguration,
  selectCompatibleScrewOption
} from "./screw-option.ts";


const interiorOptions = [
  { value: "standard", length_mm: 80 },
  { value: "long_150", length_mm: 150 }
];
const plateOptions = [
  { value: "standard", length_mm: 70 },
  { value: "long_150", length_mm: 150 }
];
const garrasOptions = [];

assert.equal(
  selectCompatibleScrewOption("standard", plateOptions),
  "standard",
  "standard must survive an anchorage change"
);
assert.equal(interiorOptions.find(({ value }) => value === "standard")?.length_mm, 80);
assert.equal(plateOptions.find(({ value }) => value === "standard")?.length_mm, 70);
assert.equal(garrasOptions.find(({ value }) => value === "standard")?.length_mm ?? null, null);
assert.equal(
  selectCompatibleScrewOption("long_150", plateOptions),
  "long_150",
  "the explicit long option must survive an anchorage change"
);
assert.equal(
  selectCompatibleScrewOption("future_incompatible", interiorOptions),
  DEFAULT_SCREW_OPTION
);

assert.equal(
  formatScrewConfiguration({ screw_length_mm: 80, screw_supplement: 0 }),
  "80 mm incluidos"
);
assert.equal(
  formatScrewConfiguration({ screw_length_mm: 150, screw_supplement: 8.95 }),
  "150 mm (+8,95 €)"
);
assert.equal(formatScrewConfiguration({ screw_length_mm: null, screw_supplement: 0 }), null);

const configuratorSource = await readFile(
  new URL("../components/product/ProductConfigurator.tsx", import.meta.url),
  "utf8"
);
const cartSource = await readFile(
  new URL("../components/cart/CartView.tsx", import.meta.url),
  "utf8"
);
const checkoutSource = await readFile(
  new URL("../components/cart/CartDetailsStep.tsx", import.meta.url),
  "utf8"
);
const stylesSource = await readFile(new URL("../app/globals.css", import.meta.url), "utf8");

const installationIndex = configuratorSource.indexOf("<span>Instalación</span>");
const screwIndex = configuratorSource.indexOf('className="mw-configurator-screws"');
const colorIndex = configuratorSource.indexOf('className="mw-configurator-colors"');
assert.ok(installationIndex >= 0 && screwIndex > installationIndex && colorIndex > screwIndex);
assert.match(configuratorSource, /type="radio"/);
assert.match(
  configuratorSource,
  /Para fijación directa sobre base maciza\./
);
assert.match(
  configuratorSource,
  /Para revestimientos o mayor profundidad de fijación\./
);
assert.match(
  configuratorSource,
  /¿Qué longitud elegir\?/
);
assert.match(
  configuratorSource,
  /configuredScrewOptions\.find\(\(option\) => option\.value === DEFAULT_SCREW_OPTION\)/
);
assert.match(configuratorSource, /\{standardScrewLength\} mm para fijación directa/);
assert.match(configuratorSource, /selectedAnchorageRequiresScrews && configuredScrewOptions\.length/);
assert.match(
  configuratorSource,
  /standardScrewLength !== null \? \(\s*<p className="mw-configurator-screws__help">/s
);
assert.match(configuratorSource, /screw_option: screwOption/);
assert.match(configuratorSource, /screwOption: isNonEmptyString/);
assert.doesNotMatch(configuratorSource, /8\.95/);
assert.match(cartSource, /formatScrewConfiguration\(item\)/);
assert.match(checkoutSource, /Tornillos: \{screwConfiguration\}/);
assert.match(stylesSource, /\.mw-configurator-screws__options[\s\S]*grid-template-columns: 1fr;/);

console.log("14 screw option tests passed");
