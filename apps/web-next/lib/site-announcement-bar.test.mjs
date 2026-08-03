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

assert.match(announcement, /Envío gratis a partir de 150 €/);
assert.match(
  announcement,
  /Envío gratuito en pedidos estándar a partir de 150 €\. Los pedidos de\s+grandes dimensiones o que requieran transporte especial pueden tener un\s+coste adicional\./s
);
assert.match(announcement, /<details className="mw-announcement__details">/);
assert.match(announcement, /<summary className="mw-announcement__summary">/);
assert.match(announcement, /Consultar condiciones del envío gratuito/);
assert.match(announcement, /aria-hidden="true"/);
assert.match(announcement, /focusable="false"/);
assert.doesNotMatch(announcement, /"use client"|alert\s*\(|useState|onClick/);
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
  /\.mw-announcement__summary\s*{[^}]*width:\s*30px;[^}]*height:\s*30px;[^}]*cursor:\s*pointer;/s
);
assert.match(styles, /\.mw-announcement__summary:focus-visible\s*{[^}]*outline:\s*2px solid #ffffff;/s);
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
assert.match(styles, /@media \(max-width: 380px\)[\s\S]*?\.mw-announcement__copy\s*{[^}]*font-size:\s*0\.76rem/s);

assert.match(checkoutService, /SHIPPING_THRESHOLD = 150\.0/);
assert.ok(
  checkoutService.indexOf('if has_type_b:') <
    checkoutService.indexOf('if subtotal >= SHIPPING_THRESHOLD:')
);
assert.ok(
  checkoutService.indexOf('if has_type_a:') <
    checkoutService.indexOf('if subtotal >= SHIPPING_THRESHOLD:')
);

const dependencies = {
  ...JSON.parse(packageJson).dependencies,
  ...JSON.parse(packageJson).devDependencies
};
assert.equal(dependencies["lucide-react"], undefined);

console.log("Site announcement bar assertions passed");
