import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import ts from "typescript";

const helperSource = readFileSync(new URL("./customer-profile.ts", import.meta.url), "utf8");
const helperOutput = ts.transpileModule(helperSource, {
  compilerOptions: {
    module: ts.ModuleKind.ESNext,
    target: ts.ScriptTarget.ES2022
  }
}).outputText;
const profileHelpers = await import(
  `data:text/javascript;base64,${Buffer.from(helperOutput).toString("base64")}`
);

const overviewSource = readFileSync(
  new URL("../components/account/AccountOverview.tsx", import.meta.url),
  "utf8"
);
const clientSource = readFileSync(new URL("./customer-profile-client.ts", import.meta.url), "utf8");
const authSource = readFileSync(new URL("./auth-client.ts", import.meta.url), "utf8");

const user = {
  id: 1,
  email: "ana@example.com",
  firstname: "Ana",
  lastname: "Martín",
  phone: "600123123",
  billing_address: "Calle Fiscal 1",
  billing_city: "Ciudad Real",
  billing_postal_code: "13001",
  shipping_address: null,
  shipping_city: null,
  shipping_postal_code: null
};

const initialDraft = profileHelpers.buildCustomerProfileDraft(user);
assert.equal(initialDraft.phone, "600123123");
assert.equal(initialDraft.email, "ana@example.com");

const typingDraft = profileHelpers.updateCustomerProfileDraftField(
  initialDraft,
  "firstname",
  "  Ana María  "
);
assert.equal(typingDraft.firstname, "  Ana María  ");

const outgoingUpdate = profileHelpers.buildCustomerProfileUpdate(typingDraft);
assert.equal(outgoingUpdate.firstname, "Ana María");
assert.equal(outgoingUpdate.phone, "600123123");
assert.equal(Object.hasOwn(outgoingUpdate, "email"), false);

const invalidPhone = profileHelpers.validateCustomerProfileDraft({
  ...initialDraft,
  phone: "1".repeat(51)
});
assert.equal(invalidPhone.isValid, false);
assert.match(invalidPhone.errors.phone, /50 caracteres/);

assert.match(authSource, /phone\?: string \| null/);
assert.match(clientSource, /fetch\(`\$\{getApiBaseUrl\(\)\}\/api\/me`/);
assert.match(clientSource, /method: "PATCH"/);
assert.match(overviewSource, />\s*Editar datos\s*</);
assert.match(overviewSource, /"Guardar cambios"/);
assert.match(overviewSource, />\s*Cancelar\s*</);
assert.match(overviewSource, /readOnly type="email"/);
assert.match(overviewSource, /updateCustomerProfile\(/);
assert.match(overviewSource, /saveSession\(token, updatedProfile\)/);
assert.match(overviewSource, /setDraft\(buildCustomerProfileDraft\(profile\)\)/);
assert.doesNotMatch(overviewSource, /onChange=.*trim\(/);

console.log("Customer profile assertions passed");
