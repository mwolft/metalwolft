import type { AuthUser } from "@/lib/auth-client";

export type CustomerProfileDraft = {
  firstname: string;
  lastname: string;
  email: string;
  phone: string;
  billing_address: string;
  billing_city: string;
  billing_postal_code: string;
  shipping_address: string;
  shipping_city: string;
  shipping_postal_code: string;
};

export type CustomerProfileEditableField = Exclude<keyof CustomerProfileDraft, "email">;
export type CustomerProfileErrors = Partial<Record<CustomerProfileEditableField, string>>;
export type CustomerProfileUpdate = Record<CustomerProfileEditableField, string>;

const PROFILE_FIELD_LIMITS: Record<CustomerProfileEditableField, number> = {
  firstname: 100,
  lastname: 100,
  phone: 50,
  billing_address: 200,
  billing_city: 100,
  billing_postal_code: 20,
  shipping_address: 200,
  shipping_city: 100,
  shipping_postal_code: 20
};

function valueOrEmpty(value: string | null | undefined) {
  return typeof value === "string" ? value : "";
}

export function buildCustomerProfileDraft(user: AuthUser): CustomerProfileDraft {
  return {
    firstname: valueOrEmpty(user.firstname),
    lastname: valueOrEmpty(user.lastname),
    email: user.email,
    phone: valueOrEmpty(user.phone),
    billing_address: valueOrEmpty(user.billing_address),
    billing_city: valueOrEmpty(user.billing_city),
    billing_postal_code: valueOrEmpty(user.billing_postal_code),
    shipping_address: valueOrEmpty(user.shipping_address),
    shipping_city: valueOrEmpty(user.shipping_city),
    shipping_postal_code: valueOrEmpty(user.shipping_postal_code)
  };
}

export function updateCustomerProfileDraftField(
  draft: CustomerProfileDraft,
  field: CustomerProfileEditableField,
  value: string
) {
  return {
    ...draft,
    [field]: value
  };
}

export function validateCustomerProfileDraft(draft: CustomerProfileDraft) {
  const errors: CustomerProfileErrors = {};

  for (const [field, maxLength] of Object.entries(PROFILE_FIELD_LIMITS) as Array<
    [CustomerProfileEditableField, number]
  >) {
    if (draft[field].trim().length > maxLength) {
      errors[field] = `No puede superar ${maxLength} caracteres.`;
    }
  }

  return {
    errors,
    isValid: Object.keys(errors).length === 0
  };
}

export function buildCustomerProfileUpdate(
  draft: CustomerProfileDraft
): CustomerProfileUpdate {
  return {
    firstname: draft.firstname.trim(),
    lastname: draft.lastname.trim(),
    phone: draft.phone.trim(),
    billing_address: draft.billing_address.trim(),
    billing_city: draft.billing_city.trim(),
    billing_postal_code: draft.billing_postal_code.trim(),
    shipping_address: draft.shipping_address.trim(),
    shipping_city: draft.shipping_city.trim(),
    shipping_postal_code: draft.shipping_postal_code.trim()
  };
}
