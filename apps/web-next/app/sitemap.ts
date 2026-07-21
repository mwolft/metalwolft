import type { MetadataRoute } from "next";
import { fetchCategories, fetchSitemapProducts } from "@/lib/api";
import { absoluteUrl } from "@/lib/metadata";

type SitemapEntry = MetadataRoute.Sitemap[number];

const STATIC_ROUTES = [
  { path: "/", changeFrequency: "weekly", priority: 1 },
  { path: "/rejas-para-ventanas", changeFrequency: "weekly", priority: 0.95 },
  { path: "/contact", changeFrequency: "monthly", priority: 0.75 },
  { path: "/blogs", changeFrequency: "weekly", priority: 0.85 },
  { path: "/medir-hueco-rejas-para-ventanas", changeFrequency: "monthly", priority: 0.75 },
  { path: "/instalation-rejas-para-ventanas", changeFrequency: "monthly", priority: 0.75 },
  { path: "/rejas-para-ventanas-sin-obra", changeFrequency: "monthly", priority: 0.8 },
  { path: "/rejas-para-ventanas-modernas", changeFrequency: "monthly", priority: 0.8 },
  { path: "/politica-privacidad", changeFrequency: "yearly", priority: 0.35 },
  { path: "/politica-cookies", changeFrequency: "yearly", priority: 0.35 },
  { path: "/politica-devolucion", changeFrequency: "yearly", priority: 0.4 },
  { path: "/cambios-politica-cookies", changeFrequency: "yearly", priority: 0.3 },
  { path: "/license", changeFrequency: "yearly", priority: 0.25 }
] as const;

function createEntry(
  path: string,
  lastModified: Date,
  changeFrequency: SitemapEntry["changeFrequency"],
  priority: number
): SitemapEntry {
  return {
    url: absoluteUrl(path),
    lastModified,
    changeFrequency,
    priority
  };
}

function buildStaticEntries(lastModified: Date) {
  return STATIC_ROUTES.map((route) =>
    createEntry(route.path, lastModified, route.changeFrequency, route.priority)
  );
}

function dedupeEntries(entries: SitemapEntry[]) {
  const byUrl = new Map<string, SitemapEntry>();

  for (const entry of entries) {
    if (!byUrl.has(entry.url)) {
      byUrl.set(entry.url, entry);
    }
  }

  return Array.from(byUrl.values());
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const lastModified = new Date();
  const staticEntries = buildStaticEntries(lastModified);

  try {
    const categories = await fetchCategories();
    const sitemapProducts = await fetchSitemapProducts().catch(() => []);
    const categoryEntries = categories
      .filter((category) => typeof category.slug === "string" && category.slug.trim().length > 0)
      .map((category) =>
        createEntry(
          `/${category.slug}`,
          lastModified,
          "weekly",
          category.slug === "rejas-para-ventanas" ? 0.95 : 0.8
        )
      );

    const productEntries = sitemapProducts.map((product) =>
      createEntry(
        `/${product.category_slug}/${product.slug}`,
        lastModified,
        "weekly",
        0.7
      )
    );

    return dedupeEntries([...staticEntries, ...categoryEntries, ...productEntries]);
  } catch {
    return staticEntries;
  }
}
