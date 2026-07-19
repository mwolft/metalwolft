"use client";

import type { FormEvent } from "react";
import { useId, useState } from "react";
import Link from "next/link";
import { getApiBaseUrl } from "@/lib/api";
import {
  FORGOT_PASSWORD_PATH,
  buildForgotPasswordPayload,
  getSafePasswordRecoveryMessage,
  validateRecoveryEmail,
  type PasswordRecoveryResponse
} from "@/lib/password-recovery";

const DEFAULT_SUCCESS_MESSAGE =
  "Si el correo está registrado, recibirás un enlace para restablecer tu contraseña.";

export function ForgotPasswordForm() {
  const feedbackId = useId();
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (isSubmitting) {
      return;
    }

    setFeedback(null);

    if (!validateRecoveryEmail(email)) {
      setFeedback({
        type: "error",
        message: "Introduce un correo electrónico válido."
      });
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch(`${getApiBaseUrl()}${FORGOT_PASSWORD_PATH}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(buildForgotPasswordPayload(email))
      }).catch(() => {
        throw new Error("API no disponible. Inténtalo de nuevo.");
      });
      const payload = (await response.json().catch(() => null)) as PasswordRecoveryResponse | null;

      if (!response.ok) {
        throw new Error(
          getSafePasswordRecoveryMessage(
            payload,
            "No se pudo solicitar la recuperación. Inténtalo de nuevo."
          )
        );
      }

      setFeedback({
        type: "success",
        message: getSafePasswordRecoveryMessage(payload, DEFAULT_SUCCESS_MESSAGE)
      });
    } catch (error) {
      setFeedback({
        type: "error",
        message:
          error instanceof Error
            ? error.message
            : "No se pudo solicitar la recuperación. Inténtalo de nuevo."
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
        <span>Correo electrónico</span>
        <input
          autoComplete="email"
          disabled={isSubmitting}
          name="email"
          onChange={(event) => setEmail(event.target.value)}
          required
          type="email"
          value={email}
        />
      </label>

      <button className="mw-button mw-button--primary" disabled={isSubmitting} type="submit">
        {isSubmitting ? "Enviando..." : "Enviar enlace de recuperación"}
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
        <Link href="/login">Volver a iniciar sesión</Link>.
      </p>
    </form>
  );
}
