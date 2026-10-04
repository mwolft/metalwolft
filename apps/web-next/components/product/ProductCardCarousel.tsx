"use client";

import Image from "next/image";
import Link from "next/link";
import { useRef, useState, type PointerEvent } from "react";
import {
  getAdjacentProductImageSrc,
  type ProductGalleryDirection,
  type ProductGalleryImage
} from "@/lib/product-images";

type ProductCardCarouselProps = {
  images: ProductGalleryImage[];
  productName: string;
  href: string;
};

type PointerOrigin = { pointerId: number; x: number; y: number };

const SWIPE_THRESHOLD_PX = 50;
const POST_SWIPE_CLICK_DELAY_MS = 350;
const PRODUCT_IMAGE_SIZES =
  "(min-width: 1200px) 340px, (min-width: 900px) 29vw, (min-width: 620px) 44vw, calc(100vw - 5rem)";

function isAvifUrl(src: string) {
  return src.split(/[?#]/)[0].toLowerCase().endsWith(".avif");
}

export function ProductCardCarousel({ images, productName, href }: ProductCardCarouselProps) {
  const [selectedSrc, setSelectedSrc] = useState(images[0]?.src ?? "");
  const [failedSources, setFailedSources] = useState<Set<string>>(() => new Set());
  const pointerOriginRef = useRef<PointerOrigin | null>(null);
  const suppressClickUntilRef = useRef(0);
  const availableImages = images.filter((image) => !failedSources.has(image.src));
  const selectedImage =
    availableImages.find((image) => image.src === selectedSrc) ?? availableImages[0] ?? null;
  const selectedIndex = selectedImage
    ? availableImages.findIndex((image) => image.src === selectedImage.src)
    : -1;
  const hasNavigation = availableImages.length > 1;

  function selectAdjacentImage(direction: ProductGalleryDirection) {
    if (selectedImage && hasNavigation) {
      setSelectedSrc(getAdjacentProductImageSrc(availableImages, selectedImage.src, direction));
    }
  }

  function handlePointerDown(event: PointerEvent<HTMLDivElement>) {
    if (!hasNavigation || !event.isPrimary || event.pointerType !== "touch" ||
      (event.target instanceof HTMLElement && event.target.closest("button"))) {
      return;
    }

    pointerOriginRef.current = {
      pointerId: event.pointerId,
      x: event.clientX,
      y: event.clientY
    };
  }

  function handlePointerUp(event: PointerEvent<HTMLDivElement>) {
    const origin = pointerOriginRef.current;
    pointerOriginRef.current = null;
    if (!origin || origin.pointerId !== event.pointerId) {
      return;
    }

    const horizontalDistance = event.clientX - origin.x;
    const verticalDistance = event.clientY - origin.y;
    if (Math.abs(horizontalDistance) < SWIPE_THRESHOLD_PX ||
      Math.abs(horizontalDistance) <= Math.abs(verticalDistance)) {
      return;
    }

    selectAdjacentImage(horizontalDistance < 0 ? 1 : -1);
    suppressClickUntilRef.current = Date.now() + POST_SWIPE_CLICK_DELAY_MS;
  }

  return (
    <div
      className="mw-product-card__carousel"
      onPointerDown={handlePointerDown}
      onPointerUp={handlePointerUp}
      onPointerCancel={() => { pointerOriginRef.current = null; }}
    >
      <Link
        className="mw-product-card__carousel-link"
        href={href}
        aria-label={`Ver modelo ${productName}`}
        onClick={(event) => {
          if (Date.now() < suppressClickUntilRef.current) {
            event.preventDefault();
            suppressClickUntilRef.current = 0;
          }
        }}
        onDragStart={(event) => event.preventDefault()}
      >
        {selectedImage ? (
          <Image
            key={selectedImage.src}
            src={selectedImage.src}
            alt={selectedImage.isPrimary ? productName : selectedImage.alt}
            fill
            sizes={PRODUCT_IMAGE_SIZES}
            unoptimized={isAvifUrl(selectedImage.src)}
            draggable={false}
            onError={() => setFailedSources((current) => new Set(current).add(selectedImage.src))}
          />
        ) : (
          <span className="mw-product-card__image-fallback" role="img" aria-label={`Imagen no disponible de ${productName}`}>
            Imagen no disponible
          </span>
        )}
      </Link>

      {hasNavigation ? (
        <>
          <button
            className="mw-product-card__carousel-control mw-product-card__carousel-control--previous"
            type="button"
            aria-label={`Imagen anterior de ${productName}`}
            onClick={(event) => { event.stopPropagation(); selectAdjacentImage(-1); }}
          >
            <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="m15 5-7 7 7 7" />
            </svg>
          </button>
          <button
            className="mw-product-card__carousel-control mw-product-card__carousel-control--next"
            type="button"
            aria-label={`Imagen siguiente de ${productName}`}
            onClick={(event) => { event.stopPropagation(); selectAdjacentImage(1); }}
          >
            <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="m9 5 7 7-7 7" />
            </svg>
          </button>
          <div className="mw-product-card__carousel-dots" aria-hidden="true">
            {availableImages.map((image) => (
              <span
                className="mw-product-card__carousel-dot"
                data-active={image.src === selectedImage?.src ? "true" : undefined}
                key={image.src}
              />
            ))}
          </div>
        </>
      ) : null}
    </div>
  );
}
