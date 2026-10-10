"use client";

import type { ChangeEvent, FormEvent } from "react";
import { useEffect, useRef, useState } from "react";

type RequestInfo = {
  mode: "free" | "incentive";
  is_simulation: boolean;
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
  const [frontPhoto, setFrontPhoto] = useState<Preview | null>(null);
  const [perspectivePhoto, setPerspectivePhoto] = useState<Preview | null>(null);
  const [additionalPhotos, setAdditionalPhotos] = useState<Preview[]>([]);
  const [consent, setConsent] = useState<"" | "yes" | "no">("");
  const [message, setMessage] = useState("Comprobando enlace…");
  const [busy, setBusy] = useState(false);
  const [oppositionRecorded, setOppositionRecorded] = useState(false);
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

  function selectPhotos(event: ChangeEvent<HTMLInputElement>, kind: "front" | "perspective" | "additional") {
    const selected = Array.from(event.target.files || []);
    event.target.value = "";
    if (!info || !selected.length) return;
    if (kind !== "additional" && selected.length !== 1) {
      setMessage("Selecciona una sola fotografía para esta perspectiva.");
      return;
    }
    const current = [frontPhoto, perspectivePhoto, ...additionalPhotos].filter((photo): photo is Preview => photo !== null);
    const replaced = kind === "front" ? frontPhoto : kind === "perspective" ? perspectivePhoto : null;
    if (kind === "additional" && selected.length + additionalPhotos.length > Math.min(3, info.max_images - 2)) {
      setMessage("Puedes añadir un máximo de tres fotografías adicionales.");
      return;
    }
    if (current.length - (replaced ? 1 : 0) + selected.length > info.max_images) {
      setMessage(`Puedes enviar un máximo de ${info.max_images} fotografías.`);
      return;
    }
    if (selected.some((file) => !["image/jpeg", "image/png", "image/webp"].includes(file.type) || file.size > info.max_image_bytes)) {
      setMessage("Usa JPEG, PNG o WebP de 5 MB o menos por fotografía.");
      return;
    }
    if (selected.reduce((sum, file) => sum + file.size, current.reduce((sum, photo) => sum + (photo === replaced ? 0 : photo.file.size), 0)) > 24 * 1024 * 1024) {
      setMessage("El conjunto de fotografías es demasiado grande. Selecciona imágenes más pequeñas.");
      return;
    }
    const added = selected.map((file) => {
      const url = URL.createObjectURL(file);
      previews.current.add(url);
      return { id: url, file, url };
    });
    if (replaced) {
      URL.revokeObjectURL(replaced.url);
      previews.current.delete(replaced.url);
    }
    if (kind === "front") setFrontPhoto(added[0]);
    else if (kind === "perspective") setPerspectivePhoto(added[0]);
    else setAdditionalPhotos((currentPhotos) => [...currentPhotos, ...added]);
    setMessage("");
  }

  function removePhoto(id: string) {
    URL.revokeObjectURL(id);
    previews.current.delete(id);
    if (frontPhoto?.id === id) setFrontPhoto(null);
    else if (perspectivePhoto?.id === id) setPerspectivePhoto(null);
    else setAdditionalPhotos((current) => current.filter((photo) => photo.id !== id));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!api || !info || !token.current || !frontPhoto || !perspectivePhoto || !consent || (info.mode === "incentive" && consent !== "yes")) return;
    setBusy(true);
    setMessage("");
    const body = new FormData();
    body.append("front_photo", frontPhoto.file);
    body.append("perspective_photo", perspectivePhoto.file);
    additionalPhotos.forEach((photo) => body.append("additional_photos", photo.file));
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
      [frontPhoto, perspectivePhoto, ...additionalPhotos].forEach((photo) => URL.revokeObjectURL(photo.url));
      previews.current.clear();
      setFrontPhoto(null);
      setPerspectivePhoto(null);
      setAdditionalPhotos([]);
      setInfo({ ...info, status: "received", commercial_consent_active: consent === "yes" });
      setMessage(result.message || "El servidor de correo ha aceptado tus fotografías. Gracias.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No se pudieron enviar las fotografías.");
    } finally {
      setBusy(false);
    }
  }

  async function optOut() {
    if (!api || !token.current || busy) return;
    setBusy(true);
    try {
      const response = await fetch(`${api}/api/customer-photos/opt-out`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token.current}` },
        cache: "no-store",
        referrerPolicy: "no-referrer"
      });
      const result = (await response.json()) as { message?: string; error?: string };
      if (!response.ok) throw new Error(result.error || "No se pudo registrar la baja.");
      setOppositionRecorded(true);
      setMessage(result.message || "No recibirás nuevas invitaciones para compartir fotografías.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No se pudo registrar la baja.");
    } finally {
      setBusy(false);
    }
  }

  const oppositionControl = oppositionRecorded
    ? <p role="status">No recibirás nuevas invitaciones para compartir fotografías.</p>
    : <p>Si no deseas recibir futuras invitaciones, puedes <button type="button" onClick={optOut} disabled={busy}>registrar tu oposición aquí</button> o escribir a <a href="mailto:admin@metalwolft.com">admin@metalwolft.com</a>. Esto no afecta a los avisos operativos de tus pedidos.</p>;

  if (!info) return <p role="status">{message}</p>;
  if (info.status !== "open") return (
    <div>
      {info.is_simulation && <p role="note"><strong>SIMULACIÓN — SIN REEMBOLSO.</strong> Esta prueba no genera derecho a compensación.</p>}
      <p role="status">{message}</p>
      <p>Para retirar tu autorización comercial o solicitar la supresión de las fotografías recibidas por correo, escribe a <a href="mailto:admin@metalwolft.com">admin@metalwolft.com</a>. Son solicitudes distintas y las atenderemos por separado.</p>
      {oppositionControl}
    </div>
  );

  return (
    <form className="mw-contact-form mw-issue-report-form" onSubmit={submit}>
      {info.is_simulation && <p role="note"><strong>SIMULACIÓN — SIN REEMBOLSO.</strong> Esta prueba no genera derecho a compensación, aunque las fotografías sean aprobadas.</p>}
      <p>Fotografía una sola reja, aunque tu pedido incluya varias. Bastan fotos hechas con móvil: procura buena luz, enfoque y encuadre.</p>
      <p>Evita personas identificables, matrículas, números de vivienda u otros datos que permitan identificar domicilios o terceros.</p>
      <p>Las imágenes se ajustan automáticamente si es necesario y se envían por correo a MetalWolft. No se guardan en el panel. El conjunto procesado no puede superar {Math.round(info.max_total_bytes / (1024 * 1024))} MB.</p>
      {info.mode === "incentive" && (
        <p>Participa dentro de los 30 días posteriores a la entrega. La revisión se comunicará en un máximo de 7 días naturales; podríamos pedirte fotos corregidas por correo. Para participar por 20 € debes aceptar expresamente la licencia de uso comercial descrita abajo. La revisión no garantiza un reembolso. Consulta las condiciones antes de enviarlas.</p>
      )}
      <div className="mw-customer-photo-fields">
        {([
          { kind: "front" as const, title: "Fotografía frontal (obligatoria)", hint: "Reja completa, centrada y de frente.", photo: frontPhoto },
          { kind: "perspective" as const, title: "Fotografía lateral o en perspectiva (obligatoria)", hint: "La misma reja: muestra su profundidad y cómo queda instalada.", photo: perspectivePhoto }
        ]).map(({ kind, title, hint, photo }) => (
          <div className="mw-customer-photo-field" key={kind}>
            <label className="mw-field">
              <span>{title}</span>
              <small>{hint}</small>
              <input type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => selectPhotos(event, kind)} disabled={busy} required={!photo} />
            </label>
            {photo && <div className="mw-customer-photo-preview">
              {/* Blob previews stay in memory and never use the public image optimizer. */}
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={photo.url} alt={`Vista previa: ${title}`} />
              <span>{photo.file.name}</span>
              <button type="button" onClick={() => removePhoto(photo.id)} disabled={busy}>Eliminar</button>
            </div>}
          </div>
        ))}
      </div>
      <div className="mw-customer-photo-field">
        <label className="mw-field">
          <span>Fotografías adicionales (opcionales, hasta tres)</span>
          <small>Si quieres, añade detalles u otras perspectivas. JPEG, PNG o WebP; máximo 5 MB por imagen.</small>
          <input type="file" accept="image/jpeg,image/png,image/webp" multiple onChange={(event) => selectPhotos(event, "additional")} disabled={busy || additionalPhotos.length >= 3} />
        </label>
        {additionalPhotos.length > 0 && <div className="mw-customer-photo-additional">
          {additionalPhotos.map((photo, index) => <div className="mw-customer-photo-preview" key={photo.id}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={photo.url} alt={`Vista previa de fotografía adicional ${index + 1}`} />
            <span>{photo.file.name}</span>
            <button type="button" onClick={() => removePhoto(photo.id)} disabled={busy}>Eliminar</button>
          </div>)}
        </div>}
      </div>
      <section aria-label="Condiciones de participación">
        <h3>Condiciones de participación</h3>
        <p>{info.terms_text}</p>
        {info.terms_url && <p><a href={info.terms_url} target="_blank" rel="noopener noreferrer">Leer condiciones completas</a></p>}
      </section>
      <fieldset>
        <legend>Licencia de uso comercial, versión {info.terms_version}{info.mode === "incentive" ? " (necesaria para la promoción)" : " (opcional)"}</legend>
        <p>{info.consent_text}</p>
        <p>Esta licencia de explotación fotográfica es distinta del tratamiento de datos personales y no limita tus derechos de protección de datos.</p>
        {info.mode === "incentive" ? (
          <label><input type="checkbox" name="commercial-consent" checked={consent === "yes"} onChange={(event) => setConsent(event.target.checked ? "yes" : "")} /> Acepto expresamente la licencia comercial descrita para participar en la promoción de 20 €.</label>
        ) : (
          <>
            <label><input type="radio" name="commercial-consent" value="yes" checked={consent === "yes"} onChange={() => setConsent("yes")} /> Sí, acepto la licencia de uso comercial descrita.</label>
            <label><input type="radio" name="commercial-consent" value="no" checked={consent === "no"} onChange={() => setConsent("no")} /> No autorizo el uso comercial; envío las fotografías voluntariamente.</label>
          </>
        )}
      </fieldset>
      <p>{info.mode === "free" ? "Puedes enviar fotografías sin conceder licencia comercial. Recibirlas no nos autoriza a publicarlas." : "Sin aceptar la licencia no puedes participar en la promoción de 20 €. Puedes consultarnos sobre un envío voluntario sin incentivo."} No publicaremos ninguna automáticamente.</p>
      <p>Puedes retirar después tu autorización comercial escribiendo a <a href="mailto:admin@metalwolft.com">admin@metalwolft.com</a>. Retirar la autorización no elimina automáticamente las fotos recibidas por correo; si deseas solicitar su supresión, indícalo expresamente.</p>
      {oppositionControl}
      <p>Consulta también nuestra <a href="/politica-privacidad">política de privacidad</a>.</p>
      <button className="mw-button mw-button--primary" type="submit" disabled={busy || !frontPhoto || !perspectivePhoto || !consent || (info.mode === "incentive" && consent !== "yes")}>
        {busy ? "Enviando…" : "Enviar fotografías"}
      </button>
      {message && <p role="status">{message}</p>}
    </form>
  );
}
