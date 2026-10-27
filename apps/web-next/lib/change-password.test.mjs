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
assert.match(form, /current_password: current, new_password: next/);
assert.match(form, /clearSession\(\);\s*window\.location\.replace\("\/login\?password_changed=1/);
assert.match(form, /hasPassword === false/);
assert.match(profile, /typeof payload\.has_password !== "boolean"/);
console.log("Account security assertions passed");
