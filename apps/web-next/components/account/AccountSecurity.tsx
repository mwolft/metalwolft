"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRef, useState, type FormEvent } from "react";
import { clearSession, getToken } from "@/lib/auth-client";
import { getApiBaseUrl } from "@/lib/api";
import { CHANGE_PASSWORD_PATH, passwordChangeError, validatePasswordChange } from "@/lib/change-password";

export function AccountSecurity({ hasPassword }: { hasPassword?: boolean }) {
  const router = useRouter();
  const submitting = useRef(false);
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submitting.current) return;
    setError("");
    const validation = validatePasswordChange(current, next, confirmation);
    if (validation) {
      setError(validation);
      return;
    }
    const token = getToken();
    if (!token) {
      clearSession();
      router.replace("/login?next=%2Fmi-cuenta");
      return;
    }
    submitting.current = true;
    setBusy(true);
    try {
      const response = await fetch(`${getApiBaseUrl()}${CHANGE_PASSWORD_PATH}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ current_password: current, new_password: next })
      });
      if (!response.ok) {
        if (response.status === 401 || response.status === 409) {
          clearSession();
        }
        throw new Error(passwordChangeError(response.status));
      }
      clearSession();
      window.location.replace("/login?password_changed=1&next=%2Fmi-cuenta");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "No se pudo cambiar la contraseña.");
    } finally {
      setCurrent("");
      setNext("");
      setConfirmation("");
      submitting.current = false;
      setBusy(false);
    }
  }

  return (
    <section className="mw-account-card mw-account-security" aria-labelledby="account-security-title">
      <h2 id="account-security-title">Seguridad de la cuenta</h2>
      {hasPassword === false ? (
        <p>
          Esta cuenta no tiene contraseña local. Si quieres establecer una, puedes hacerlo mediante la{" "}
          <Link href="/forgot-password">recuperación por correo</Link>.
        </p>
      ) : hasPassword === undefined ? (
        <p>Comprobando las opciones de seguridad de tu cuenta...</p>
      ) : (
        <form className="mw-account-security__form" onSubmit={handleSubmit}>
          <p>Cambia tu contraseña introduciendo primero la actual. Después tendrás que iniciar sesión de nuevo.</p>
          <label className="mw-field">
            <span>Contraseña actual</span>
            <input autoComplete="current-password" disabled={busy} onChange={(event) => setCurrent(event.target.value)} required type="password" value={current} />
          </label>
          <label className="mw-field">
            <span>Contraseña nueva</span>
            <input autoComplete="new-password" disabled={busy} onChange={(event) => setNext(event.target.value)} required type="password" value={next} />
          </label>
          <label className="mw-field">
            <span>Confirmar contraseña nueva</span>
            <input autoComplete="new-password" disabled={busy} onChange={(event) => setConfirmation(event.target.value)} required type="password" value={confirmation} />
          </label>
          {error ? <p className="mw-alert mw-alert--error" role="alert">{error}</p> : null}
          <button className="mw-button mw-button--primary" disabled={busy} type="submit">
            {busy ? "Cambiando..." : "Cambiar contraseña"}
          </button>
        </form>
      )}
    </section>
  );
}
