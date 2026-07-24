import type { ApiProduct } from "@/lib/api";

export type ProductGalleryImage = {
  src: string;
  alt: string;
  isPrimary: boolean;
};

export function buildProductGalleryImages(
  product: Pick<ApiProduct, "imagen" | "images" | "nombre">
): ProductGalleryImage[] {
  const candidates = [
    { src: product.imagen, isPrimary: true },
    ...(product.images ?? []).map((image) => ({
      src: image.image_url,
      isPrimary: false
    }))
  ];
  const seen = new Set<string>();

  return candidates.flatMap((candidate) => {
    const src = candidate.src?.trim();
    if (!src || seen.has(src)) {
      return [];
    }

    seen.add(src);
    const position = seen.size;
    return [
      {
        src,
        alt: candidate.isPrimary
          ? product.nombre
          : `Vista adicional ${position - 1} de ${product.nombre}`,
        isPrimary: candidate.isPrimary
      }
    ];
  });
}
