import type { Metadata } from "next";
import {
  absoluteUrl,
  buildMetadata,
  siteConfig,
  trimTextAtWord
} from "@/lib/metadata";

export type BlogArticle = {
  slug: string;
  title: string;
  description: string;
  excerpt: string;
  image: string;
  imageAlt: string;
  readingTime: string;
  topic: string;
};

export const blogArticles: BlogArticle[] = [
  {
    slug: "medir-hueco-rejas-para-ventanas",
    title: "Cómo medir el hueco para rejas para ventanas",
    description:
      "Guía práctica para medir el ancho y el alto del hueco antes de pedir rejas para ventanas a medida, evitando errores de montaje y desajustes en fachada.",
    excerpt:
      "Aprende a medir el hueco real, detectar variaciones entre puntos y dejar el margen necesario para un montaje limpio y seguro.",
    image:
      "https://res.cloudinary.com/dewanllxn/image/upload/v1733562847/rejas-para-ventanas_ttjq3d.avif",
    imageAlt: "Medición del hueco para rejas para ventanas",
    readingTime: "6 min",
    topic: "Medición"
  },
  {
    slug: "instalation-rejas-para-ventanas",
    title: "Instalación de rejas para ventanas sin obra",
    description:
      "Paso a paso para instalar rejas para ventanas sin obra, con herramientas, consejos de nivelación y recomendaciones para un acabado firme y duradero.",
    excerpt:
      "Herramientas, orden de montaje y recomendaciones prácticas para colocar una reja sin obra con seguridad y buen acabado.",
    image:
      "https://res.cloudinary.com/dewanllxn/image/upload/v1733562840/rejas-de-seguridad-para-ventanas_buzhg0.avif",
    imageAlt: "Instalación de rejas para ventanas sin obra",
    readingTime: "7 min",
    topic: "Instalación"
  },
  {
    slug: "rejas-para-ventanas-sin-obra",
    title: "Rejas para ventanas sin obra",
    description:
      "Descubre cómo funcionan las rejas para ventanas sin obra, cuándo conviene elegirlas y qué ventajas ofrecen frente a una instalación tradicional con albañilería.",
    excerpt:
      "Una guía clara para entender el sistema sin obra, sus ventajas, el tipo de fijación y los casos donde resulta más cómodo y limpio.",
    image:
      "https://res.cloudinary.com/dewanllxn/image/upload/v1760282424/rejas-para-ventanas-sin-obra_s8mzho.avif",
    imageAlt: "Rejas para ventanas sin obra",
    readingTime: "5 min",
    topic: "Sin obra"
  },
  {
    slug: "rejas-para-ventanas-modernas",
    title: "Rejas para ventanas modernas",
    description:
      "Ideas y criterios para elegir rejas para ventanas modernas con diseño actual, perfiles limpios y fabricación a medida sin renunciar a seguridad y durabilidad.",
    excerpt:
      "Repasa los diseños más buscados, acabados disponibles y ejemplos de rejas modernas adaptadas a vivienda actual.",
    image:
      "https://res.cloudinary.com/dewanllxn/image/upload/v1760282425/rejas-para-ventanas-modernas_rdp46a.avif",
    imageAlt: "Rejas para ventanas modernas",
    readingTime: "5 min",
    topic: "Diseño"
  }
];

export function getBlogArticle(slug: string) {
  return blogArticles.find((article) => article.slug === slug) || null;
}

export function buildBlogArticleMetadata(article: BlogArticle): Metadata {
  return buildMetadata({
    title: article.title,
    description: trimTextAtWord(article.description, 155),
    path: `/${article.slug}`,
    image: article.image
  });
}

export function buildBlogIndexMetadata(): Metadata {
  return buildMetadata({
    title: "Blog de rejas para ventanas y guías prácticas",
    description: trimTextAtWord(
      "Guías prácticas sobre rejas para ventanas, medición del hueco, instalación sin obra y modelos modernos fabricados a medida por MetalWolft.",
      155
    ),
    path: "/blogs",
    image: blogArticles[0]?.image || siteConfig.defaultOgImage
  });
}

export function buildBlogArticleJsonLd(article: BlogArticle) {
  const articleUrl = absoluteUrl(`/${article.slug}`);

  return {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: article.title,
    description: article.description,
    image: [article.image],
    articleSection: article.topic,
    mainEntityOfPage: articleUrl,
    url: articleUrl,
    author: {
      "@type": "Organization",
      name: siteConfig.name
    },
    publisher: {
      "@type": "Organization",
      name: siteConfig.name,
      logo: {
        "@type": "ImageObject",
        url: siteConfig.defaultOgImage
      }
    }
  };
}

export function buildBlogIndexJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "Blog",
    name: "Blog MetalWolft",
    url: absoluteUrl("/blogs"),
    description:
      "Guías prácticas sobre rejas para ventanas, instalación sin obra, medición del hueco y diseños modernos.",
    blogPost: blogArticles.map((article) => ({
      "@type": "BlogPosting",
      headline: article.title,
      url: absoluteUrl(`/${article.slug}`),
      image: article.image,
      description: article.description
    }))
  };
}

export function buildBlogItemListJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "ItemList",
    name: "Guías sobre rejas para ventanas",
    itemListElement: blogArticles.map((article, index) => ({
      "@type": "ListItem",
      position: index + 1,
      url: absoluteUrl(`/${article.slug}`),
      name: article.title
    }))
  };
}
