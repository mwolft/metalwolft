"use client";

import type { ChangeEvent, FormEvent } from "react";
import { useState } from "react";

type ContactFormValues = {
  name: string;
  firstname: string;
  phone: string;
  email: string;
  message: string;
};

const INITIAL_VALUES: ContactFormValues = {
  name: "",
  firstname: "",
  phone: "",
  email: "",
  message: ""
};

const CLIENT_LOCAL_API_URL = "http://127.0.0.1:3001";

function resolveClientApiBaseUrl() {
  const configuredApiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();

  if (configuredApiUrl) {
    return {
      url: configuredApiUrl.replace(/\/$/, ""),
      error: null
    };
  }

  if (process.env.NODE_ENV !== "production") {
    return {
      url: CLIENT_LOCAL_API_URL,
      error: null
    };
  }

  return {
    url: null,
    error:
      "El formulario no está disponible en este entorno ahora mismo. Escríbenos por WhatsApp, teléfono o email."
  };
}

export function ContactForm() {
  const [values, setValues] = useState<ContactFormValues>(INITIAL_VALUES);
  const [status, setStatus] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const apiConfig = resolveClientApiBaseUrl();
  const availabilityMessage = !apiConfig.url ? apiConfig.error : null;

  function handleChange(
    event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) {
    const { name, value } = event.target;
    setValues((current) => ({
      ...current,
      [name]: value
    }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus(null);

    if (!apiConfig.url) {
      setStatus({
        type: "error",
        message:
          apiConfig.error ||
          "El formulario no está disponible en este entorno ahora mismo."
      });
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch(`${apiConfig.url}/api/email/contact`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(values)
      });

      const payload = (await response.json().catch(() => null)) as
        | { message?: string; error?: string }
        | null;

      if (!response.ok) {
        throw new Error(payload?.error || "No se pudo enviar el mensaje.");
      }

      setValues(INITIAL_VALUES);
      setStatus({
        type: "success",
        message: payload?.message || "Mensaje enviado correctamente."
      });
    } catch (error) {
      setStatus({
        type: "error",
        message:
          error instanceof Error
            ? error.message
            : "No se pudo enviar el mensaje. Inténtalo de nuevo."
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="mw-contact-form" onSubmit={handleSubmit}>
      <div className="mw-form-grid">
        <label className="mw-field">
          <span>Nombre</span>
          <input
            autoComplete="given-name"
            name="name"
            onChange={handleChange}
            required
            type="text"
            value={values.name}
          />
        </label>

        <label className="mw-field">
          <span>Apellidos</span>
          <input
            autoComplete="family-name"
            name="firstname"
            onChange={handleChange}
            required
            type="text"
            value={values.firstname}
          />
        </label>

        <label className="mw-field">
          <span>Teléfono</span>
          <input
            autoComplete="tel"
            name="phone"
            onChange={handleChange}
            required
            type="tel"
            value={values.phone}
          />
        </label>

        <label className="mw-field">
          <span>Correo electrónico</span>
          <input
            autoComplete="email"
            name="email"
            onChange={handleChange}
            required
            type="email"
            value={values.email}
          />
        </label>

        <label className="mw-field mw-field--full">
          <span>Mensaje</span>
          <textarea
            name="message"
            onChange={handleChange}
            required
            rows={6}
            value={values.message}
          />
        </label>
      </div>

      <div className="mw-actions">
        <button
          className="mw-button mw-button--primary"
          disabled={isSubmitting || !apiConfig.url}
          type="submit"
        >
          {isSubmitting ? "Enviando..." : "Enviar mensaje"}
        </button>
      </div>

      {availabilityMessage ? (
        <p aria-live="polite" className="mw-alert mw-alert--error">
          {availabilityMessage}
        </p>
      ) : null}

      {status ? (
        <p
          aria-live="polite"
          className={`mw-alert ${
            status.type === "success" ? "mw-alert--success" : "mw-alert--error"
          }`}
        >
          {status.message}
        </p>
      ) : null}
    </form>
  );
}
