import type { AuthUser } from "@/lib/auth-client";

export const CHECKOUT_DETAILS_STORAGE_KEY = "mw_checkout_customer_details";

export type CheckoutBillingType = "individual" | "company";

export type CheckoutCustomerDetails = {
  firstname: string;
  lastname: string;
  email: string;
  phone: string;
  billing_type: CheckoutBillingType;
  legal_name: string;
  tax_id: string;
  billing_address: string;
  billing_city: string;
  billing_postal_code: string;
  useDifferentShipping: boolean;
  shipping_address: string;
  shipping_city: string;
  shipping_postal_code: string;
  acceptedPolicy: boolean;
};

export type CheckoutDetailsErrors = Partial<Record<keyof CheckoutCustomerDetails, string>>;

export type CheckoutDraftField = Exclude<keyof CheckoutCustomerDetails, "billing_type">;

export const EMPTY_CHECKOUT_CUSTOMER_DETAILS: CheckoutCustomerDetails = {
  firstname: "",
  lastname: "",
  email: "",
  phone: "",
  billing_type: "individual",
  legal_name: "",
  tax_id: "",
  billing_address: "",
  billing_city: "",
  billing_postal_code: "",
  useDifferentShipping: false,
  shipping_address: "",
  shipping_city: "",
  shipping_postal_code: "",
  acceptedPolicy: false
};

const VALID_SPANISH_POSTAL_CODE_REGEX = /^\d{5}$/;
const RESTRICTED_SHIPPING_POSTAL_PREFIXES = ["07", "35", "38", "51", "52"];
const TAX_ID_MAX_LENGTH = 20;
const INVALID_POSTAL_CODE_MESSAGE = "Introduce un código postal válido.";
const PENINSULA_ONLY_SHIPPING_MESSAGE =
  "Actualmente solo realizamos envíos a la península. Para Baleares, Canarias, Ceuta o Melilla, consúltanos antes de comprar.";

function normalizeText(value: unknown) {
  return typeof value === "string" ? value.trim() : "";
}

function normalizeTaxId(value: unknown) {
  return normalizeText(value).toUpperCase();
}

export function buildIndividualLegalName(firstname: unknown, lastname: unknown) {
  return [normalizeText(firstname), normalizeText(lastname)].filter(Boolean).join(" ");
}

function normalizeBillingType(value: unknown): CheckoutBillingType {
  return value === "company" ? "company" : "individual";
}

function normalizeSameAsBillingValue(value: unknown) {
  const normalizedValue = normalizeText(value);
  const normalizedLowerValue = normalizedValue.toLowerCase();

  if (
    normalizedLowerValue === "la misma que la de facturación" ||
    normalizedLowerValue === "la misma que la de facturacion" ||
    normalizedLowerValue === "misma dirección" ||
    normalizedLowerValue === "misma direccion" ||
    normalizedLowerValue === "igual que facturación" ||
    normalizedLowerValue === "igual que facturacion"
  ) {
    return "";
  }

  return normalizedValue;
}

