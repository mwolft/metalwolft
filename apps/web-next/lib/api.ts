const DEFAULT_LOCAL_API_URL = "http://127.0.0.1:3001";

export class ApiRequestError extends Error {
  status: number;
  url: string;
  body: string;

  constructor(message: string, options: { status?: number; url: string; body?: string }) {
    super(message);
    this.name = "ApiRequestError";
    this.status = options.status ?? 0;
    this.url = options.url;
    this.body = options.body ?? "";
  }
}

export function getApiBaseUrl() {
  const candidates = [
    process.env.API_URL,
    process.env.NEXT_PUBLIC_API_URL,
    process.env.REACT_APP_BACKEND_URL,
    DEFAULT_LOCAL_API_URL
  ];

  const resolved = candidates.find((value) => typeof value === "string" && value.trim().length > 0);
  return resolved!.trim().replace(/\/$/, "");
}

export async function fetchApi<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${getApiBaseUrl()}${path.startsWith("/") ? path : `/${path}`}`;
  const response = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {})
    }
  });

  const rawBody = await response.text();

  if (!response.ok) {
    throw new ApiRequestError(`API request failed: ${response.status} ${response.statusText}`, {
      status: response.status,
      url,
      body: rawBody
    });
  }

  if (!rawBody) {
    throw new ApiRequestError("API request returned an empty body", {
      status: response.status,
      url
    });
  }

  try {
    return JSON.parse(rawBody) as T;
  } catch {
    throw new ApiRequestError("API response is not valid JSON", {
      status: response.status,
      url,
      body: rawBody
    });
  }
}

export type ApiProductImage = {
  id: number;
  product_id: number;
  image_url: string;
};

export type ApiProduct = {
  id: number;
  slug: string;
  nombre: string;
  descripcion: string;
  descripcion_seo: string | null;
  titulo_seo: string | null;
  h1_seo: string | null;
  precio: number;
  precio_rebajado: number | null;
  porcentaje_rebaja: number | null;
  categoria_id: number;
  category_slug: string;
  categoria_nombre?: string;
  subcategoria_id: number | null;
  subcategoria_nombre?: string | null;
  imagen: string | null;
  has_abatible: boolean;
  has_door_model: boolean;
  es_mas_vendido: boolean;
  es_nuevo_diseno: boolean;
  available_for_sale: boolean;
  images?: ApiProductImage[];
};

export type ApiCategory = {
  id: number;
  nombre: string;
  descripcion: string | null;
  parent_id: number | null;
  image_url: string | null;
  slug: string;
  product_count?: number;
  subcategories?: Array<{
    id: number;
    nombre: string;
    descripcion: string | null;
    categoria_id: number;
    product_count?: number;
  }>;
};

export type ApiSitemapProduct = {
  category_slug: string;
  slug: string;
};

function pickFirstEntity<T extends Record<string, unknown>>(payload: T | T[] | { results?: T | T[] }) {
  if (Array.isArray(payload)) {
    return payload[0] ?? null;
  }

  if (payload && typeof payload === "object" && "results" in payload) {
    const { results } = payload;
    if (Array.isArray(results)) {
      return results[0] ?? null;
    }

    return results ?? null;
  }

  return payload ?? null;
}

function pickEntityList<T>(payload: T[] | { results?: T[] } | T) {
  if (Array.isArray(payload)) {
    return payload;
  }

  if (payload && typeof payload === "object" && "results" in payload) {
    const { results } = payload as { results?: T[] };
    return Array.isArray(results) ? results : [];
  }

  return [];
}

export async function fetchProductBySlug(categorySlug: string, productSlug: string) {
  const payload = await fetchApi<ApiProduct | { results?: ApiProduct | ApiProduct[] } | ApiProduct[]>(
    `/api/${categorySlug}/${productSlug}`,
    {
    next: { revalidate: 300 }
    }
  );

  const product = pickFirstEntity<ApiProduct>(payload);
  if (product && "slug" in product) {
    return product;
  }

  throw new ApiRequestError("API response did not match the expected product shape", {
    url: `${getApiBaseUrl()}/api/${categorySlug}/${productSlug}`,
    body: JSON.stringify(payload)
  });
}

export async function fetchCategories() {
  const payload = await fetchApi<ApiCategory[] | { results?: ApiCategory[] }>(`/api/categories`, {
    next: { revalidate: 300 }
  });

  return pickEntityList<ApiCategory>(payload);
}

export async function fetchCategoryProducts(categorySlug: string) {
  const payload = await fetchApi<ApiProduct[] | { results?: ApiProduct[] }>(
    `/api/category/${categorySlug}/products`,
    {
      next: { revalidate: 300 }
    }
  );

  return pickEntityList<ApiProduct>(payload);
}

export async function fetchSitemapProducts() {
  const payload = await fetchApi<ApiSitemapProduct[] | { results?: ApiSitemapProduct[] }>(
    "/api/sitemap/products",
    {
      next: { revalidate: 300 }
    }
  );

  return pickEntityList<ApiSitemapProduct>(payload);
}
