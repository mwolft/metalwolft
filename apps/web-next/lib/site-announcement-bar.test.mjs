import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [announcement, header, styles, packageJson, checkoutService] = await Promise.all([
  readFile(
    new URL("../components/layout/SiteAnnouncementBar.tsx", import.meta.url),
    "utf8"
  ),
  readFile(new URL("../components/layout/SiteHeader.tsx", import.meta.url), "utf8"),
  readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
  readFile(new URL("../package.json", import.meta.url), "utf8"),
  readFile(new URL("../../../src/api/checkout_service.py", import.meta.url), "utf8")
]);

assert.match(announcement, /^"use client";/);
assert.match(announcement, /useEffect, useId, useRef, useState/);
assert.match(announcement, /Envío gratis a partir de 150 €/);
assert.match(
  announcement,
  /Envío gratuito en pedidos estándar a partir de 150 €\. Los pedidos de\s+grandes dimensiones o que requieran transporte especial pueden tener un\s+coste adicional\./s
);

assert.match(announcement, /const \[isOpen, setIsOpen\] = useState\(false\)/);
assert.match(announcement, /if \(!isOpen\) \{\s+return;\s+\}/s);
assert.match(announcement, /onClick=\{\(\) => setIsOpen\(\(current\) => !current\)\}/);
assert.match(announcement, /!popoverRef\.current\?\.contains\(event\.target\)/);
assert.match(announcement, /event\.key !== "Escape"/);
assert.match(announcement, /triggerRef\.current\?\.focus\(\)/);
assert.match(announcement, /const handleScroll = \(\) => \{\s+setIsOpen\(false\);\s+\}/s);

for (const eventName of ["pointerdown", "keydown"]) {
  assert.match(announcement, new RegExp(`document\\.addEventListener\\("${eventName}"`));
  assert.match(announcement, new RegExp(`document\\.removeEventListener\\("${eventName}"`));
}
assert.match(announcement, /window\.addEventListener\("scroll", handleScroll/);
assert.match(announcement, /window\.removeEventListener\("scroll", handleScroll/);

assert.match(announcement, /<button/);
assert.match(announcement, /type="button"/);
assert.match(announcement, /aria-expanded=\{isOpen\}/);
assert.match(announcement, /aria-controls=\{popoverId\}/);
assert.match(announcement, /aria-label="Información sobre condiciones de envío"/);
assert.match(announcement, /aria-hidden=\{!isOpen\}/);
assert.match(announcement, /data-open=\{isOpen\}/);
assert.match(announcement, /aria-hidden="true"/);
assert.match(announcement, /focusable="false"/);
assert.doesNotMatch(announcement, /<details|<summary|role="dialog"/);
assert.doesNotMatch(announcement, /alert\s*\(|>\s*(Cerrar|Aceptar)\s*</i);
assert.doesNotMatch(announcement, /<h[1-6]/);

assert.match(
  header,
  /import \{ SiteAnnouncementBar \} from "@\/components\/layout\/SiteAnnouncementBar";/
);
assert.ok(header.indexOf("<SiteAnnouncementBar />") < header.indexOf("<PageContainer>"));

assert.match(styles, /--mw-announcement-height:\s*36px/);
assert.match(styles, /--mw-header-nav-height:\s*82px/);
assert.match(
  styles,
  /--mw-header-total-height:\s*calc\(\s*var\(--mw-announcement-height\) \+ var\(--mw-header-nav-height\)\s*\)/s
);
assert.match(
  styles,
  /--mw-sticky-content-top:\s*calc\(var\(--mw-header-total-height\) \+ 28px\)/
);
assert.match(styles, /\.mw-announcement\s*{[^}]*background:\s*#cf1c35;[^}]*color:\s*#ffffff;/s);
assert.match(
  styles,
  /\.mw-announcement__trigger\s*{[^}]*width:\s*30px;[^}]*height:\s*30px;[^}]*cursor:\s*pointer;/s
);
assert.match(styles, /\.mw-announcement__trigger:focus-visible\s*{[^}]*outline:\s*2px solid #ffffff;/s);
assert.match(styles, /\.mw-announcement__panel\s*{[^}]*width:\s*min\(24rem, 90vw\);/s);
assert.match(styles, /opacity:\s*0;[^}]*transform:\s*translate\(-50%, -4px\);[^}]*visibility:\s*hidden;/s);
assert.match(
  styles,
  /\.mw-announcement__panel\[data-open="true"\]\s*{[^}]*opacity:\s*1;[^}]*transform:\s*translate\(-50%, 0\);[^}]*visibility:\s*visible;/s
);
assert.match(styles, /opacity 160ms ease/);
assert.match(
  styles,
  /@media \(prefers-reduced-motion: reduce\)[\s\S]*?\.mw-announcement__trigger,[\s\S]*?\.mw-announcement__panel\s*{\s*transition:\s*none;/s
);
assert.match(styles, /\.mw-header\s*{[^}]*position:\s*sticky;[^}]*top:\s*0;/s);
assert.match(
  styles,
  /html\s*{[^}]*scroll-padding-top:\s*calc\(var\(--mw-header-total-height\) \+ 1rem\);/s
);
assert.equal((styles.match(/top:\s*var\(--mw-sticky-content-top\);/g) || []).length, 3);
assert.doesNotMatch(styles, /top:\s*110px/);
assert.match(
  styles,
  /@media \(max-width: 900px\)\s*{\s*:root\s*{\s*--mw-header-nav-height:\s*78px;/s
);
assert.match(
  styles,
  /@media \(max-width: 380px\)[\s\S]*?\.mw-announcement__copy\s*{[^}]*font-size:\s*0\.76rem/s
);

assert.match(checkoutService, /SHIPPING_THRESHOLD = 150\.0/);
assert.ok(
  checkoutService.indexOf("if has_type_b:") <
    checkoutService.indexOf("if subtotal >= SHIPPING_THRESHOLD:")
);
assert.ok(
  checkoutService.indexOf("if has_type_a:") <
    checkoutService.indexOf("if subtotal >= SHIPPING_THRESHOLD:")
);

const dependencies = {
  ...JSON.parse(packageJson).dependencies,
  ...JSON.parse(packageJson).devDependencies
};
assert.equal(dependencies["lucide-react"], undefined);

console.log("Site announcement popover assertions passed");
