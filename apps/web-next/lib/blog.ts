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
  metadataTitle?: string;
  description: string;
  metadataDescription?: string;
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
    title: "Guía de instalación y manipulación de rejas para ventanas",
    metadataTitle: "Guía de instalación y manipulación de rejas para ventanas | MetalWolft",
    description:
      "Guía práctica para desembalar, manipular e instalar una reja para ventana: comprobaciones previas, anclajes, tornillería, fijación y revisión final.",
    metadataDescription:
      "Guía práctica para desembalar, manipular e instalar una reja para ventana: comprobaciones previas, anclajes, tornillería, fijación y revisión final.",
    excerpt:
      "Comprueba, desembala y coloca tu reja con un orden claro para cuidar el acabado y revisar cada punto de fijación.",
    image:
      "https://res.cloudinary.com/dewanllxn/image/upload/v1733562840/rejas-de-seguridad-para-ventanas_buzhg0.avif",
    imageAlt: "Instalación y manipulación de una reja para ventana",
    readingTime: "10 min",
    topic: "Instalación"
  },
  {
    slug: "mantenimiento-retoque-rejas-metalicas",
    title: "Mantenimiento y retoque del acabado de rejas metálicas",
    metadataTitle: "Mantenimiento y retoque de rejas metálicas | MetalWolft",
    description:
      "Cómo limpiar, revisar y retocar pequeños roces, desconchados o puntos localizados de corrosión en rejas metálicas con acabado de esmalte sintético antioxidante.",
    metadataDescription:
      "Cómo limpiar, revisar y retocar pequeños roces, desconchados o puntos localizados de corrosión en rejas metálicas con acabado de esmalte sintético antioxidante.",
    excerpt:
      "Limpieza cotidiana, revisión visual y retoque localizado del acabado cuando el daño es pequeño y posterior a la instalación.",
    image:
      "https://res.cloudinary.com/dewanllxn/image/upload/v1733562840/rejas-de-seguridad-para-ventanas_buzhg0.avif",
    imageAlt: "Reja metálica para ventana con acabado protector",
    readingTime: "8 min",
    topic: "Mantenimiento"
  },
  {
    slug: "plazos-entrega-rejas-a-medida",
    title: "¿Cuánto tardan las rejas a medida?",
    metadataTitle: "¿Cuánto tardan las rejas a medida? | Plazos de fabricación y entrega",
    description:
      "Consulta cómo funciona nuestra previsión de entrega para rejas a medida y qué debes tener en cuenta antes de realizar tu pedido.",
    metadataDescription:
      "Consulta la previsión actual de entrega de nuestras rejas a medida y descubre cómo interpretarla antes de realizar tu pedido.",
    excerpt:
      "Entiende qué representa el intervalo orientativo de entrega y qué conviene revisar antes de confirmar tu pedido.",
    image:
      "https://res.cloudinary.com/dewanllxn/image/upload/v1753776840/plazos-de-entrega-rejas-para-ventanas_v48rm7.avif",
    imageAlt: "Plazos de entrega de rejas para ventanas a medida",
    readingTime: "4 min",
    topic: "Entrega"
  },
  {
    slug: "recepcion-pedidos-revisar-antes-firmar",
    title: "Recepción de pedidos: qué revisar antes de firmar",
    metadataTitle: "Recepción de pedidos: qué revisar antes de firmar | MetalWolft",
    description:
      "Al recibir una reja a medida conviene revisar el estado exterior del envío antes de dar la entrega por correcta. Una comprobación rápida puede facilitar mucho la gestión si el paquete ha sufrido algún daño durante el transporte.",
    metadataDescription:
      "Qué revisar al recibir una reja a medida y cómo actuar si detectas daños en el transporte. Fotografías, embalaje y pasos para comunicar una incidencia.",
    excerpt:
      "Una guía práctica para comprobar el embalaje, documentar posibles daños y comunicar una incidencia dentro del plazo vigente.",
    image:
      "https://res.cloudinary.com/dewanllxn/image/upload/v1757832270/recepcion-pedidos-revisar-antes-firmar-open_yu5oqv.avif",
    imageAlt: "Recepción de pedidos y revisión de daños",
    readingTime: "4 min",
    topic: "Entrega"
  },
  {
    slug: "donde-comprar-rejas-leroy-ikea",
    title: "¿Dónde comprar rejas para ventanas? Soluciones estándar y a medida",
    metadataTitle: "¿Dónde comprar rejas para ventanas? | MetalWolft",
    description:
      "Cuando buscas dónde comprar rejas para ventanas es habitual consultar grandes superficies, tiendas especializadas y fabricantes a medida. No existe una opción adecuada para todos los casos: la elección depende principalmente de las medidas del hueco, el tipo de instalación, el acabado que buscas y el grado de personalización que necesitas.",
    metadataDescription:
      "Qué debes comparar al comprar rejas para ventanas: medidas, anclaje, acabado y diferencias entre soluciones estándar y fabricación a medida.",
    excerpt:
      "Compara medidas, anclajes, acabados y alcance de cada solución antes de elegir entre una reja estándar o fabricada a medida.",
    image:
      "https://res.cloudinary.com/dewanllxn/image/upload/v1760079525/donde-comprar-rejas-leroy-ikea_rsquhp.avif",
    imageAlt: "¿Dónde comprar rejas para ventanas? Ikea, Leroy Merlin o a medida",
    readingTime: "6 min",
    topic: "Compra"
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
    title: article.metadataTitle || article.title,
    description: trimTextAtWord(article.metadataDescription || article.description, 155),
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
