export type DesignServiceSeed = {
  product_slug: string;
  width_cm: number;
  height_cm: number;
};

type SearchParamsReader = Pick<URLSearchParams, "get">;

function parsePositiveNumber(value: string | null) {
  if (!value) {
    return null;
  }

  const normalized = value.trim().replace(",", ".");
  if (!normalized || !/^\d+(?:\.\d+)?$/.test(normalized)) {
    return null;
  }

  const parsed = Number(normalized);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

function parseProductSlug(value: string | null) {
  const slug = value?.trim() || "";
  return /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug) && slug.length <= 160 ? slug : null;
}

export function parseDesignServiceSeed(searchParams: SearchParamsReader): DesignServiceSeed | null {
  const product_slug = parseProductSlug(searchParams.get("producto"));
  const width_cm = parsePositiveNumber(searchParams.get("ancho"));
  const height_cm = parsePositiveNumber(searchParams.get("alto"));

  if (!product_slug || width_cm === null || height_cm === null) {
    return null;
  }

  return { product_slug, width_cm, height_cm };
}

export function buildDesignServiceSeedHref(seed: DesignServiceSeed) {
  const product_slug = parseProductSlug(seed.product_slug);
  const width_cm = parsePositiveNumber(String(seed.width_cm));
  const height_cm = parsePositiveNumber(String(seed.height_cm));
  if (!product_slug || width_cm === null || height_cm === null) {
    return null;
  }

  const query = new URLSearchParams({
    producto: product_slug,
    ancho: String(width_cm),
    alto: String(height_cm)
  });
  return `/diseno-previo?${query.toString()}`;
}

export function buildDesignServiceProductHref(categorySlug: string, seed: DesignServiceSeed) {
  const category = parseProductSlug(categorySlug);
  const productSlug = parseProductSlug(seed.product_slug);
  if (!category || !productSlug) {
    return null;
  }

  return `/${category}/${productSlug}`;
}
