import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import ts from "typescript";

const checkoutDetailsUrl = new URL("./checkout-details.ts", import.meta.url);
const checkoutDetailsSource = readFileSync(checkoutDetailsUrl, "utf8");
const transpiledCheckoutDetails = ts.transpileModule(checkoutDetailsSource, {
  compilerOptions: {
    module: ts.ModuleKind.ESNext,
    target: ts.ScriptTarget.ES2022
  }
}).outputText;
const checkoutDetails = await import(
  `data:text/javascript;base64,${Buffer.from(transpiledCheckoutDetails).toString("base64")}`
);

const detailsStepSource = readFileSync(
  new URL("../components/cart/CartDetailsStep.tsx", import.meta.url),
  "utf8"
);
const paymentStepSource = readFileSync(
  new URL("../components/cart/CartPaymentStep.tsx", import.meta.url),
  "utf8"
);
const paymentSummarySource = readFileSync(
  new URL("../components/cart/CheckoutPaymentSummary.tsx", import.meta.url),
  "utf8"
);
const stripeSource = readFileSync(
  new URL("../components/cart/StripePaymentForm.tsx", import.meta.url),
  "utf8"
);
const paypalSource = readFileSync(
  new URL("../components/cart/PayPalPaymentForm.tsx", import.meta.url),
  "utf8"
);

const validDetails = {
  ...checkoutDetails.EMPTY_CHECKOUT_CUSTOMER_DETAILS,
  firstname: "Juan",
  lastname: "García López",
  email: "juan@example.com",
  phone: "600123123",
  legal_name: "Juan García López",
  tax_id: "12345678Z",
  billing_address: "Calle Mayor 1",
  billing_city: "Ciudad Real",
  billing_postal_code: "13001",
  acceptedPolicy: true
};

const individual = checkoutDetails.sanitizeCheckoutDetails({
  firstname: "Juan",
  lastname: "García López"
});
assert.equal(individual.billing_type, "individual");
assert.equal(individual.legal_name, "Juan García López");

const editedIndividual = checkoutDetails.sanitizeCheckoutDetails({
  ...individual,
  legal_name: "Juan García López Autónomo"
});
assert.equal(editedIndividual.legal_name, "Juan García López Autónomo");

let companyNameDraft = {
  ...validDetails,
  billing_type: "company",
  legal_name: ""
};
for (const value of [
  "CONSTRUCCIONES ",
  "CONSTRUCCIONES E",
  "CONSTRUCCIONES EJEMPLO SL"
]) {
  companyNameDraft = checkoutDetails.updateCheckoutDraftField(
    companyNameDraft,
    "legal_name",
    value
  );
  assert.equal(companyNameDraft.legal_name, value);
}
assert.equal(
  checkoutDetails.sanitizeCheckoutDetails(companyNameDraft).legal_name,
  "CONSTRUCCIONES EJEMPLO SL"
);

const individualFromUser = checkoutDetails.buildCheckoutDetailsFromUser({
  firstname: "Ana",
  lastname: "Martín",
  email: "ana@example.com",
  CIF: "12345678Z"
});
assert.equal(individualFromUser.billing_type, "individual");
assert.equal(individualFromUser.legal_name, "Ana Martín");
assert.equal(individualFromUser.tax_id, "12345678Z");

const company = checkoutDetails.sanitizeCheckoutDetails({
  ...validDetails,
  billing_type: "company",
  legal_name: "CONSTRUCCIONES EJEMPLO SL",
  tax_id: "  b12345678  "
});
assert.equal(company.legal_name, "CONSTRUCCIONES EJEMPLO SL");
assert.equal(company.tax_id, "B12345678");

const invalidCompany = checkoutDetails.validateCheckoutDetails({
  ...validDetails,
  billing_type: "company",
  legal_name: ""
});
assert.equal(invalidCompany.isValid, false);
assert.equal(invalidCompany.errors.legal_name, "Introduce la razón social.");

const companyAfterSwitch = checkoutDetails.changeCheckoutBillingType(validDetails, "company");
assert.equal(companyAfterSwitch.billing_type, "company");
assert.equal(companyAfterSwitch.legal_name, "");
assert.equal(companyAfterSwitch.tax_id, "");

