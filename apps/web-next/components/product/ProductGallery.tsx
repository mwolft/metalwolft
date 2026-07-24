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
  const pointerOriginRef = useRef<PointerOrigin | null>(null);
  const suppressClickRef = useRef(false);
  const suppressClickTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const availableImages = images.filter((image) => !failedSources.has(image.src));
  const selectedImage =
    availableImages.find((image) => image.src === selectedSrc) ?? availableImages[0] ?? null;
  const hasNavigation = Boolean(selectedImage && availableImages.length > 1);

  useEffect(
    () => () => {
      if (suppressClickTimerRef.current) {
        clearTimeout(suppressClickTimerRef.current);
      }
    },
    []
  );

  function markImageAsFailed(src: string) {
    setFailedSources((current) => {
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
          <Image
            key={selectedImage.src}
            src={selectedImage.src}
            alt={selectedImage.alt}
            fill
            sizes="(max-width: 900px) calc(100vw - 2rem), 55vw"
            priority={selectedImage.src === images[0]?.src}
            unoptimized={isAvifUrl(selectedImage.src)}
            draggable={false}
            onError={() => markImageAsFailed(selectedImage.src)}
          />
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
    </section>
  );
}
