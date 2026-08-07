import type { Metadata } from "next";

export const siteConfig = {
  name: "MetalWolft",
  siteUrl: process.env.NEXT_PUBLIC_SITE_URL || "https://www.metalwolft.com",
  defaultTitle: "Rejas para ventanas a medida | MetalWolft",
  defaultDescription:
    "Fabricamos rejas para ventanas a medida, con enfoque en seguridad, instalación sin obra y envío directo desde fábrica.",
  defaultOgImage:
    "https://res.cloudinary.com/dewanllxn/image/upload/v1749024437/rejas-para-ventanas_nzmi8k.png"
};

export function absoluteUrl(path = "/") {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return new URL(normalizedPath, siteConfig.siteUrl).toString();
}

const WEAK_ENDINGS = new Set([
  "el",
  "la",
  "los",
  "las",
  "un",
  "una",
  "unos",
  "unas",
  "de",
  "del",
  "para",
  "con",
  "sin",
  "por",
  "en",
  "a",
  "que",
  "y",
  "o",
  "renunciar",
  "disfrutar",
  "conseguir",
  "aportar",
  "ofrece",
  "aporta",
  "ofrecer",
  "permite"
]);

function normalizeEndingToken(token: string) {
  return token
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "");
}

function stripTrailingSeparators(text: string) {
  return text.replace(/[,:;/-]+$/g, "").trim();
}

function removeTrailingWeakWords(text: string) {
  let candidate = stripTrailingSeparators(text);

  while (candidate) {
    const words = candidate.split(/\s+/);
    const lastWord = normalizeEndingToken(words[words.length - 1] || "");

    if (!lastWord || !WEAK_ENDINGS.has(lastWord)) {
      break;
    }

    words.pop();
    candidate = stripTrailingSeparators(words.join(" "));
  }

  return candidate;
}

function ensureSentenceEnding(text: string) {
  const cleaned = stripTrailingSeparators(text);

  if (!cleaned) {
    return "";
  }

  return /[.!?]$/.test(cleaned) ? cleaned : `${cleaned}.`;
}

export function trimTextAtWord(value: string, maxLength: number) {
  const normalized = value.replace(/\s+/g, " ").trim();
  const sentenceFloor = Math.floor(maxLength * 0.45);

  if (!normalized) {
    return "";
  }

  if (normalized.length <= maxLength) {
    const cleaned = removeTrailingWeakWords(normalized);
    return ensureSentenceEnding(cleaned || normalized);
  }

  let lastSentenceEnd = -1;
  for (let index = 0; index < Math.min(normalized.length, maxLength); index += 1) {
    if (/[.!?]/.test(normalized[index])) {
      lastSentenceEnd = index;
    }
  }

  if (lastSentenceEnd >= sentenceFloor) {
    const sentenceCandidate = normalized.slice(0, lastSentenceEnd + 1).trim();
    const cleanedSentence = removeTrailingWeakWords(
      sentenceCandidate.replace(/[.!?]+$/g, "").trim()
    );

    if (cleanedSentence) {
      return ensureSentenceEnding(cleanedSentence);
    }
  }

  const sliced = normalized.slice(0, maxLength + 1);
  const lastSpace = sliced.lastIndexOf(" ");
  const safeLength = lastSpace > Math.floor(maxLength * 0.6) ? lastSpace : maxLength;
  const truncated = normalized.slice(0, safeLength).trim();
  const cleaned = removeTrailingWeakWords(truncated);

  if (cleaned) {
    return ensureSentenceEnding(cleaned);
  }

  const fallbackWords = truncated.split(/\s+/);
  while (fallbackWords.length > 3) {
    fallbackWords.pop();
    const fallbackCandidate = removeTrailingWeakWords(fallbackWords.join(" "));
    if (fallbackCandidate) {
      return ensureSentenceEnding(fallbackCandidate);
    }
  }

  return ensureSentenceEnding(normalized.slice(0, maxLength).trim());
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
