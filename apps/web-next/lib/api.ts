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
