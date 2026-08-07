import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [navigation, styles] = await Promise.all([
  readFile(
    new URL("../components/layout/SiteHeaderNavigation.tsx", import.meta.url),
    "utf8"
  ),
  readFile(new URL("../app/globals.css", import.meta.url), "utf8")
]);

assert.match(navigation, /^"use client";/);
assert.match(navigation, /const \[isMenuOpen, setIsMenuOpen\] = useState\(false\)/);
assert.match(navigation, /useRef<HTMLDivElement>\(null\)/);
assert.match(navigation, /useRef<HTMLButtonElement>\(null\)/);

assert.match(navigation, /<button\s+className="mw-nav-toggle"/s);
assert.match(navigation, /type="button"/);
assert.match(navigation, /aria-controls=\{NAVIGATION_ID\}/);
assert.match(navigation, /aria-expanded=\{isMenuOpen\}/);
assert.match(navigation, /Abrir navegación principal/);
assert.match(navigation, /Cerrar navegación principal/);
assert.match(navigation, /onClick=\{\(\) => setIsMenuOpen\(\(current\) => !current\)\}/);
assert.match(navigation, /data-open=\{isMenuOpen\}/);
assert.doesNotMatch(navigation, /<details|<summary|onToggle=/);

assert.match(navigation, /const closeMenu = \(shouldRestoreFocus = false\) => \{\s+setIsMenuOpen\(false\);/s);
assert.match(navigation, /toggleRef\.current\?\.focus\(\)/);
assert.match(navigation, /event\.key === "Escape"/);
assert.match(navigation, /event\.key !== "Tab"/);

assert.match(navigation, /if \(!isMenuOpen \|\| !disclosureElement\) \{\s+return undefined;\s+\}/s);
assert.match(navigation, /!disclosureElement\.contains\(event\.target\)/);
assert.match(navigation, /const handleScroll = \(\) => \{\s+closeMenu\(false\);\s+\}/s);
for (const eventName of ["pointerdown", "keydown"]) {
  assert.match(navigation, new RegExp(`document\\.addEventListener\\("${eventName}"`));
  assert.match(navigation, new RegExp(`document\\.removeEventListener\\("${eventName}"`));
}
assert.match(navigation, /window\.addEventListener\("scroll", handleScroll/);
assert.match(navigation, /window\.removeEventListener\("scroll", handleScroll/);
assert.doesNotMatch(navigation, /touchstart|BODY_OPEN_CLASS|mw-nav-open/);

assert.match(navigation, /renderNavigationLinks\(\(\) => closeMenu\(false\)\)/);
assert.match(navigation, /variant="mobile" onNavigate=\{\(\) => closeMenu\(false\)\}/);
assert.match(navigation, /href=\{headerPrimaryCta\.href\}\s+onClick=\{\(\) => closeMenu\(false\)\}/s);

assert.match(styles, /\.mw-nav-toggle\[aria-expanded="true"\] > span:nth-child\(1\)/);
assert.match(styles, /\.mw-nav-toggle\[aria-expanded="true"\] > span:nth-child\(2\)/);
assert.match(styles, /\.mw-nav-toggle\[aria-expanded="true"\] > span:nth-child\(3\)/);
assert.match(
  styles,
  /\.mw-nav-disclosure\[data-open="true"\] \.mw-nav-shell--mobile\s*{\s*display:\s*flex;/s
);
assert.doesNotMatch(styles, /body\.mw-nav-open/);

console.log("Site header navigation assertions passed");
