"use client";

import type { FormEvent } from "react";
import { useId, useState } from "react";
import Link from "next/link";
import { getApiBaseUrl } from "@/lib/api";
import {
  RESET_PASSWORD_PATH,
  buildResetPasswordPayload,
  getSafePasswordRecoveryMessage,
  validateResetPasswordInput,
  type PasswordRecoveryResponse
} from "@/lib/password-recovery";

type ResetPasswordFormProps = {
  token?: string;
};

export function ResetPasswordForm({ token }: ResetPasswordFormProps) {
  const feedbackId = useId();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(
    token
        ? null
        : {
            type: "error",
            message: "El enlace de recuperación no es válido. Solicita uno nuevo."
          }
  );

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (isSubmitting) {
      return;
    }

    setFeedback(null);

    const validationError = validateResetPasswordInput({
      token,
      password,
      confirmPassword
    });

    if (validationError) {
      setFeedback({
        type: "error",
        message: validationError
      });
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch(`${getApiBaseUrl()}${RESET_PASSWORD_PATH}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(buildResetPasswordPayload(token!, password))
      }).catch(() => {
        throw new Error("API no disponible. Inténtalo de nuevo.");
      });
      const payload = (await response.json().catch(() => null)) as PasswordRecoveryResponse | null;

      if (!response.ok) {
        throw new Error(
          getSafePasswordRecoveryMessage(
            payload,
            response.status === 400
              ? "El enlace no es válido o ha caducado. Solicita uno nuevo."
              : "No se pudo restablecer la contraseña. Inténtalo de nuevo."
          )
        );
      }

      setPassword("");
      setConfirmPassword("");
      setFeedback({
        type: "success",
        message: getSafePasswordRecoveryMessage(
          payload,
          "Contraseña actualizada correctamente."
        )
      });
    } catch (error) {
      setFeedback({
        type: "error",
        message:
          error instanceof Error
            ? error.message
            : "No se pudo restablecer la contraseña. Inténtalo de nuevo."
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form
      aria-describedby={feedback ? feedbackId : undefined}
      className="mw-login-form"
      onSubmit={handleSubmit}
    >
      <label className="mw-field">
        <span>Nueva contraseña</span>
        <input
          autoComplete="new-password"
          disabled={isSubmitting || !token}
          name="password"
          onChange={(event) => setPassword(event.target.value)}
          required
          type="password"
          value={password}
        />
      </label>

      <label className="mw-field">
        <span>Confirmar contraseña</span>
        <input
          autoComplete="new-password"
          disabled={isSubmitting || !token}
          name="confirm-password"
          onChange={(event) => setConfirmPassword(event.target.value)}
          required
          type="password"
          value={confirmPassword}
        />
      </label>

      <button
        className="mw-button mw-button--primary"
        disabled={isSubmitting || !token}
        type="submit"
      >
        {isSubmitting ? "Restableciendo..." : "Restablecer contraseña"}
      </button>

      {feedback ? (
        <p
          aria-live="polite"
          className={`mw-alert ${
            feedback.type === "success" ? "mw-alert--success" : "mw-alert--error"
          }`}
          id={feedbackId}
        >
          {feedback.message}
        </p>
      ) : null}

      <p className="mw-auth-footnote">
        <Link href="/login">Volver a iniciar sesión</Link>
        {" | "}
        <Link href="/forgot-password">Solicitar otro enlace</Link>.
      </p>
    </form>
  );
}
