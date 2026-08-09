import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [analytics, banner, gtm, footer, styles] = await Promise.all([
  readFile(new URL("./analytics.ts", import.meta.url), "utf8"),
  readFile(new URL("../components/analytics/CookieConsentBanner.tsx", import.meta.url), "utf8"),
  readFile(new URL("../components/analytics/GtmAnalytics.tsx", import.meta.url), "utf8"),
  readFile(new URL("../components/layout/SiteFooter.tsx", import.meta.url), "utf8"),
  readFile(new URL("../app/globals.css", import.meta.url), "utf8")
]);

assert.match(analytics, /storedConsent === "all"/);
assert.match(analytics, /storedConsent === "necessary" \|\| storedConsent === "essential"/);
assert.match(analytics, /setItem\(ANALYTICS_CONSENT_STORAGE_KEY, consent\)/);
assert.match(analytics, /event: "consent_update"/);
assert.match(analytics, /analytics_storage: storage/);
assert.match(analytics, /dispatchEvent\(new Event\(ANALYTICS_CONSENT_CHANGED_EVENT\)\)/);
assert.match(banner, /getAnalyticsConsent\(\) === null/);
assert.match(banner, /saveConsent\("all"\)/);
assert.match(banner, /saveConsent\("necessary"\)/);
assert.match(banner, /href="\/politica-de-cookies"/);
assert.match(gtm, /addEventListener\(ANALYTICS_CONSENT_CHANGED_EVENT, updateConsent\)/);
assert.match(gtm, /setIsEnabled\(hasAnalyticsConsent\(\)\)/);
assert.match(footer, /<CookieConsentSettingsButton \/>/);
assert.match(styles, /\.mw-cookie-consent\s*{[^}]*right: 0;[^}]*bottom: 0;[^}]*left: 0;/s);
assert.match(styles, /\.mw-cookie-consent__content\s*{[^}]*justify-content: center;[^}]*width: 100%;[^}]*linear-gradient\(135deg, #757575 0%, #666666 100%\)/s);
assert.match(styles, /\.mw-cookie-consent__actions \.mw-button--primary\s*{[^}]*background: #cf1c35/s);
assert.match(styles, /\.mw-cookie-consent__actions \.mw-button--secondary\s*{[^}]*background: transparent/s);

console.log("16 cookie consent assertions passed");
