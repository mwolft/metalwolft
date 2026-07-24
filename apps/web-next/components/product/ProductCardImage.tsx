"use client";

import Image from "next/image";
import { useState } from "react";

type ProductCardImageProps = {
  src: string | null;
  alt: string;
};

const PRODUCT_IMAGE_SIZES =
  "(min-width: 1200px) 340px, (min-width: 900px) 29vw, (min-width: 620px) 44vw, calc(100vw - 5rem)";

function isAvifUrl(src: string) {
  return src.split(/[?#]/)[0].toLowerCase().endsWith(".avif");
}

export function ProductCardImage({ src, alt }: ProductCardImageProps) {
  const [failed, setFailed] = useState(false);

  if (!src || failed) {
    return (
      <span
        className="mw-product-card__image-fallback"
        role="img"
        aria-label={`Imagen no disponible de ${alt}`}
      >
        Imagen no disponible
      </span>
    );
  }

  return (
    <Image
      src={src}
      alt={alt}
      fill
      sizes={PRODUCT_IMAGE_SIZES}
      unoptimized={isAvifUrl(src)}
      onError={() => setFailed(true)}
    />
  );
}
