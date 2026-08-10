"use client";

import type { ChangeEvent, FormEvent } from "react";
import { useEffect, useRef, useState } from "react";

const MAX_IMAGES = 3;
const CLIENT_LOCAL_API_URL = "http://127.0.0.1:3001";

const ISSUE_TYPES = [
  "Pintura o acabado",
  "Medidas o encaje",
  "Transporte o embalaje",
  "Otro"
] as const;

type IssueReportValues = {
  name: string;
  email: string;
  order_number: string;
  issue_type: "" | (typeof ISSUE_TYPES)[number];
  message: string;
};

type SelectedImage = {
  file: File;
  id: string;
  previewUrl: string;
};

const INITIAL_VALUES: IssueReportValues = {
  name: "",
  email: "",
  order_number: "",
  issue_type: "",
  message: ""
};

function resolveClientApiBaseUrl() {
  const configuredApiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();

  if (configuredApiUrl) {
    return { url: configuredApiUrl.replace(/\/$/, ""), error: null };
  }

  if (process.env.NODE_ENV !== "production") {
    return { url: CLIENT_LOCAL_API_URL, error: null };
  }

  return {
    url: null,
    error: "El formulario no está disponible en este entorno ahora mismo."
  };
}

export function IssueReportForm() {
  const [values, setValues] = useState<IssueReportValues>(INITIAL_VALUES);
  const [images, setImages] = useState<SelectedImage[]>([]);
  const [imageFeedback, setImageFeedback] = useState<string | null>(null);
  const [status, setStatus] = useState<{ type: "success" | "error"; message: string } | null>(
    null
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const previewUrls = useRef(new Set<string>());
  const apiConfig = resolveClientApiBaseUrl();

  useEffect(() => {
    return () => {
      previewUrls.current.forEach((url) => URL.revokeObjectURL(url));
    };
  }, []);

  function handleChange(event: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) {
    const { name, value } = event.target;
    setValues((current) => ({ ...current, [name]: value }));
  }

  function removeImage(imageId: string) {
    setImages((current) => {
      const selected = current.find((image) => image.id === imageId);
      if (selected) {
        URL.revokeObjectURL(selected.previewUrl);
        previewUrls.current.delete(selected.previewUrl);
      }
      return current.filter((image) => image.id !== imageId);
    });
    setImageFeedback(null);
  }

  function handleImageChange(event: ChangeEvent<HTMLInputElement>) {
    const selectedFiles = Array.from(event.target.files || []);
    const availableSlots = Math.max(0, MAX_IMAGES - images.length);
    const filesToAdd = selectedFiles.slice(0, availableSlots);

    if (selectedFiles.length > availableSlots) {
      setImageFeedback(`Puedes adjuntar un máximo de ${MAX_IMAGES} imágenes.`);
    } else {
      setImageFeedback(null);
    }

    if (filesToAdd.length > 0) {
      const newImages = filesToAdd.map((file) => {
        const previewUrl = URL.createObjectURL(file);
        previewUrls.current.add(previewUrl);
        return { file, id: previewUrl, previewUrl };
      });
      setImages((current) => [...current, ...newImages]);
    }

    event.target.value = "";
  }

  function clearImages() {
    images.forEach((image) => {
      URL.revokeObjectURL(image.previewUrl);
      previewUrls.current.delete(image.previewUrl);
    });
    setImages([]);
    setImageFeedback(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus(null);

    if (!apiConfig.url) {
      setStatus({ type: "error", message: apiConfig.error || "No se pudo enviar la incidencia." });
      return;
    }

    setIsSubmitting(true);

    try {
      const body = new FormData();
      body.append("name", values.name);
      body.append("email", values.email);
      body.append("order_number", values.order_number);
      body.append("issue_type", values.issue_type);
      body.append("message", values.message);
      images.forEach((image) => body.append("images", image.file));

      const response = await fetch(`${apiConfig.url}/api/email/report-issue`, {
        method: "POST",
        body
      });
      const payload = (await response.json().catch(() => null)) as
        | { message?: string; error?: string }
        | null;

      if (!response.ok) {
        throw new Error(payload?.error || "No se pudo enviar la incidencia.");
      }

      setValues(INITIAL_VALUES);
      clearImages();
      setStatus({
        type: "success",
        message: "Incidencia enviada correctamente. Te contactaremos en breve."
      });
    } catch (error) {
      setStatus({
        type: "error",
        message: error instanceof Error ? error.message : "No se pudo enviar la incidencia."
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="mw-contact-form mw-issue-report-form" onSubmit={handleSubmit}>
      <div className="mw-form-grid">
        <label className="mw-field">
          <span>Nombre</span>
          <input
            autoComplete="name"
            name="name"
            onChange={handleChange}
            required
            type="text"
            value={values.name}
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

        <label className="mw-field">
          <span>Número de pedido</span>
          <input
            name="order_number"
            onChange={handleChange}
            placeholder="Ejemplo: MW1234"
            required
            type="text"
            value={values.order_number}
          />
        </label>

        <label className="mw-field">
          <span>Tipo de incidencia</span>
          <select name="issue_type" onChange={handleChange} required value={values.issue_type}>
            <option value="">Selecciona una opción</option>
            {ISSUE_TYPES.map((issueType) => (
              <option key={issueType} value={issueType}>
                {issueType}
              </option>
            ))}
          </select>
        </label>

        <label className="mw-field mw-field--full">
          <span>Mensaje <small>Opcional</small></span>
          <textarea
            name="message"
            onChange={handleChange}
            placeholder="Describe brevemente la incidencia..."
            rows={5}
            value={values.message}
          />
        </label>

        <div className="mw-field mw-field--full">
          <span id="issue-images-label">Imágenes <small>Opcional</small></span>
          <input
            accept="image/jpeg,image/png,image/webp"
            aria-describedby="issue-images-help"
            aria-labelledby="issue-images-label"
            className="mw-issue-report-form__file-input"
            multiple
            onChange={handleImageChange}
            type="file"
          />
          <small className="mw-field-helper" id="issue-images-help">
            Puedes adjuntar hasta 3 imágenes en formato JPG, PNG o WebP.
          </small>
          {imageFeedback ? (
            <p aria-live="polite" className="mw-issue-report-form__feedback">
              {imageFeedback}
            </p>
          ) : null}
        </div>
      </div>

      {images.length > 0 ? (
        <ul className="mw-issue-report-form__previews" aria-label="Imágenes adjuntas">
          {images.map((image) => (
            <li key={image.id}>
              <img alt={`Vista previa de ${image.file.name}`} src={image.previewUrl} />
              <div>
                <span>{image.file.name}</span>
                <button onClick={() => removeImage(image.id)} type="button">
                  Quitar imagen
                </button>
              </div>
            </li>
          ))}
        </ul>
      ) : null}

      <div className="mw-actions">
        <button
          className="mw-button mw-button--primary"
          disabled={isSubmitting || !apiConfig.url}
          type="submit"
        >
          {isSubmitting ? "Enviando..." : "Enviar incidencia"}
        </button>
      </div>

      {status ? (
        <p
          aria-live="polite"
          className={`mw-alert ${status.type === "success" ? "mw-alert--success" : "mw-alert--error"}`}
        >
          {status.message}
        </p>
      ) : null}
    </form>
  );
}
