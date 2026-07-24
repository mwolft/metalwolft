"use client";

import Image from "next/image";
import { useState } from "react";
import type { ProductGalleryImage } from "@/lib/product-images";

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

  return (
    <section className="mw-product-gallery" aria-label={`Imágenes de ${productName}`}>
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
