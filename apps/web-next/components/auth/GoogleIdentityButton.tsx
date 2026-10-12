"use client";

import { useEffect, useRef, useState } from "react";
import Script from "next/script";
import { useRouter } from "next/navigation";
import { getApiBaseUrl } from "@/lib/api";
import { getSafeInternalPath, getToken, saveSession, type AuthUser } from "@/lib/auth-client";

type GoogleClient = {
  accounts: { id: {
    initialize: (options: { client_id: string; callback: (response: { credential?: string }) => void }) => void;
    renderButton: (element: HTMLElement, options: { theme: string; size: string; text: string; width: number }) => void;
  } };
};

type GoogleIdentityButtonProps = {
  mode: "login" | "link";
  nextPath?: string;
};

const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID?.trim();

export function GoogleIdentityButton({ mode, nextPath }: GoogleIdentityButtonProps) {
  const router = useRouter();
  const container = useRef<HTMLDivElement>(null);
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const busyRef = useRef(false);
  const [feedback, setFeedback] = useState("");
  const [password, setPassword] = useState("");
  const passwordRef = useRef(password);
  passwordRef.current = password;
  const [linked, setLinked] = useState<boolean | null>(null);

  useEffect(() => {
    if (mode !== "link") return;
    const token = getToken();
    if (!token) return;
    let active = true;
    void fetch(`${getApiBaseUrl()}/api/auth/google/link`, {
      headers: { Authorization: `Bearer ${token}` }
    }).then(async (response) => {
      if (!response.ok) throw new Error("No se pudo comprobar la vinculación.");
      const status = (await response.json()) as { linked: boolean };
      if (active) setLinked(status.linked);
    }).catch(() => {
      if (active) setFeedback("No se pudo comprobar el acceso Google. Inténtalo más tarde.");
    });
    return () => { active = false; };
  }, [mode]);

  useEffect(() => {
    if (!ready || !clientId || !container.current || (mode === "link" && linked !== false)) return;
    const google = (window as Window & { google?: GoogleClient }).google;
    if (!google) return;

    google.accounts.id.initialize({
      client_id: clientId,
      callback: ({ credential }) => {
        if (busyRef.current) return;
        if (!credential) {
          setFeedback("No se pudo completar el acceso con Google.");
          return;
        }
        setFeedback("");
        const token = mode === "link" ? getToken() : null;
        if (mode === "link" && !token) {
          setFeedback("Tu sesión ha caducado. Inicia sesión de nuevo.");
          return;
        }
        if (mode === "link" && !passwordRef.current) {
          setFeedback("Confirma tu contraseña antes de vincular Google.");
          return;
        }
        busyRef.current = true;
        setBusy(true);
        void fetch(`${getApiBaseUrl()}/api/auth/google${mode === "link" ? "/link" : ""}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {})
          },
          body: JSON.stringify({ credential, ...(mode === "link" ? { password: passwordRef.current } : {}) })
        })
          .then(async (response) => {
            const payload = (await response.json().catch(() => null)) as {
              message?: string;
              access_token?: string;
              results?: AuthUser;
            } | null;
            if (!response.ok) throw new Error(payload?.message || "No se pudo acceder con Google.");
            if (mode === "link") {
              setFeedback("");
              setPassword("");
              setLinked(true);
              return;
            }
            if (!payload?.access_token || !payload.results) throw new Error("Respuesta de acceso inválida.");
            saveSession(payload.access_token, payload.results);
            router.replace(getSafeInternalPath(nextPath));
          })
          .catch((error: unknown) => {
            setFeedback(error instanceof Error ? error.message : "No se pudo acceder con Google.");
          })
          .finally(() => {
            busyRef.current = false;
            setBusy(false);
          });
      }
    });

    container.current.replaceChildren();
    google.accounts.id.renderButton(container.current, {
      theme: "outline", size: "large", text: "continue_with",
      width: Math.min(container.current.clientWidth || 400, 400)
    });
  }, [linked, mode, nextPath, ready, router]);

  if (!clientId) return null;

  return (
    <div className="mw-google-auth" aria-busy={busy}>
      <Script
        src="https://accounts.google.com/gsi/client"
        strategy="afterInteractive"
        onReady={() => setReady(true)}
        onError={() => setFeedback("No se pudo cargar el acceso con Google. Inténtalo más tarde.")}
      />
      {mode === "link" && linked === true ? <p className="mw-account-google-link__status">Google ya está vinculado a tu cuenta.</p> : null}
      {mode === "link" && linked === false ? (
        <p className="mw-account-google-link__intro">¿Quieres acceder también con Google? Vincúlalo a esta cuenta sin perder tus pedidos.</p>
      ) : null}
      {mode === "link" && linked === false ? (
        <label className="mw-field">
          <span>Confirma tu contraseña para vincular Google</span>
          <input autoComplete="current-password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
        </label>
      ) : null}
      {mode === "login" || linked === false ? <div className="mw-google-auth__button" ref={container} /> : null}
      {feedback ? <p className="mw-auth-footnote" role="status">{feedback}</p> : null}
    </div>
  );
}
