"use client";

import { useEffect, useRef, useState } from "react";
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
  downloadAll: {
    onClick: () => void;
    isDownloading: boolean;
    error: string | null;
  } | null;
};
type FileProps = Pick<Props, "orderId" | "onSessionExpired">;

function usePrivateFile(orderId: number, file: CustomerDesignFile, onSessionExpired: () => void, enabled = true) {
  const [url, setUrl] = useState<string | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!enabled) return;
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
  }, [enabled, file, onSessionExpired, orderId]);

  return { url, error };
}

function PrivateModelFallback({ orderId, image, onSessionExpired }: FileProps & { image?: CustomerDesignFile }) {
  return image ? <PrivateModelFallbackImage orderId={orderId} file={image} onSessionExpired={onSessionExpired} />
    : <p role="alert">No se pudo mostrar el modelo 3D. Puedes consultar los documentos del diseño.</p>;
}

function PrivateModelFallbackImage({ orderId, file, onSessionExpired }: FileProps & { file: CustomerDesignFile }) {
  const { url, error } = usePrivateFile(orderId, file, onSessionExpired);
  return (
    <div className="mw-design-delivery__model-fallback" role="status">
      {url ? <>{/* eslint-disable-next-line @next/next/no-img-element */}<img src={url} alt={`Imagen real del diseño: ${file.filename}`} /></>
        : <p>{error ? "No se pudo cargar la imagen del diseño." : "Cargando imagen del diseño…"}</p>}
      <p>La vista interactiva no está disponible. Esta es una imagen del diseño entregado.</p>
    </div>
  );
}

function PrivateModel({ orderId, file, image, label, onSessionExpired }: FileProps & { file: CustomerDesignFile; image?: CustomerDesignFile; label: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [nearViewport, setNearViewport] = useState(false);
  useEffect(() => {
    const container = containerRef.current;
    if (!container || !("IntersectionObserver" in window)) {
      setNearViewport(true);
      return;
    }
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setNearViewport(true);
        observer.disconnect();
      }
    }, { rootMargin: "240px 0px" });
    observer.observe(container);
    return () => observer.disconnect();
  }, []);
  const { url, error } = usePrivateFile(orderId, file, onSessionExpired, nearViewport);
  const fallback = <PrivateModelFallback orderId={orderId} image={image} onSessionExpired={onSessionExpired} />;
  return (
    <div ref={containerRef} className="mw-design-delivery__model">
      {error ? fallback : url ? <ModernGrilleViewerLoader key={url} modelUrl={url} label={label} fallback={fallback} />
        : <p role="status">{nearViewport ? "Preparando el modelo 3D…" : "El modelo 3D se cargará al acercarte."}</p>}
    </div>
  );
}

function PrivateImage({ orderId, file, onSessionExpired, onEnlarge }: FileProps & {
  file: CustomerDesignFile;
  onEnlarge: (url: string, file: CustomerDesignFile) => void;
}) {
  const { url, error } = usePrivateFile(orderId, file, onSessionExpired);
  return (
    <div className="mw-design-delivery__image">
      {url ? (
        <button type="button" onClick={() => onEnlarge(url, file)} aria-label={`Ampliar ${file.filename}`}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={url} alt={file.filename} />
        </button>
      ) : <span role={error ? "alert" : "status"}>{error ? "Imagen no disponible" : "Cargando imagen…"}</span>}
    </div>
  );
}

export function DesignDeliveryView({ orderId, delivery, purchaseItems, onSessionExpired, downloadAll }: Props) {
  const [preview, setPreview] = useState<{ url: string; file: CustomerDesignFile } | null>(null);
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
      <div className="mw-account-section-heading mw-design-delivery__heading">
        <div>
          <p className="mw-note">Tu diseño previo</p>
          <h3 id="design-delivery-title">Diseños preparados</h3>
        </div>
        {downloadAll ? <button
          className="mw-button mw-button--primary mw-customer-order-invoice__button"
          type="button"
          onClick={downloadAll.onClick}
          disabled={downloadAll.isDownloading}
        >{downloadAll.isDownloading ? "Descargando..." : "Descargar todos los archivos"}</button> : null}
      </div>
      {downloadAll?.error ? <p className="mw-customer-order-invoice__error" role="alert">{downloadAll.error}</p> : null}
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
                <h5>Modelo 3D</h5>
                <PrivateModel orderId={orderId} file={model} image={images[0]} label={`Modelo 3D de ${item.product_name}`} onSessionExpired={onSessionExpired} />
              </div>
            ) : null}
            {images.length ? (
              <div className="mw-design-delivery__media">
                <h5>Imágenes</h5>
                <div className="mw-design-delivery__gallery">
                  {images.map((file) => <PrivateImage key={file.id} orderId={orderId} file={file} onSessionExpired={onSessionExpired} onEnlarge={(url, selectedFile) => { setDownloadError(null); setPreview({ url, file: selectedFile }); }} />)}
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
        <div className="mw-design-delivery__lightbox" role="dialog" aria-modal="true" aria-label={`Vista ampliada: ${preview.file.filename}`} onClick={() => setPreview(null)}>
          <div className="mw-design-delivery__lightbox-actions">
            <button type="button" onClick={(event) => { event.stopPropagation(); void download(preview.file); }} disabled={downloadingId !== null}>Descargar imagen</button>
            <button type="button" onClick={() => setPreview(null)}>Cerrar imagen</button>
          </div>
          {downloadError ? <p role="alert" onClick={(event) => event.stopPropagation()}>{downloadError}</p> : null}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={preview.url} alt={preview.file.filename} onClick={(event) => event.stopPropagation()} />
        </div>
      ) : null}
    </section>
  );
}
