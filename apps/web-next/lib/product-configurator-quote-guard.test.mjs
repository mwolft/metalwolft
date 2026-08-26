import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const configuratorSource = await readFile(
  new URL("../components/product/ProductConfigurator.tsx", import.meta.url),
  "utf8"
);

assert.match(configuratorSource, /const physicalOptionsReadyForQuote = Boolean\(/);
assert.match(configuratorSource, /selectedAnchorage\?\.enabled/);
assert.match(configuratorSource, /configuredColors\.some\(\(option\) => option\.value === color\)/);
assert.match(configuratorSource, /screwOption === NOT_APPLICABLE_SCREW_OPTION/);
assert.match(configuratorSource, /configuredScrewOptions\.some\(\(option\) => option\.value === screwOption\)/);
assert.match(configuratorSource, /if \(!physicalOptionsReadyForQuote\) \{/);
assert.match(configuratorSource, /requestProductQuote\(/);

console.log("7 physical quote guard assertions passed");
