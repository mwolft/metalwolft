"use client";

import { useEffect, useState } from "react";
import { ModernGrilleViewerLoader } from "@/components/visualization/ModernGrilleViewerLoader";
import { DesignPurchaseCard } from "@/components/account/DesignPurchaseCard";
import { getToken } from "@/lib/auth-client";
import {
  fetchCustomerDesignFile,
  isCustomerOrdersSessionError,
  type CustomerDesignDelivery,
  type CustomerDesignFile,
  type CustomerDesignPurchaseItem
} from "@/lib/customer-orders-client";

type Props = {
  orderId: number;
  delivery: CustomerDesignDelivery;
  purchaseItems: CustomerDesignPurchaseItem[];
  onSessionExpired: () => void;
};
type FileProps = Pick<Props, "orderId" | "onSessionExpired">;

function usePrivateFile(orderId: number, file: CustomerDesignFile, onSessionExpired: () => void) {
  const [url, setUrl] = useState<string | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;
    let objectUrl: string | null = null;
    const token = getToken();
    if (!token) {
      onSessionExpired();
      return;
    }
    fetchCustomerDesignFile(token, orderId, file).then(({ blob }) => {
      if (!active) return;
      objectUrl = URL.createObjectURL(blob);
      setUrl(objectUrl);
    }).catch((cause) => {
      if (!active) return;
      if (isCustomerOrdersSessionError(cause)) onSessionExpired();
      else setError(true);
    });
    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [file, onSessionExpired, orderId]);

  return { url, error };
}

function PrivateModel({ orderId, file, label, onSessionExpired }: FileProps & { file: CustomerDesignFile; label: string }) {
  const { url, error } = usePrivateFile(orderId, file, onSessionExpired);
  if (error) return <p role="alert">No se pudo cargar el modelo 3D. Puedes descargar los archivos.</p>;
  if (!url) return <p role="status">Preparando el modelo 3D…</p>;
  return <ModernGrilleViewerLoader key={url} modelUrl={url} label={label} />;
}

function PrivateImage({ orderId, file, onSessionExpired, onEnlarge, onDownload }: FileProps & {
  file: CustomerDesignFile;
  onEnlarge: (url: string, label: string) => void;
  onDownload: (file: CustomerDesignFile) => void;
}) {
  const { url, error } = usePrivateFile(orderId, file, onSessionExpired);
  return (
    <div className="mw-design-delivery__image">
      {url ? (
        <button type="button" onClick={() => onEnlarge(url, file.filename)} aria-label={`Ampliar ${file.filename}`}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={url} alt={file.filename} />
        </button>
      ) : <span role={error ? "alert" : "status"}>{error ? "Imagen no disponible" : "Cargando imagen…"}</span>}
      <button className="mw-button mw-button--secondary" type="button" onClick={() => onDownload(file)}>Descargar imagen</button>
    </div>
  );
}

export function DesignDeliveryView({ orderId, delivery, purchaseItems, onSessionExpired }: Props) {
  const [activeModelId, setActiveModelId] = useState<number | null>(null);
  const [preview, setPreview] = useState<{ url: string; label: string } | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [downloadingId, setDownloadingId] = useState<number | null>(null);

  useEffect(() => {
    if (!preview) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setPreview(null);
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [preview]);

  async function download(file: CustomerDesignFile) {
    if (downloadingId !== null) return;
    const token = getToken();
    if (!token) return onSessionExpired();
    setDownloadingId(file.id);
    setDownloadError(null);
    try {
      const result = await fetchCustomerDesignFile(token, orderId, file);
      const url = URL.createObjectURL(result.blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = result.filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 30_000);
    } catch (cause) {
      if (isCustomerOrdersSessionError(cause)) onSessionExpired();
      else setDownloadError("No se pudo descargar el archivo. Inténtalo de nuevo.");
    } finally {
      setDownloadingId(null);
    }
  }

  return (
    <section className="mw-account-card mw-design-delivery" aria-labelledby="design-delivery-title">
      <div className="mw-account-section-heading">
        <p className="mw-note">Tu diseño previo</p>
        <h3 id="design-delivery-title">Diseños preparados</h3>
      </div>
      {delivery.message ? <p className="mw-design-delivery__message">{delivery.message}</p> : null}
      {delivery.items.map((item) => {
        const model = item.files.find((file) => file.kind === "glb");
        const images = item.files.filter((file) => file.kind === "image");
        const documents = item.files.filter((file) => file.kind === "pdf");
        const purchaseItem = purchaseItems.find((candidate) => candidate.id === item.id);
        return (
          <article className="mw-design-delivery__item" key={item.id}>
            <h4>{item.product_name}</h4>
            <p>Alto {item.height_cm} cm × Ancho {item.width_cm} cm</p>
            {model ? (
              <div className="mw-design-delivery__media">
                <button className="mw-button mw-button--secondary" type="button" onClick={() => setActiveModelId(activeModelId === model.id ? null : model.id)}>
                  {activeModelId === model.id ? "Cerrar vista 3D" : "Ver diseño en 3D"}
                </button>
                {activeModelId === model.id ? <PrivateModel orderId={orderId} file={model} label={`Modelo 3D de ${item.product_name}`} onSessionExpired={onSessionExpired} /> : null}
              </div>
            ) : null}
            {images.length ? (
              <div className="mw-design-delivery__media">
                <h5>Imágenes</h5>
                <div className="mw-design-delivery__gallery">
                  {images.map((file) => <PrivateImage key={file.id} orderId={orderId} file={file} onSessionExpired={onSessionExpired} onEnlarge={(url, label) => setPreview({ url, label })} onDownload={download} />)}
                </div>
              </div>
            ) : null}
            {documents.length ? (
              <div className="mw-design-delivery__media">
                <h5>Documentos</h5>
                <ul className="mw-design-delivery__documents">
                  {documents.map((file) => <li key={file.id}><span>{file.filename}</span><button className="mw-button mw-button--secondary" type="button" onClick={() => download(file)} disabled={downloadingId !== null}>Descargar PDF</button></li>)}
                </ul>
              </div>
            ) : null}
            {purchaseItem ? <DesignPurchaseCard item={purchaseItem} /> : null}
          </article>
        );
      })}
      {downloadError ? <p role="alert">{downloadError}</p> : null}
      {preview ? (
        <div className="mw-design-delivery__lightbox" role="dialog" aria-modal="true" aria-label={`Vista ampliada: ${preview.label}`} onClick={() => setPreview(null)}>
          <button type="button" onClick={() => setPreview(null)}>Cerrar imagen</button>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={preview.url} alt={preview.label} onClick={(event) => event.stopPropagation()} />
        </div>
      ) : null}
    </section>
  );
}
