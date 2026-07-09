import type { MetadataRoute } from "next";
import { fetchCategories, fetchCategoryProducts } from "@/lib/api";
import { absoluteUrl } from "@/lib/metadata";

type SitemapEntry = MetadataRoute.Sitemap[number];

const STATIC_ROUTES = [
  { path: "/", changeFrequency: "weekly", priority: 1 },
  { path: "/rejas-para-ventanas", changeFrequency: "weekly", priority: 0.95 },
  { path: "/blogs", changeFrequency: "weekly", priority: 0.85 },
  { path: "/medir-hueco-rejas-para-ventanas", changeFrequency: "monthly", priority: 0.75 },
  { path: "/instalation-rejas-para-ventanas", changeFrequency: "monthly", priority: 0.75 },
  { path: "/rejas-para-ventanas-sin-obra", changeFrequency: "monthly", priority: 0.8 },
  { path: "/rejas-para-ventanas-modernas", changeFrequency: "monthly", priority: 0.8 }
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
    const categoryEntries = categories
      .filter((category) => typeof category.slug === "string" && category.slug.trim().length > 0)
      .map((category) =>
        createEntry(`/${category.slug}`, lastModified, "weekly", category.slug === "rejas-para-ventanas" ? 0.95 : 0.8)
      );

    const productResults = await Promise.allSettled(
      categories
        .filter((category) => typeof category.slug === "string" && category.slug.trim().length > 0)
        .map(async (category) => {
          const products = await fetchCategoryProducts(category.slug);
          return products.map((product) =>
            createEntry(
              `/${product.category_slug || category.slug}/${product.slug}`,
              lastModified,
              "weekly",
              0.7
            )
          );
        })
    );

    const productEntries = productResults.flatMap((result) =>
      result.status === "fulfilled" ? result.value : []
    );

    return dedupeEntries([
      ...staticEntries,
      ...categoryEntries,
      ...productEntries
    ]);
  } catch {
    return staticEntries;
  }
}
