import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [analytics, banner, gtm, footer] = await Promise.all([
  readFile(new URL("./analytics.ts", import.meta.url), "utf8"),
  readFile(new URL("../components/analytics/CookieConsentBanner.tsx", import.meta.url), "utf8"),
  readFile(new URL("../components/analytics/GtmAnalytics.tsx", import.meta.url), "utf8"),
  readFile(new URL("../components/layout/SiteFooter.tsx", import.meta.url), "utf8")
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

console.log("13 cookie consent assertions passed");
