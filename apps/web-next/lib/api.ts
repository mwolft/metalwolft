const DEFAULT_LOCAL_API_URL = "http://localhost:3001";

export function getApiBaseUrl() {
  const envUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
  return (envUrl && envUrl.replace(/\/$/, "")) || DEFAULT_LOCAL_API_URL;
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

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<T>;
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
  categoria_nombre: string;
  subcategoria_id: number | null;
  subcategoria_nombre: string | null;
  imagen: string | null;
  has_abatible: boolean;
  has_door_model: boolean;
  es_mas_vendido: boolean;
  es_nuevo_diseno: boolean;
  images: ApiProductImage[];
};

export async function fetchProductBySlug(categorySlug: string, productSlug: string) {
  return fetchApi<ApiProduct>(`/api/${categorySlug}/${productSlug}`, {
    next: { revalidate: 300 }
  });
}
