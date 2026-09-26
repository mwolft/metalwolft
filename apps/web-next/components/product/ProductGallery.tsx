"use client";

import Image from "next/image";
import {
  useEffect,
  useRef,
  useState,
  type KeyboardEvent,
  type MouseEvent,
  type PointerEvent
} from "react";
import { createPortal } from "react-dom";
import {
  getAdjacentProductImageSrc,
  type ProductGalleryDirection,
  type ProductGalleryImage
} from "@/lib/product-images";

type ProductGalleryProps = {
  images: ProductGalleryImage[];
  productName: string;
};

type PointerOrigin = {
  pointerId: number;
  x: number;
  y: number;
};

const SWIPE_THRESHOLD_PX = 50;
const POST_SWIPE_CLICK_DELAY_MS = 350;

function isAvifUrl(src: string) {
  return src.split(/[?#]/)[0].toLowerCase().endsWith(".avif");
}

export function ProductGallery({ images, productName }: ProductGalleryProps) {
  const [selectedSrc, setSelectedSrc] = useState(images[0]?.src ?? "");
  const [failedSources, setFailedSources] = useState<Set<string>>(() => new Set());
  const [horizontalSources, setHorizontalSources] = useState<Set<string>>(() => new Set());
  const [isLightboxOpen, setIsLightboxOpen] = useState(false);
  const pointerOriginRef = useRef<PointerOrigin | null>(null);
  const lightboxPointerOriginRef = useRef<PointerOrigin | null>(null);
  const lightboxRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const imageButtonRef = useRef<HTMLButtonElement>(null);
  const suppressClickRef = useRef(false);
  const suppressClickTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const availableImages = images.filter((image) => !failedSources.has(image.src));
  const selectedImage =
    availableImages.find((image) => image.src === selectedSrc) ?? availableImages[0] ?? null;
  const hasNavigation = Boolean(selectedImage && availableImages.length > 1);
  const selectedIndex = selectedImage
    ? availableImages.findIndex((image) => image.src === selectedImage.src)
    : -1;

  useEffect(
    () => () => {
      if (suppressClickTimerRef.current) {
        clearTimeout(suppressClickTimerRef.current);
      }
    },
    []
  );

  useEffect(() => {
    if (!isLightboxOpen) {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeButtonRef.current?.focus();

    return () => {
      document.body.style.overflow = previousOverflow;
      imageButtonRef.current?.focus();
    };
  }, [isLightboxOpen]);

  function markImageAsFailed(src: string) {
    setFailedSources((current) => {
      const next = new Set(current);
      next.add(src);
      return next;
    });
  }

  function rememberHorizontalImage(src: string, width: number, height: number) {
    if (!width || !height || width <= height) {
      return;
    }

    setHorizontalSources((current) => {
      if (current.has(src)) {
        return current;
      }

      const next = new Set(current);
      next.add(src);
      return next;
    });
  }

  function selectAdjacentImage(direction: ProductGalleryDirection) {
    if (!selectedImage || !hasNavigation) {
      return;
    }

    setSelectedSrc(getAdjacentProductImageSrc(availableImages, selectedImage.src, direction));
  }

  function handleGalleryKeyDown(event: KeyboardEvent<HTMLElement>) {
    const target = event.target;
    if (
      target instanceof HTMLElement &&
      target.closest("input, textarea, select, [contenteditable='true']")
    ) {
      return;
    }

    if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
      event.preventDefault();
      selectAdjacentImage(event.key === "ArrowLeft" ? -1 : 1);
    }
  }

  function suppressNextClick() {
    suppressClickRef.current = true;
    if (suppressClickTimerRef.current) {
      clearTimeout(suppressClickTimerRef.current);
    }
    suppressClickTimerRef.current = setTimeout(() => {
      suppressClickRef.current = false;
      suppressClickTimerRef.current = null;
    }, POST_SWIPE_CLICK_DELAY_MS);
  }

  function consumeSuppressedClick() {
    if (!suppressClickRef.current) {
      return false;
    }

    suppressClickRef.current = false;
    if (suppressClickTimerRef.current) {
      clearTimeout(suppressClickTimerRef.current);
      suppressClickTimerRef.current = null;
    }
    return true;
  }

  function handleNavigationClick(
    event: MouseEvent<HTMLElement>,
    direction: ProductGalleryDirection
  ) {
    event.stopPropagation();
    if (!consumeSuppressedClick()) {
      selectAdjacentImage(direction);
    }
  }

  function handlePointerDown(event: PointerEvent<HTMLDivElement>) {
    if (!hasNavigation || !event.isPrimary || event.button !== 0) {
      return;
    }

    pointerOriginRef.current = {
      pointerId: event.pointerId,
      x: event.clientX,
      y: event.clientY
    };
  }

  function resetPointerGesture() {
    pointerOriginRef.current = null;
  }

  function handlePointerUp(event: PointerEvent<HTMLDivElement>) {
    const origin = pointerOriginRef.current;
    resetPointerGesture();
    if (!hasNavigation || !origin || origin.pointerId !== event.pointerId) {
      return;
    }

    const horizontalDistance = event.clientX - origin.x;
    const verticalDistance = event.clientY - origin.y;
    if (
      Math.abs(horizontalDistance) < SWIPE_THRESHOLD_PX ||
      Math.abs(horizontalDistance) <= Math.abs(verticalDistance)
    ) {
      return;
    }

    selectAdjacentImage(horizontalDistance < 0 ? 1 : -1);
    suppressNextClick();
  }

  function handleLightboxKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    event.stopPropagation();
    if (event.key === "Escape") {
      event.preventDefault();
      setIsLightboxOpen(false);
    } else if (hasNavigation && (event.key === "ArrowLeft" || event.key === "ArrowRight")) {
      event.preventDefault();
      selectAdjacentImage(event.key === "ArrowLeft" ? -1 : 1);
    } else if (event.key === "Tab") {
      const buttons = lightboxRef.current?.querySelectorAll<HTMLButtonElement>("button");
      if (!buttons?.length) {
        return;
      }

      const first = buttons[0];
      const last = buttons[buttons.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
  }

  function handleLightboxPointerDown(event: PointerEvent<HTMLDivElement>) {
    if (!hasNavigation || !event.isPrimary || event.button !== 0 ||
      (event.target instanceof HTMLElement && event.target.closest("button"))) {
      return;
    }

    lightboxPointerOriginRef.current = {
      pointerId: event.pointerId,
      x: event.clientX,
      y: event.clientY
    };
  }

  function handleLightboxPointerUp(event: PointerEvent<HTMLDivElement>) {
    const origin = lightboxPointerOriginRef.current;
    lightboxPointerOriginRef.current = null;
    if (!hasNavigation || !origin || origin.pointerId !== event.pointerId) {
      return;
    }

    const horizontalDistance = event.clientX - origin.x;
    if (Math.abs(horizontalDistance) >= SWIPE_THRESHOLD_PX &&
      Math.abs(horizontalDistance) > Math.abs(event.clientY - origin.y)) {
      selectAdjacentImage(horizontalDistance < 0 ? 1 : -1);
    }
  }

  return (
    <section
      className="mw-product-gallery"
      aria-label={`Imágenes de ${productName}`}
      onKeyDown={handleGalleryKeyDown}
      tabIndex={0}
    >
      <div
        className="mw-product-gallery__stage"
        onClick={consumeSuppressedClick}
        onPointerCancel={resetPointerGesture}
        onPointerDown={handlePointerDown}
        onPointerUp={handlePointerUp}
      >
        {selectedImage ? (
          <button
            className="mw-product-gallery__open"
            type="button"
            aria-label={`Ampliar imagen de ${productName}`}
            aria-haspopup="dialog"
            ref={imageButtonRef}
            onClick={() => {
              if (!consumeSuppressedClick()) {
                setIsLightboxOpen(true);
              }
            }}
          >
            <Image
              key={selectedImage.src}
              src={selectedImage.src}
              alt={selectedImage.alt}
              fill
              sizes="(max-width: 900px) calc(100vw - 2rem), 55vw"
              priority={selectedImage.src === images[0]?.src}
              unoptimized={isAvifUrl(selectedImage.src)}
              draggable={false}
              style={horizontalSources.has(selectedImage.src) ? { objectFit: "cover" } : undefined}
              onLoad={(event) =>
                rememberHorizontalImage(
                  selectedImage.src,
                  event.currentTarget.naturalWidth,
                  event.currentTarget.naturalHeight
                )
              }
              onError={() => markImageAsFailed(selectedImage.src)}
            />
          </button>
        ) : (
          <div className="mw-product-gallery__placeholder" role="img" aria-label={productName}>
            <span>Imagen no disponible</span>
          </div>
        )}

        {hasNavigation ? (
          <>
            <span
              className="mw-product-gallery__hit-zone mw-product-gallery__hit-zone--previous"
              aria-hidden="true"
              onClick={(event) => handleNavigationClick(event, -1)}
            />
            <span
              className="mw-product-gallery__hit-zone mw-product-gallery__hit-zone--next"
              aria-hidden="true"
              onClick={(event) => handleNavigationClick(event, 1)}
            />
            <button
              className="mw-product-gallery__control mw-product-gallery__control--previous"
              type="button"
              aria-label={`Mostrar imagen anterior de ${productName}`}
              onClick={(event) => handleNavigationClick(event, -1)}
            >
              <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                <path d="m15 5-7 7 7 7" />
              </svg>
            </button>
            <button
              className="mw-product-gallery__control mw-product-gallery__control--next"
              type="button"
              aria-label={`Mostrar imagen siguiente de ${productName}`}
              onClick={(event) => handleNavigationClick(event, 1)}
            >
              <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                <path d="m9 5 7 7-7 7" />
              </svg>
            </button>
          </>
        ) : null}
      </div>

      {availableImages.length > 1 ? (
        <div className="mw-product-gallery__thumbnails" aria-label="Seleccionar imagen">
          {availableImages.map((image, index) => (
            <button
              className="mw-product-gallery__thumbnail"
              data-active={selectedImage?.src === image.src ? "true" : undefined}
              key={image.src}
              type="button"
              aria-label={`Mostrar imagen ${index + 1} de ${productName}`}
              aria-pressed={selectedImage?.src === image.src}
              onClick={() => setSelectedSrc(image.src)}
            >
              <Image
                src={image.src}
                alt=""
                fill
                sizes="72px"
                unoptimized={isAvifUrl(image.src)}
                onError={() => markImageAsFailed(image.src)}
              />
            </button>
          ))}
        </div>
      ) : null}

      {isLightboxOpen && selectedImage
        ? createPortal(
            <div
              className="mw-product-gallery__lightbox"
              role="dialog"
              aria-modal="true"
              aria-label={`Visor de imágenes de ${productName}`}
              ref={lightboxRef}
              onKeyDown={handleLightboxKeyDown}
              onClick={(event) => {
                if (event.target === event.currentTarget) {
                  setIsLightboxOpen(false);
                }
              }}
            >
              <div className="mw-product-gallery__lightbox-content">
                <div className="mw-product-gallery__lightbox-header">
                  <span aria-live="polite">{selectedIndex + 1} / {availableImages.length}</span>
                  <button
                    className="mw-product-gallery__lightbox-close"
                    type="button"
                    aria-label="Cerrar visor"
                    ref={closeButtonRef}
                    onClick={() => setIsLightboxOpen(false)}
                  >
                    <span aria-hidden="true">×</span>
                  </button>
                </div>
                <div
                  className="mw-product-gallery__lightbox-media"
                  onPointerDown={handleLightboxPointerDown}
                  onPointerUp={handleLightboxPointerUp}
                  onPointerCancel={() => { lightboxPointerOriginRef.current = null; }}
                >
                  <Image
                    key={selectedImage.src}
                    className="mw-product-gallery__lightbox-image"
                    src={selectedImage.src}
                    alt={selectedImage.alt}
                    fill
                    sizes="(max-width: 900px) 100vw, 90vw"
                    unoptimized={isAvifUrl(selectedImage.src)}
                    draggable={false}
                    onError={() => markImageAsFailed(selectedImage.src)}
                  />
                  {hasNavigation ? (
                    <>
                      <button
                        className="mw-product-gallery__lightbox-arrow mw-product-gallery__lightbox-arrow--previous"
                        type="button"
                        aria-label="Imagen anterior"
                        onClick={() => selectAdjacentImage(-1)}
                      >
                        <span aria-hidden="true">‹</span>
                      </button>
                      <button
                        className="mw-product-gallery__lightbox-arrow mw-product-gallery__lightbox-arrow--next"
                        type="button"
                        aria-label="Imagen siguiente"
                        onClick={() => selectAdjacentImage(1)}
                      >
                        <span aria-hidden="true">›</span>
                      </button>
                    </>
                  ) : null}
                </div>
                {hasNavigation ? (
                  <div className="mw-product-gallery__lightbox-thumbnails" aria-label="Seleccionar imagen ampliada">
                    {availableImages.map((image, index) => (
                      <button
                        className="mw-product-gallery__lightbox-thumbnail"
                        data-active={selectedImage.src === image.src ? "true" : undefined}
                        type="button"
                        key={image.src}
                        aria-label={`Mostrar imagen ${index + 1} de ${productName}`}
                        aria-pressed={selectedImage.src === image.src}
                        onClick={() => setSelectedSrc(image.src)}
                      >
                        <Image src={image.src} alt="" fill sizes="64px" unoptimized={isAvifUrl(image.src)} />
                      </button>
                    ))}
                  </div>
                ) : null}
              </div>
            </div>,
            document.body
          )
        : null}
    </section>
  );
}
