import type { Metadata } from "next";

export const siteConfig = {
  name: "MetalWolft",
  siteUrl: process.env.NEXT_PUBLIC_SITE_URL || "https://www.metalwolft.com",
  defaultTitle: "Rejas para ventanas a medida | MetalWolft",
  defaultDescription:
    "Fabricamos rejas para ventanas a medida, con enfoque en seguridad, instalación sin obra y envío directo de fábrica.",
  defaultOgImage:
    "https://res.cloudinary.com/dewanllxn/image/upload/v1749024437/rejas-para-ventanas_nzmi8k.png"
};

export function absoluteUrl(path = "/") {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return new URL(normalizedPath, siteConfig.siteUrl).toString();
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
