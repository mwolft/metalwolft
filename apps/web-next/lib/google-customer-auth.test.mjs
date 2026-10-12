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
  assert.match(read("components/auth/GoogleIdentityButton.tsx"), /mode === "login" \? 400 : 320/);
});

test("linking keeps the local session and requires a password", () => {
  const source = read("components/auth/GoogleIdentityButton.tsx");
  assert.match(read("components/account/AccountOverview.tsx"), /<GoogleIdentityButton mode="link" \/>/);
  assert.match(source, /getToken\(\)/);
  assert.match(source, /password: passwordRef\.current/);
  assert.match(source, /\/api\/auth\/google\/link/);
});

test("the content security policy permits only the GIS script and frame origin", () => {
  const csp = read("next.config.mjs");
  assert.match(csp, /https:\/\/accounts\.google\.com\/gsi\/client/);
  assert.match(csp, /frame-src 'self' https:\/\/accounts\.google\.com/);
});
