import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const home = readFileSync(new URL("../app/page.tsx", import.meta.url), "utf8");
const webPage = home.slice(home.indexOf("function buildWebPageJsonLd"), home.indexOf("function buildItemListJsonLd"));

assert.match(
  webPage,
  /primaryImageOfPage:\s*\{\s*"@type": "ImageObject",\s*url: absoluteUrl\(HERO_IMAGE_PATH\)\s*\}/
);
