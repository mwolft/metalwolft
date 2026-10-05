import type { ApiProduct } from "@/lib/api";

export const ABATIBLE_COLLECTION_SLUGS = [
  "reja-abatible-albany",
  "reja-abatible-cortland",
  "reja-abatible-essex",
  "reja-abatible-idaho",
  "reja-abatible-maryland-para-ventanas",
] as const;

export function selectAbatibleCollection(products: ApiProduct[]) {
  const bySlug = new Map(products.map((product) => [product.slug, product]));
  return ABATIBLE_COLLECTION_SLUGS.flatMap((slug) => {
    const product = bySlug.get(slug);
    return product ? [product] : [];
  });
}
