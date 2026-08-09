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

  assert.equal(rules[0].source, "/:path*");
  assert.match(csp, /default-src 'self'/);
  assert.match(csp, /frame-ancestors 'self'/);
  assert.match(csp, /connect-src 'self' https:\/\/api\.metalwolft\.com/);
  assert.match(csp, /https:\/\/res\.cloudinary\.com/);
  assert.match(csp, /https:\/\/www\.googletagmanager\.com/);
  assert.match(csp, /https:\/\/www\.google-analytics\.com/);
  assert.match(csp, /https:\/\/js\.stripe\.com/);
  assert.match(csp, /https:\/\/api\.stripe\.com/);
  assert.match(csp, /https:\/\/hooks\.stripe\.com/);
  assert.match(csp, /https:\/\/\*\.paypal\.com/);
  assert.doesNotMatch(csp, /trusted-types|require-trusted-types-for/);
  assert.equal(headers["X-Frame-Options"], "SAMEORIGIN");
  assert.equal(headers["Cross-Origin-Opener-Policy"], "same-origin-allow-popups");
  assert.equal(headers["Strict-Transport-Security"], "max-age=31536000");

  console.log("13 security header assertions passed");
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
