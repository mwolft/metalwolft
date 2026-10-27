import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import ts from "typescript";

const source = readFileSync(new URL("./change-password.ts", import.meta.url), "utf8");
const output = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 }
}).outputText;
const { validatePasswordChange, passwordChangeError } = await import(
  `data:text/javascript;base64,${Buffer.from(output).toString("base64")}`
);

assert.equal(validatePasswordChange("old-password", "new-password", "new-password"), null);
assert.match(validatePasswordChange("", "new-password", "new-password"), /tres campos/);
assert.match(validatePasswordChange("old-password", "new-password", "different"), /no coinciden/);
assert.match(validatePasswordChange("same-pass", "same-pass", "same-pass"), /distinta/);
assert.match(validatePasswordChange("old-password", "1234567", "1234567"), /8 y 72 bytes/);
assert.equal(validatePasswordChange("old-password", "á".repeat(36), "á".repeat(36)), null);
assert.match(validatePasswordChange("old-password", "á".repeat(37), "á".repeat(37)), /8 y 72 bytes/);
assert.match(passwordChangeError(403), /actual es incorrecta/);
assert.match(passwordChangeError(429), /Demasiados intentos/);

const form = readFileSync(new URL("../components/account/AccountSecurity.tsx", import.meta.url), "utf8");
const profile = readFileSync(new URL("./customer-profile-client.ts", import.meta.url), "utf8");
const profileOutput = ts.transpileModule(
  profile.replace('import { getApiBaseUrl } from "@/lib/api";', ""),
  { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 } }
).outputText;
const { parseCustomerProfile } = await import(
  `data:text/javascript;base64,${Buffer.from(profileOutput).toString("base64")}`
);
const baseProfile = {
  id: 1,
  email: "test@example.invalid",
  firstname: null,
  lastname: null,
  phone: null,
  shipping_address: null,
  shipping_city: null,
  shipping_postal_code: null,
  billing_address: null,
  billing_city: null,
  billing_postal_code: null,
  CIF: null
};
assert.equal(parseCustomerProfile({ ...baseProfile, has_password: true }).has_password, true);
assert.equal(parseCustomerProfile({ ...baseProfile, has_password: false }).has_password, false);
assert.equal(parseCustomerProfile(baseProfile).has_password, undefined);
assert.throws(() => parseCustomerProfile({ ...baseProfile, has_password: null }));
assert.match(form, /current_password: current, new_password: next/);
assert.match(form, /clearSession\(\);\s*window\.location\.replace\("\/login\?password_changed=1/);
assert.match(form, /hasPassword === false/);
assert.match(form, /hasPassword === true/);
assert.match(form, /no está disponible temporalmente/);
assert.match(profile, /payload\.has_password !== undefined && typeof payload\.has_password !== "boolean"/);
console.log("Account security assertions passed");
