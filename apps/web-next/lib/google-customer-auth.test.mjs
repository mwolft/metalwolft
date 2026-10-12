import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import test from "node:test";

const root = path.resolve(import.meta.dirname, "..");
const read = (file) => readFileSync(path.join(root, file), "utf8");

test("login and registration use the same Google Identity Services component", () => {
  assert.match(read("app/login/page.tsx"), /<GoogleIdentityButton mode="login" nextPath={nextPath} \/>/);
  assert.match(read("app/registro/page.tsx"), /<GoogleIdentityButton mode="login" nextPath={nextPath} \/>/);
  assert.match(read("components/auth/GoogleIdentityButton.tsx"), /saveSession\(payload\.access_token, payload\.results\)/);
  assert.match(read("components/auth/GoogleIdentityButton.tsx"), /router\.replace\(getSafeInternalPath\(nextPath\)\)/);
});

test("authentication pages present Google before the email form without a technical sidebar", () => {
  for (const [page, form] of [
    ["app/login/page.tsx", "LoginForm"],
    ["app/registro/page.tsx", "RegisterForm"]
  ]) {
    const source = read(page);
    assert.ok(source.indexOf("<GoogleIdentityButton") < source.indexOf(`<${form} `));
    assert.match(source, /o con tu correo/);
    assert.doesNotMatch(source, /mw-auth-aside/);
  }
  assert.match(read("app/globals.css"), /width: min\(100%, 480px\)/);
  assert.match(read("components/auth/GoogleIdentityButton.tsx"), /Math\.min\(container\.current\.clientWidth \|\| 400, 400\)/);
});

test("linking keeps the local session and requires a password", () => {
  const source = read("components/auth/GoogleIdentityButton.tsx");
  assert.match(read("components/account/AccountOverview.tsx"), /<GoogleIdentityButton mode="link" \/>/);
  assert.match(source, /getToken\(\)/);
  assert.match(source, /password: passwordRef\.current/);
  assert.match(source, /\/api\/auth\/google\/link/);
});

test("linked Google identity has one status message and no linking controls", () => {
  const source = read("components/auth/GoogleIdentityButton.tsx");
  assert.match(source, /linked === true \? <p className="mw-account-google-link__status">Google ya está vinculado a tu cuenta/);
  assert.match(source, /linked === false \? \(\s*<label className="mw-field">/);
  assert.match(source, /mode === "login" \|\| linked === false \? <div className="mw-google-auth__button"/);
  assert.match(source, /if \(mode === "link"\) \{\s*setFeedback\(""\);/);
  assert.match(read("app/globals.css"), /\.mw-account-google-link \.mw-google-auth \{\s*max-width: 400px;/);
});

test("the content security policy permits only the GIS script and frame origin", () => {
  const csp = read("next.config.mjs");
  assert.match(csp, /https:\/\/accounts\.google\.com\/gsi\/client/);
  assert.match(csp, /frame-src 'self' https:\/\/accounts\.google\.com/);
});
