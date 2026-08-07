import assert from "node:assert/strict";
import {
  FORGOT_PASSWORD_PATH,
  RESET_PASSWORD_PATH,
  buildForgotPasswordPayload,
  buildResetPasswordPayload,
  getSafePasswordRecoveryMessage,
  normalizeRecoveryEmail,
  validateRecoveryEmail,
  validateResetPasswordInput
} from "./password-recovery";

type TestCase = {
  name: string;
  assertion: () => void;
};

const tests: TestCase[] = [];

function test(name: string, assertion: () => void) {
  tests.push({ name, assertion });
}

test("uses the real Flask password recovery endpoints", () => {
  assert.equal(FORGOT_PASSWORD_PATH, "/api/auth/forgot-password");
  assert.equal(RESET_PASSWORD_PATH, "/api/auth/reset-password");
});

test("normalizes recovery email before sending", () => {
  assert.equal(normalizeRecoveryEmail(" CLIENTE@EXAMPLE.COM "), "cliente@example.com");
  assert.deepEqual(buildForgotPasswordPayload(" CLIENTE@EXAMPLE.COM "), {
    email: "cliente@example.com"
  });
});

test("rejects invalid recovery email locally", () => {
  assert.equal(validateRecoveryEmail(""), false);
  assert.equal(validateRecoveryEmail("cliente"), false);
  assert.equal(validateRecoveryEmail("cliente@example.com"), true);
});

test("builds reset password payload exactly as Flask expects", () => {
  assert.deepEqual(buildResetPasswordPayload("token-123", "nueva-password"), {
    token: "token-123",
    password: "nueva-password"
  });
});

test("rejects reset without token", () => {
  assert.match(
    validateResetPasswordInput({
      token: "",
      password: "nueva-password",
      confirmPassword: "nueva-password"
    }),
    /enlace/
  );
});

test("rejects reset with different passwords", () => {
  assert.match(
    validateResetPasswordInput({
      token: "token-123",
      password: "nueva-password",
      confirmPassword: "otra-password"
    }),
    /no coinciden/
  );
});

test("accepts reset with token and matching password", () => {
  assert.equal(
    validateResetPasswordInput({
      token: "token-123",
      password: "nueva-password",
      confirmPassword: "nueva-password"
    }),
    ""
  );
});

test("does not show internal server error to customers", () => {
  assert.equal(
    getSafePasswordRecoveryMessage({ error: "Internal server error" }, "Mensaje seguro"),
    "Mensaje seguro"
  );
});

for (const { name, assertion } of tests) {
  assertion();
  console.log(`ok - ${name}`);
}

console.log(`${tests.length} password recovery tests passed`);
