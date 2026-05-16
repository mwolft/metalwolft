import type { MetadataRoute } from "next";
import { absoluteUrl } from "@/lib/metadata";

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: absoluteUrl("/"),
      lastModified: new Date("2026-05-16"),
      changeFrequency: "weekly",
      priority: 1
    },
    {
      url: absoluteUrl("/rejas-para-ventanas"),
      lastModified: new Date("2026-05-16"),
      changeFrequency: "weekly",
      priority: 0.9
    }
  ];
}
