import type { Metadata } from "next";

export const siteConfig = {
  name: "MetalWolft",
  siteUrl: process.env.NEXT_PUBLIC_SITE_URL || "https://www.metalwolft.com",
  defaultTitle: "Rejas para ventanas a medida | MetalWolft",
  defaultDescription:
    "Fabricamos rejas para ventanas a medida, con enfoque en seguridad, instalacion sin obra y envio directo desde fabrica.",
  defaultOgImage:
    "https://res.cloudinary.com/dewanllxn/image/upload/v1749024437/rejas-para-ventanas_nzmi8k.png"
};

export function absoluteUrl(path = "/") {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return new URL(normalizedPath, siteConfig.siteUrl).toString();
}

export function trimTextAtWord(value: string, maxLength: number) {
  const normalized = value.replace(/\s+/g, " ").trim();

  if (normalized.length <= maxLength) {
    return /[.!?]$/.test(normalized) ? normalized : `${normalized}.`;
  }

  const sliced = normalized.slice(0, maxLength + 1);
  const lastSpace = sliced.lastIndexOf(" ");
  const safeLength = lastSpace > Math.floor(maxLength * 0.6) ? lastSpace : maxLength;

  return `${sliced.slice(0, safeLength).trim()}.`;
}

type MetadataInput = {
  title: string;
  description: string;
  path: string;
  image?: string;
};

export function buildMetadata({
  title,
  description,
  path,
  image = siteConfig.defaultOgImage
}: MetadataInput): Metadata {
  const url = absoluteUrl(path);
  const normalizedTitle = title.trim();
  const metadataTitle = normalizedTitle.includes(siteConfig.name)
    ? { absolute: normalizedTitle }
    : normalizedTitle;

  return {
    title: metadataTitle,
    description,
    alternates: {
      canonical: url
    },
    openGraph: {
      type: "website",
      url,
      title: normalizedTitle,
      description,
      siteName: siteConfig.name,
      locale: "es_ES",
      images: [
        {
          url: image,
          alt: normalizedTitle
        }
      ]
    },
    twitter: {
      card: "summary_large_image",
      title: normalizedTitle,
      description,
      images: [image]
    }
  };
}
