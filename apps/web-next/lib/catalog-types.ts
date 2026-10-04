import type { ApiProduct } from "@/lib/api";

export type CatalogType = "all" | "fixed" | "hinged" | "door" | "pets";
export type ProductCatalogType = Exclude<CatalogType, "all">;

export const CATALOG_FILTER_STORAGE_KEY = "mw-catalog-next-filter";

export function getProductCatalogType(product: Pick<ApiProduct, "slug" | "opening_type">): ProductCatalogType {
  if (product.slug.startsWith("reja-mascotas-")) return "pets";
  if (product.slug.startsWith("reja-puerta-")) return "door";
  return product.opening_type === "hinged" ? "hinged" : "fixed";
}

export function isLocalCatalogFilter(value: unknown): value is Exclude<CatalogType, "all" | "hinged"> {
  return value === "fixed" || value === "door" || value === "pets";
}
