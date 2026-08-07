"use client";

import type { FormEvent } from "react";
import { useId, useState } from "react";
import { useRouter } from "next/navigation";
import { getApiBaseUrl } from "@/lib/api";
import { getSafeInternalPath, saveSession, type AuthUser } from "@/lib/auth-client";

type RegisterFormProps = {
  nextPath?: string;
};

type SignupResponse = {
  access_token?: string;
  message?: string;
  results?: AuthUser;
};

export function RegisterForm({ nextPath }: RegisterFormProps) {
  const router = useRouter();
  const feedbackId = useId();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
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

    if (password !== confirmPassword) {
      setFeedback({
        type: "error",
        message: "Las contraseñas no coinciden."
      });
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch(`${getApiBaseUrl()}/api/signup`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ email, password })
      }).catch(() => {
        throw new Error("API no disponible. Inténtalo de nuevo.");
      });
      const payload = (await response.json().catch(() => null)) as SignupResponse | null;

      if (!response.ok) {
        throw new Error(payload?.message || "No se pudo crear la cuenta. Inténtalo de nuevo.");
      }

      if (!payload?.access_token || !payload.results) {
        throw new Error("Respuesta de registro inválida. Inténtalo de nuevo.");
      }

      saveSession(payload.access_token, payload.results);
      const destination = getSafeInternalPath(nextPath);

      setFeedback({
        type: "success",
        message: "Cuenta creada correctamente. Redirigiendo..."
      });
      router.replace(destination);
    } catch (error) {
      setFeedback({
        type: "error",
        message:
          error instanceof Error
            ? error.message
            : "No se pudo crear la cuenta. Inténtalo de nuevo."
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

      <label className="mw-field">
        <span>Contraseña</span>
        <input
          autoComplete="new-password"
          disabled={isSubmitting}
          name="password"
          onChange={(event) => setPassword(event.target.value)}
          required
          type="password"
          value={password}
        />
      </label>

      <label className="mw-field">
        <span>Repite la contraseña</span>
        <input
          autoComplete="new-password"
          disabled={isSubmitting}
          name="confirm-password"
          onChange={(event) => setConfirmPassword(event.target.value)}
          required
          type="password"
          value={confirmPassword}
        />
      </label>

      <button className="mw-button mw-button--primary" disabled={isSubmitting} type="submit">
        {isSubmitting ? "Creando cuenta..." : "Crear cuenta"}
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
    </form>
  );
}
