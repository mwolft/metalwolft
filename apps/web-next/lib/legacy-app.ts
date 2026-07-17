const legacyBaseUrl = process.env.NEXT_PUBLIC_LEGACY_APP_URL?.trim().replace(/\/+$/, "");

export const legacyCartUrl = legacyBaseUrl ? `${legacyBaseUrl}/cart` : "/cart";
export const legacyAdminUrl = legacyBaseUrl ? `${legacyBaseUrl}/admin/users` : "/admin/users";
