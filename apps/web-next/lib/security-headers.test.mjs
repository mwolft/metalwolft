import assert from "node:assert/strict";

const originalNodeEnv = process.env.NODE_ENV;
const originalApiUrl = process.env.NEXT_PUBLIC_API_URL;

process.env.NODE_ENV = "production";
process.env.NEXT_PUBLIC_API_URL = "https://api.metalwolft.com";

try {
  const moduleUrl = new URL("../next.config.mjs", import.meta.url);
  const { default: nextConfig } = await import(`${moduleUrl.href}?security-headers-test`);
  const rules = await nextConfig.headers();
  const headers = Object.fromEntries(rules[0].headers.map(({ key, value }) => [key, value]));
  const csp = headers["Content-Security-Policy"];
  const reportOnlyCsp = headers["Content-Security-Policy-Report-Only"];
  const reportOnlyScriptSrc = reportOnlyCsp.split("; ").find((directive) => directive.startsWith("script-src "));

  assert.equal(rules[0].source, "/:path*");
  assert.match(csp, /default-src 'self'/);
  assert.match(csp, /frame-ancestors 'self'/);
  assert.match(csp, /connect-src 'self' https:\/\/api\.metalwolft\.com/);
  assert.match(csp, /https:\/\/res\.cloudinary\.com/);
  assert.match(csp, /https:\/\/www\.googletagmanager\.com/);
  assert.match(csp, /https:\/\/www\.google-analytics\.com/);
  assert.match(csp, /https:\/\/region1\.analytics\.google\.com/);
  assert.match(csp, /https:\/\/www\.google\.es/);
  assert.match(csp, /https:\/\/js\.stripe\.com/);
  assert.match(csp, /https:\/\/api\.stripe\.com/);
  assert.match(csp, /https:\/\/hooks\.stripe\.com/);
  assert.match(csp, /https:\/\/\*\.paypal\.com/);
  assert.match(csp, /script-src 'self' 'unsafe-inline'/);
  assert.doesNotMatch(csp, /trusted-types|require-trusted-types-for/);
  assert.equal(headers["X-Frame-Options"], "SAMEORIGIN");
  assert.equal(headers["Cross-Origin-Opener-Policy"], "same-origin-allow-popups");
  assert.equal(headers["Strict-Transport-Security"], "max-age=63072000; includeSubDomains");
  assert.doesNotMatch(headers["Strict-Transport-Security"], /preload/);
  assert.ok(reportOnlyCsp);
  assert.ok(reportOnlyScriptSrc);
  assert.doesNotMatch(reportOnlyScriptSrc, /'unsafe-inline'/);
  assert.match(reportOnlyScriptSrc, /https:\/\/www\.googletagmanager\.com/);
  assert.match(reportOnlyCsp, /report-uri https:\/\/api\.metalwolft\.com\/api\/security\/csp-report/);
  assert.match(reportOnlyCsp, /report-to mw-csp/);
  assert.equal(
    headers["Reporting-Endpoints"],
    'mw-csp="https://api.metalwolft.com/api/security/csp-report"'
  );

  console.log("CSP security header assertions passed");
} finally {
  if (originalNodeEnv === undefined) {
    delete process.env.NODE_ENV;
  } else {
    process.env.NODE_ENV = originalNodeEnv;
  }

  if (originalApiUrl === undefined) {
    delete process.env.NEXT_PUBLIC_API_URL;
  } else {
    process.env.NEXT_PUBLIC_API_URL = originalApiUrl;
  }
}
