"use client";

import type { ChangeEvent, FormEvent } from "react";
import { useEffect, useRef, useState } from "react";

type RequestInfo = {
  mode: "free" | "incentive";
  status: "open" | "received" | "pending_confirmation";
  commercial_consent_active: boolean;
  terms_version: string;
  terms_url: string | null;
  terms_text: string;
  consent_text: string;
  max_images: number;
  max_image_bytes: number;
  max_total_bytes: number;
};

type Preview = { id: string; file: File; url: string };
const LOCAL_API = "http://127.0.0.1:3001";

function apiBase() {
  const configured = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (configured) return configured.replace(/\/$/, "");
  return process.env.NODE_ENV === "production" ? null : LOCAL_API;
}

export function CustomerPhotoForm() {
  const token = useRef("");
  const previews = useRef(new Set<string>());
  const [info, setInfo] = useState<RequestInfo | null>(null);
  const [photos, setPhotos] = useState<Preview[]>([]);
  const [consent, setConsent] = useState<"" | "yes" | "no">("");
  const [message, setMessage] = useState("Comprobando enlace…");
  const [busy, setBusy] = useState(false);
  const api = apiBase();

  useEffect(() => {
    const value = window.location.hash.slice(1);
    window.history.replaceState(window.history.state, "", window.location.pathname);
    token.current = value;
    if (!value || !api) {
      setMessage("Este enlace no está disponible.");
      return;
    }
    void fetch(`${api}/api/customer-photos`, {
      headers: { Authorization: `Bearer ${value}` },
      cache: "no-store",
      referrerPolicy: "no-referrer"
    })
      .then(async (response) => {
        if (!response.ok) throw new Error("Este enlace no está disponible o ha caducado.");
        return response.json() as Promise<RequestInfo>;
      })
      .then((data) => {
        setInfo(data);
        setMessage(data.status === "received" ? "El servidor de correo ha aceptado tus fotografías. Gracias." : data.status === "pending_confirmation" ? "Estamos verificando el envío. No vuelvas a enviarlas; contacta con MetalWolft si necesitas ayuda." : "");
      })
      .catch((error) => setMessage(error instanceof Error ? error.message : "No se pudo abrir el formulario."));
    return () => {
      previews.current.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [api]);

  function addPhotos(event: ChangeEvent<HTMLInputElement>) {
    const selected = Array.from(event.target.files || []);
    event.target.value = "";
    if (!info) return;
    if (selected.length + photos.length > info.max_images) {
      setMessage(`Puedes enviar un máximo de ${info.max_images} fotografías.`);
      return;
    }
    if (selected.some((file) => !["image/jpeg", "image/png", "image/webp"].includes(file.type) || file.size > info.max_image_bytes)) {
      setMessage("Usa JPEG, PNG o WebP de 5 MB o menos por fotografía.");
      return;
    }
    if (selected.reduce((sum, file) => sum + file.size, photos.reduce((sum, photo) => sum + photo.file.size, 0)) > 24 * 1024 * 1024) {
      setMessage("El conjunto de fotografías es demasiado grande. Selecciona imágenes más pequeñas.");
      return;
    }
    const added = selected.map((file) => {
      const url = URL.createObjectURL(file);
      previews.current.add(url);
      return { id: url, file, url };
    });
    setPhotos((current) => [...current, ...added]);
    setMessage("");
  }

  function removePhoto(id: string) {
    URL.revokeObjectURL(id);
    previews.current.delete(id);
    setPhotos((current) => current.filter((photo) => photo.id !== id));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!api || !info || !token.current || !photos.length || !consent) return;
    setBusy(true);
    setMessage("");
    const body = new FormData();
    photos.forEach((photo) => body.append("photos", photo.file));
    body.append("commercial_consent", consent);
    try {
      const response = await fetch(`${api}/api/customer-photos`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token.current}` },
        body,
        cache: "no-store",
        referrerPolicy: "no-referrer"
      });
      const result = (await response.json()) as { message?: string; error?: string };
      if (response.status === 409) {
        setInfo({ ...info, status: "pending_confirmation" });
      }
      if (!response.ok) throw new Error(result.error || "No se pudieron enviar las fotografías.");
      photos.forEach((photo) => URL.revokeObjectURL(photo.url));
      previews.current.clear();
      setPhotos([]);
      setInfo({ ...info, status: "received", commercial_consent_active: consent === "yes" });
      setMessage(result.message || "El servidor de correo ha aceptado tus fotografías. Gracias.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No se pudieron enviar las fotografías.");
    } finally {
      setBusy(false);
    }
  }

  if (!info) return <p role="status">{message}</p>;
  if (info.status !== "open") return (
    <div>
      <p role="status">{message}</p>
      <p>Para retirar tu autorización comercial o solicitar la supresión de las fotografías recibidas por correo, escribe a <a href="mailto:admin@metalwolft.com">admin@metalwolft.com</a>. Son solicitudes distintas y las atenderemos por separado.</p>
    </div>
  );

  return (
    <form className="mw-contact-form mw-issue-report-form" onSubmit={submit}>
      <p>Hasta cinco fotografías: una vista general, otra del diseño y, si quieres, detalles o perspectivas. No hace falta calidad profesional.</p>
      <p>Busca buena luz y evita personas identificables, matrículas o información privada.</p>
      <p>Las imágenes se ajustan automáticamente si es necesario y se envían por correo a MetalWolft. No se guardan en el panel. El conjunto procesado no puede superar {Math.round(info.max_total_bytes / (1024 * 1024))} MB.</p>
      {info.mode === "incentive" && (
        <p>La revisión de las fotos no garantiza el reembolso de 20 €. Consulta las condiciones antes de enviarlas.</p>
      )}
      <label className="mw-field">
        <span>Fotografías (JPEG, PNG o WebP, máximo 5 MB cada una)</span>
        <input type="file" accept="image/jpeg,image/png,image/webp" multiple onChange={addPhotos} disabled={busy || photos.length >= info.max_images} />
      </label>
      {photos.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 16 }}>
          {photos.map((photo, index) => (
            <div key={photo.id}>
              {/* Blob previews stay in memory and never use the public image optimizer. */}
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={photo.url} alt={`Fotografía seleccionada ${index + 1}`} style={{ width: 140, height: 120, objectFit: "contain" }} />
              <button type="button" onClick={() => removePhoto(photo.id)} disabled={busy}>Eliminar</button>
            </div>
          ))}
        </div>
      )}
      <section aria-label="Condiciones de participación">
        <h3>Condiciones de participación</h3>
        <p>{info.terms_text}</p>
        {info.terms_url && <p><a href={info.terms_url} target="_blank" rel="noopener noreferrer">Leer condiciones completas</a></p>}
      </section>
      <fieldset>
        <legend>Autorización de uso comercial, versión {info.terms_version}</legend>
        <p>{info.consent_text}</p>
        <label><input type="radio" name="commercial-consent" value="yes" checked={consent === "yes"} onChange={() => setConsent("yes")} /> Sí, autorizo el uso comercial descrito.</label>
        <label><input type="radio" name="commercial-consent" value="no" checked={consent === "no"} onChange={() => setConsent("no")} /> No autorizo el uso comercial.</label>
      </fieldset>
      <p>Enviar fotos no implica autorizar su publicación. No publicaremos ninguna automáticamente.</p>
      <p>Puedes retirar después tu autorización comercial escribiendo a <a href="mailto:admin@metalwolft.com">admin@metalwolft.com</a>. Retirar la autorización no elimina automáticamente las fotos recibidas por correo; si deseas solicitar su supresión, indícalo expresamente.</p>
      <button className="mw-button mw-button--primary" type="submit" disabled={busy || photos.length === 0 || !consent}>
        {busy ? "Enviando…" : "Enviar fotografías"}
      </button>
      {message && <p role="status">{message}</p>}
    </form>
  );
}