function isValidEmail(value: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

function postalCodeError(value: string, checkShippingRestriction: boolean) {
  if (!value) {
    return "Campo obligatorio.";
  }

  if (!VALID_SPANISH_POSTAL_CODE_REGEX.test(value)) {
    return INVALID_POSTAL_CODE_MESSAGE;
  }

  if (checkShippingRestriction && RESTRICTED_SHIPPING_POSTAL_PREFIXES.includes(value.slice(0, 2))) {
    return PENINSULA_ONLY_SHIPPING_MESSAGE;
  }

  return "";
}

export function sanitizeCheckoutDetails(
  input: (Partial<CheckoutCustomerDetails> & { CIF?: unknown }) = {}
): CheckoutCustomerDetails {
  const useDifferentShipping = Boolean(input.useDifferentShipping);
  const billingType = normalizeBillingType(input.billing_type);
  const contactLegalName = buildIndividualLegalName(input.firstname, input.lastname);
  const suppliedLegalName = normalizeText(input.legal_name);

  return {
    firstname: normalizeText(input.firstname),
    lastname: normalizeText(input.lastname),
    email: normalizeText(input.email),
    phone: normalizeText(input.phone),
    billing_type: billingType,
    legal_name:
      suppliedLegalName || (billingType === "individual" ? contactLegalName : ""),
    tax_id: normalizeTaxId(input.tax_id) || normalizeTaxId(input.CIF),
    billing_address: normalizeText(input.billing_address),
    billing_city: normalizeText(input.billing_city),
    billing_postal_code: normalizeText(input.billing_postal_code),
    useDifferentShipping,
    shipping_address: useDifferentShipping ? normalizeText(input.shipping_address) : "",
    shipping_city: useDifferentShipping ? normalizeText(input.shipping_city) : "",
    shipping_postal_code: useDifferentShipping ? normalizeText(input.shipping_postal_code) : "",
    acceptedPolicy: Boolean(input.acceptedPolicy)
  };
}

export function buildCheckoutDetailsFromUser(user: AuthUser | null): CheckoutCustomerDetails {
  if (!user) {
    return EMPTY_CHECKOUT_CUSTOMER_DETAILS;
  }

  const details = sanitizeCheckoutDetails({
    firstname: user.firstname || "",
    lastname: user.lastname || "",
    email: user.email || "",
    phone: "",
    billing_type: "individual",
    legal_name: buildIndividualLegalName(user.firstname, user.lastname),
    tax_id: user.CIF || "",
    billing_address: user.billing_address || "",
    billing_city: user.billing_city || "",
    billing_postal_code: user.billing_postal_code || "",
    shipping_address: normalizeSameAsBillingValue(user.shipping_address),
    shipping_city: normalizeSameAsBillingValue(user.shipping_city),
    shipping_postal_code: normalizeSameAsBillingValue(user.shipping_postal_code)
  });

  const hasDifferentShipping = Boolean(
    details.shipping_address &&
      (details.shipping_address !== details.billing_address ||
        details.shipping_city !== details.billing_city ||
        details.shipping_postal_code !== details.billing_postal_code)
  );

  return sanitizeCheckoutDetails({
    ...details,
    useDifferentShipping: hasDifferentShipping
  });
}

export function loadStoredCheckoutDetails() {
  if (typeof window === "undefined") {
    return null;
  }

  const rawValue = window.sessionStorage.getItem(CHECKOUT_DETAILS_STORAGE_KEY);
  if (!rawValue) {
    return null;
  }

  try {
    const parsed = JSON.parse(rawValue) as Partial<CheckoutCustomerDetails> & {
      CIF?: unknown;
    };
    return sanitizeCheckoutDetails(parsed);
  } catch {
    window.sessionStorage.removeItem(CHECKOUT_DETAILS_STORAGE_KEY);
    return null;
  }
}

export function saveCheckoutDetails(details: CheckoutCustomerDetails) {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.setItem(
    CHECKOUT_DETAILS_STORAGE_KEY,
    JSON.stringify(sanitizeCheckoutDetails(details))
  );
}

export function updateCheckoutDraftField(
  details: CheckoutCustomerDetails,
  field: CheckoutDraftField,
  value: string | boolean
): CheckoutCustomerDetails {
  const previousContactLegalName = buildIndividualLegalName(
    details.firstname,
    details.lastname
  );
  const nextDetails = {
    ...details,
    [field]: value
  } as CheckoutCustomerDetails;

  if (
    details.billing_type === "individual" &&
    (field === "firstname" || field === "lastname") &&
    (!details.legal_name || details.legal_name === previousContactLegalName)
  ) {
    nextDetails.legal_name = buildIndividualLegalName(
      nextDetails.firstname,
      nextDetails.lastname
    );
  }

  if (field === "useDifferentShipping" && value === false) {
    nextDetails.shipping_address = "";
    nextDetails.shipping_city = "";
    nextDetails.shipping_postal_code = "";
  }

  return nextDetails;
}

export function validateCheckoutDetails(details: CheckoutCustomerDetails) {
  const sanitizedDetails = sanitizeCheckoutDetails(details);
  const errors: CheckoutDetailsErrors = {};

  if (!sanitizedDetails.firstname) errors.firstname = "Campo obligatorio.";
  if (!sanitizedDetails.lastname) errors.lastname = "Campo obligatorio.";
  if (!sanitizedDetails.phone) errors.phone = "Campo obligatorio.";
  if (!sanitizedDetails.email) {
    errors.email = "Campo obligatorio.";
  } else if (!isValidEmail(sanitizedDetails.email)) {
    errors.email = "Introduce un correo electrónico válido.";
  }
  if (!sanitizedDetails.legal_name) {
    errors.legal_name =
      sanitizedDetails.billing_type === "company"
        ? "Introduce la razón social."
        : "Campo obligatorio.";
  }
  if (!sanitizedDetails.tax_id) {
    errors.tax_id =
      sanitizedDetails.billing_type === "company"
        ? "Introduce el NIF / CIF."
        : "Introduce el NIF / NIE.";
  } else if (sanitizedDetails.tax_id.length > TAX_ID_MAX_LENGTH) {
    errors.tax_id = `El identificador fiscal no puede superar ${TAX_ID_MAX_LENGTH} caracteres.`;
  }
  if (!sanitizedDetails.billing_address) errors.billing_address = "Campo obligatorio.";
  if (!sanitizedDetails.billing_city) errors.billing_city = "Campo obligatorio.";

  const billingPostalError = postalCodeError(
    sanitizedDetails.billing_postal_code,
    !sanitizedDetails.useDifferentShipping
  );
  if (billingPostalError) errors.billing_postal_code = billingPostalError;

  if (sanitizedDetails.useDifferentShipping) {
    if (!sanitizedDetails.shipping_address) errors.shipping_address = "Campo obligatorio.";
    if (!sanitizedDetails.shipping_city) errors.shipping_city = "Campo obligatorio.";

    const shippingPostalError = postalCodeError(sanitizedDetails.shipping_postal_code, true);
    if (shippingPostalError) errors.shipping_postal_code = shippingPostalError;
  }

  if (!sanitizedDetails.acceptedPolicy) {
    errors.acceptedPolicy = "Debes aceptar la política de devoluciones y garantías.";
  }

  return {
    details: sanitizedDetails,
    errors,
    isValid: Object.keys(errors).length === 0
  };
}

export function buildCustomerData(details: CheckoutCustomerDetails) {
  const sanitizedDetails = sanitizeCheckoutDetails(details);

  return {
    firstname: sanitizedDetails.firstname,
    lastname: sanitizedDetails.lastname,
    email: sanitizedDetails.email,
    phone: sanitizedDetails.phone,
    legal_name: sanitizedDetails.legal_name,
    tax_id: sanitizedDetails.tax_id,
    billing_address: sanitizedDetails.billing_address,
    billing_city: sanitizedDetails.billing_city,
    billing_postal_code: sanitizedDetails.billing_postal_code,
    shipping_address: sanitizedDetails.useDifferentShipping
      ? sanitizedDetails.shipping_address
      : "",
    shipping_city: sanitizedDetails.useDifferentShipping ? sanitizedDetails.shipping_city : "",
    shipping_postal_code: sanitizedDetails.useDifferentShipping
      ? sanitizedDetails.shipping_postal_code
      : ""
  };
}

export function changeCheckoutBillingType(
  details: CheckoutCustomerDetails,
  billingType: CheckoutBillingType
) {
  if (billingType === "company") {
    return {
      ...details,
      billing_type: billingType,
      legal_name: "",
      tax_id: ""
    };
  }

  return {
    ...details,
    billing_type: billingType,
    legal_name: buildIndividualLegalName(
      details.firstname,
      details.lastname
    ),
    tax_id: ""
  };
}
