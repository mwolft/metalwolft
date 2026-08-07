import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [accountMenu, navigation, styles] = await Promise.all([
  readFile(
    new URL("../components/layout/HeaderAccountMenu.tsx", import.meta.url),
    "utf8"
  ),
  readFile(
    new URL("../components/layout/SiteHeaderNavigation.tsx", import.meta.url),
    "utf8"
  ),
  readFile(new URL("../app/globals.css", import.meta.url), "utf8")
]);

assert.match(accountMenu, /const \{ user, isAuthenticated, isReady, logout \} = useAuthSession\(\)/);
assert.match(accountMenu, /typeof firstname !== "string"/);
assert.match(accountMenu, /firstname\.trim\(\)\.replace\(\/\\s\+\/g, " "\)/);
assert.match(accountMenu, /return normalizedFirstname \? `Hola, \$\{normalizedFirstname\}` : "Mi cuenta"/);
assert.match(accountMenu, /getAccountLabel\(user\?\.firstname\)/);
assert.doesNotMatch(accountMenu, /getAccountLabel\(user\?\.email\)|Hola, \$\{user\?\.email/);

assert.match(accountMenu, /<span className="mw-account-menu__summary-label">\{accountLabel\}<\/span>/);
assert.match(accountMenu, />Tu cuenta<\/p>/);
assert.match(accountMenu, /href="\/mi-cuenta"/);
assert.match(accountMenu, /href="\/mi-cuenta\/pedidos"/);
assert.match(accountMenu, />\s*Resumen\s*<\/Link>/s);
assert.match(accountMenu, />\s*Mis pedidos\s*<\/Link>/s);
assert.match(accountMenu, />\s*Cerrar sesión\s*<\/button>/s);
assert.match(accountMenu, /logout\(\);/);

assert.match(accountMenu, /<summary[\s\S]*aria-expanded=\{isOpen\}/);
assert.match(accountMenu, /Abrir menú de cuenta/);
assert.match(accountMenu, /Cerrar menú de cuenta/);
assert.match(accountMenu, /event\.key === "Escape"/);
assert.match(accountMenu, /!menuRef\.current\?\.contains\(event\.target as Node\)/);
assert.match(accountMenu, /variant === "mobile"[\s\S]*?>\s*Mi cuenta\s*<\/Link>/);

assert.match(styles, /\.mw-account-menu__summary\s*{[^}]*max-width:\s*clamp\(7\.5rem, 12vw, 10\.5rem\);/s);
assert.match(styles, /\.mw-account-menu__summary-label\s*{[^}]*text-overflow:\s*ellipsis;[^}]*white-space:\s*nowrap;/s);
assert.match(styles, /\.mw-account-menu__panel\s*{[^}]*width:\s*min\(260px, calc\(100vw - 2rem\)\);/s);
assert.match(styles, /\.mw-account-menu__action\s*{[^}]*color:\s*var\(--mw-muted\);[^}]*font-weight:\s*600;/s);
assert.match(styles, /\.mw-account-menu__action--logout\s*{[^}]*border-top:\s*1px solid/s);

assert.match(navigation, /<HeaderCartLink \/>/);
assert.match(navigation, /href=\{headerPrimaryCta\.href\}/);
assert.match(navigation, /\{headerPrimaryCta\.label\}/);

console.log("Header account menu assertions passed");
