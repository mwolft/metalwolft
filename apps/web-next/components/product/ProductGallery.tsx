"use client";

import Image from "next/image";
import { useState, type KeyboardEvent } from "react";
import {
  getAdjacentProductImageSrc,
  type ProductGalleryDirection,
  type ProductGalleryImage
} from "@/lib/product-images";

type ProductGalleryProps = {
  images: ProductGalleryImage[];
  productName: string;
};

function isAvifUrl(src: string) {
  return src.split(/[?#]/)[0].toLowerCase().endsWith(".avif");
}

export function ProductGallery({ images, productName }: ProductGalleryProps) {
  const [selectedSrc, setSelectedSrc] = useState(images[0]?.src ?? "");
  const [failedSources, setFailedSources] = useState<Set<string>>(() => new Set());
  const availableImages = images.filter((image) => !failedSources.has(image.src));
  const selectedImage =
    availableImages.find((image) => image.src === selectedSrc) ?? availableImages[0] ?? null;

  function markImageAsFailed(src: string) {
    setFailedSources((current) => {
      const next = new Set(current);
      next.add(src);
      return next;
    });
  }

  function selectAdjacentImage(direction: ProductGalleryDirection) {
    if (!selectedImage || availableImages.length < 2) {
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

  return (
    <section
      className="mw-product-gallery"
      aria-label={`Imágenes de ${productName}`}
      onKeyDown={handleGalleryKeyDown}
      tabIndex={0}
    >
      <div className="mw-product-gallery__stage">
        {selectedImage ? (
          <Image
            key={selectedImage.src}
            src={selectedImage.src}
            alt={selectedImage.alt}
            fill
            sizes="(max-width: 900px) calc(100vw - 2rem), 55vw"
            priority={selectedImage.src === images[0]?.src}
            unoptimized={isAvifUrl(selectedImage.src)}
            onError={() => markImageAsFailed(selectedImage.src)}
          />
        ) : (
          <div className="mw-product-gallery__placeholder" role="img" aria-label={productName}>
            <span>Imagen no disponible</span>
          </div>
        )}

        {selectedImage && availableImages.length > 1 ? (
          <>
            <button
              className="mw-product-gallery__control mw-product-gallery__control--previous"
              type="button"
              aria-label={`Mostrar imagen anterior de ${productName}`}
              onClick={() => selectAdjacentImage(-1)}
            >
              <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                <path d="m15 5-7 7 7 7" />
              </svg>
            </button>
            <button
              className="mw-product-gallery__control mw-product-gallery__control--next"
              type="button"
              aria-label={`Mostrar imagen siguiente de ${productName}`}
              onClick={() => selectAdjacentImage(1)}
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