const individualAfterSwitch = checkoutDetails.changeCheckoutBillingType(company, "individual");
assert.equal(individualAfterSwitch.billing_type, "individual");
assert.equal(individualAfterSwitch.legal_name, "Juan García López");
assert.equal(individualAfterSwitch.tax_id, "");

const storage = new Map();
globalThis.window = {
  sessionStorage: {
    getItem: (key) => storage.get(key) ?? null,
    removeItem: (key) => storage.delete(key),
    setItem: (key, value) => storage.set(key, value)
  }
};

checkoutDetails.saveCheckoutDetails(company);
const restoredCompany = checkoutDetails.loadStoredCheckoutDetails();
assert.equal(restoredCompany.billing_type, "company");
assert.equal(restoredCompany.legal_name, "CONSTRUCCIONES EJEMPLO SL");
assert.equal(restoredCompany.tax_id, "B12345678");

storage.set(
  checkoutDetails.CHECKOUT_DETAILS_STORAGE_KEY,
  JSON.stringify({
    ...validDetails,
    legal_name: undefined,
    billing_type: undefined,
    tax_id: undefined,
    CIF: "  x1234567l  "
  })
);
const restoredLegacy = checkoutDetails.loadStoredCheckoutDetails();
assert.equal(restoredLegacy.billing_type, "individual");
assert.equal(restoredLegacy.legal_name, "Juan García López");
assert.equal(restoredLegacy.tax_id, "X1234567L");

const companyPayload = checkoutDetails.buildCustomerData(company);
assert.equal(companyPayload.firstname, "Juan");
assert.equal(companyPayload.lastname, "García López");
assert.equal(companyPayload.legal_name, "CONSTRUCCIONES EJEMPLO SL");
assert.equal(companyPayload.tax_id, "B12345678");
for (const internalField of ["billing_type", "CIF", "acceptedPolicy", "useDifferentShipping"]) {
  assert.equal(Object.hasOwn(companyPayload, internalField), false);
}

const individualPayload = checkoutDetails.buildCustomerData({
  ...validDetails,
  tax_id: "12345678Z"
});
assert.equal(individualPayload.legal_name, "Juan García López");
assert.equal(individualPayload.tax_id, "12345678Z");

const individualWithoutTaxId = checkoutDetails.validateCheckoutDetails({
  ...validDetails,
  tax_id: ""
});
assert.equal(individualWithoutTaxId.isValid, false);
assert.equal(individualWithoutTaxId.errors.tax_id, "Introduce el NIF / NIE.");

const companyWithoutTaxId = checkoutDetails.validateCheckoutDetails({
  ...validDetails,
  billing_type: "company",
  legal_name: "CONSTRUCCIONES EJEMPLO SL",
  tax_id: ""
});
assert.equal(companyWithoutTaxId.isValid, false);
assert.equal(companyWithoutTaxId.errors.tax_id, "Introduce el NIF / CIF.");

const oversizedTaxId = checkoutDetails.validateCheckoutDetails({
  ...validDetails,
  tax_id: "X".repeat(21)
});
assert.equal(oversizedTaxId.isValid, false);
assert.equal(
  oversizedTaxId.errors.tax_id,
  "El identificador fiscal no puede superar 20 caracteres."
);

assert.match(detailsStepSource, /<fieldset className="mw-checkout-billing-type">/);
assert.match(detailsStepSource, /¿A nombre de quién se emitirá la factura\?/);
assert.match(detailsStepSource, /Particular \/ autónomo/);
assert.match(detailsStepSource, /value="company"/);
assert.match(detailsStepSource, /label=\{details\.billing_type === "company" \? "Razón social" : "Nombre fiscal"\}/);
assert.match(detailsStepSource, /label=\{details\.billing_type === "company" \? "NIF \/ CIF" : "NIF \/ NIE"\}/);
assert.match(paymentStepSource, /<CheckoutPaymentSummary customerDetails=\{customerDetails\} quote=\{quote\} \/>/);
assert.match(paymentSummarySource, /customerDetails\.legal_name/);
assert.match(paymentSummarySource, /customerDetails\.tax_id/);
assert.match(stripeSource, /customer_data: buildCustomerData\(customerDetails\)/);
assert.match(paypalSource, /customer_data: buildCustomerData\(customerDetails\)/);

delete globalThis.window;

console.log("Checkout billing identity assertions passed");
