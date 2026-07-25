import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [header, styles] = await Promise.all([
  readFile(new URL("../components/layout/SiteHeader.tsx", import.meta.url), "utf8"),
  readFile(new URL("../app/globals.css", import.meta.url), "utf8")
]);

assert.match(header, /import Image from "next\/image"/);
assert.match(header, /<Link className="mw-brand" href="\/" aria-label="MetalWolft, inicio">/);
assert.match(
  header,
  /<Image\s+className="mw-brand__icon"\s+src="\/icon\.svg"\s+alt=""\s+width=\{48\}\s+height=\{48\}\s+\/>/s
);
assert.match(header, /className="mw-brand__text"/);
assert.equal((header.match(/<Link className="mw-brand"/g) || []).length, 1);
assert.ok(header.indexOf("mw-brand__icon") < header.indexOf("mw-brand__text"));

assert.match(styles, /\.mw-brand\s*{[^}]*align-items:\s*center;[^}]*gap:\s*0\.7rem/s);
assert.match(
  styles,
  /\.mw-brand__icon\s*{[^}]*width:\s*48px;[^}]*height:\s*48px;[^}]*object-fit:\s*contain/s
);
assert.match(
  styles,
  /@media \(max-width: 900px\)[\s\S]*?\.mw-brand__icon\s*{[^}]*width:\s*40px;[^}]*height:\s*40px/s
);

console.log("Site header brand assertions passed");
