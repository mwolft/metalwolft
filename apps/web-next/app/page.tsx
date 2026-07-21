import Image from "next/image";
import Link from "next/link";
import type { Metadata } from "next";
import { PageContainer } from "@/components/layout/PageContainer";
import { JsonLd } from "@/components/seo/JsonLd";
import { contactDetails, contactLinks } from "@/lib/contact";
import {
  ApiRequestError,
  ApiProduct,
  fetchCategories,
  fetchCategoryProducts
} from "@/lib/api";
import { absoluteUrl, buildMetadata, siteConfig, trimTextAtWord } from "@/lib/metadata";

type HomeFeaturedProduct = {
  id: string;
  href: string;
  title: string;
  description: string;
  image: string | null;
  badge: string;
};

type HomeData = {
  categoryDescription: string | null;
  featuredProducts: HomeFeaturedProduct[];
  catalogUnavailable: boolean;
};

const CATEGORY_SLUG = "rejas-para-ventanas";
const HERO_IMAGE_PATH = "/images/home/rejas-hero.avif";
const CATALOG_LOG_DEDUPLICATION_MS = 60_000;
const lastCatalogLogAt: Partial<Record<"products" | "categories", number>> = {};

const FAQ_ITEMS = [
  {
    question: "¿Cómo sé qué medida de reja necesito?",
    answer:
      "La forma más segura es medir el hueco con calma antes de configurar el pedido. En la guía de medición explicamos cómo tomar alto y ancho para evitar errores y elegir el modelo adecuado."
  },
  {
    question: "¿Qué tipos de anclaje puedo elegir?",
    answer:
      "Depende del tipo de hueco, del soporte y de si buscas una instalación más visible o más discreta. En la ficha de cada modelo y en la guía de instalación explicamos qué opción encaja mejor en cada caso."
  },
  {
    question: "¿Se pueden instalar sin obra?",
    answer:
      "Muchos casos admiten una instalación sin obra o con intervención mínima. La clave es medir bien el hueco y escoger el anclaje correcto. MetalWolft fabrica y envía la reja, pero no presta servicio de instalación."
  },
  {
    question: "¿Cuánto tarda la fabricación?",
    answer:
      "Cada reja se fabrica a medida, así que el plazo depende de la carga de taller y del modelo elegido. Mantenemos una guía de plazos para que puedas planificar la compra con una referencia clara."
  },
  {
    question: "¿Dónde enviáis las rejas?",
    answer:
      "Enviamos los pedidos a España peninsular para que puedas comprar online y recibir la reja en la dirección indicada durante el pedido."
  },
  {
    question: "¿Puedo elegir color o acabado?",
    answer:
      "Sí, la fabricación a medida permite adaptar medidas, acabados y otros detalles del pedido. El objetivo es que la reja proteja bien y encaje visualmente con la vivienda."
  }
] as const;

function getConfiguredHomeApiBaseUrl() {
  const apiBaseUrl = process.env.API_URL?.trim() || process.env.NEXT_PUBLIC_API_URL?.trim();
  return apiBaseUrl && apiBaseUrl.length > 0 ? apiBaseUrl : null;
}

function isHomeCatalogUnavailableError(error: unknown) {
  if (error instanceof ApiRequestError || error instanceof TypeError) {
    return true;
  }

  if (error instanceof Error) {
    return /fetch failed|econnrefused|enotfound|connect/i.test(error.message);
  }

  return false;
}

function logHomeCatalogUnavailable(source: "products" | "categories", error: unknown) {
  const now = Date.now();
  if (now - (lastCatalogLogAt[source] || 0) < CATALOG_LOG_DEDUPLICATION_MS) {
    return;
  }
  lastCatalogLogAt[source] = now;

  const details =
    error instanceof ApiRequestError
      ? { source, errorName: error.name, status: error.status }
      : { source, errorName: error instanceof Error ? error.name : "UnknownError" };

  console.error("[HomePage] Catalog data unavailable.", details);
}

function getProductImage(product: Pick<ApiProduct, "imagen">) {
  return product.imagen?.trim() || null;
}

function buildProductExcerpt(product: Pick<ApiProduct, "descripcion" | "descripcion_seo" | "nombre">) {
  const rawDescription =
    product.descripcion_seo?.trim() ||
    product.descripcion?.trim() ||
    `${product.nombre} fabricada a medida por MetalWolft.`;

  return trimTextAtWord(rawDescription, 150);
}

function mapProductToCard(product: ApiProduct): HomeFeaturedProduct {
  return {
    id: String(product.id),
    href: `/${product.category_slug || CATEGORY_SLUG}/${product.slug}`,
    title: product.h1_seo?.trim() || product.nombre,
    description: buildProductExcerpt(product),
    image: getProductImage(product),
    badge: product.es_mas_vendido ? "Más vendido" : "Modelo a medida"
  };
}

function selectFeaturedProducts(products: ApiProduct[]) {
  return [...products]
    .sort((left, right) => {
      const leftScore = Number(Boolean(left.es_mas_vendido)) * 4 + Number(Boolean(left.es_nuevo_diseno)) * 2;
      const rightScore =
        Number(Boolean(right.es_mas_vendido)) * 4 + Number(Boolean(right.es_nuevo_diseno)) * 2;

      return rightScore - leftScore;
    })
    .slice(0, 6)
    .map(mapProductToCard);
}

async function getHomeData(): Promise<HomeData> {
  if (process.env.NODE_ENV === "production" && !getConfiguredHomeApiBaseUrl()) {
    throw new Error("HomePage requires API_URL or NEXT_PUBLIC_API_URL in production.");
  }

  const [productsResult, categoriesResult] = await Promise.allSettled([
    fetchCategoryProducts(CATEGORY_SLUG),
    fetchCategories()
  ]);

  if (productsResult.status === "rejected") {
    if (isHomeCatalogUnavailableError(productsResult.reason)) {
      logHomeCatalogUnavailable("products", productsResult.reason);
      return {
        categoryDescription: null,
        featuredProducts: [],
        catalogUnavailable: true
      };
    }

    throw productsResult.reason;
  }

  if (
    categoriesResult.status === "rejected" &&
    !isHomeCatalogUnavailableError(categoriesResult.reason)
  ) {
    throw categoriesResult.reason;
  }

  if (categoriesResult.status === "rejected") {
    logHomeCatalogUnavailable("categories", categoriesResult.reason);
  }

  const categories = categoriesResult.status === "fulfilled" ? categoriesResult.value : [];
  const category = categories.find((item) => item.slug === CATEGORY_SLUG) || null;

  return {
    categoryDescription: category?.descripcion?.trim() || null,
    featuredProducts: selectFeaturedProducts(productsResult.value),
    catalogUnavailable: false
  };
}

function buildMetaDescription(featuredCount: number) {
  const description =
    featuredCount > 0
      ? `Rejas para ventanas a medida fabricadas por MetalWolft. Descubre ${featuredCount} modelos reales, aprende a medir el hueco y compra online con envío a España peninsular.`
      : "Rejas para ventanas a medida fabricadas por MetalWolft. Compra online con envío a España peninsular y organiza la instalación por tu cuenta o con un profesional.";

  return trimTextAtWord(description, 155);
}

function buildOrganizationJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: siteConfig.name,
    url: siteConfig.siteUrl,
    logo: siteConfig.defaultOgImage,
    contactPoint: {
      "@type": "ContactPoint",
      telephone: contactDetails.phoneDisplay,
      contactType: "customer support",
      areaServed: contactDetails.supportArea,
      availableLanguage: "es"
    }
  };
}

function buildWebPageJsonLd(description: string) {
  return {
    "@context": "https://schema.org",
    "@type": "WebPage",
    name: "Rejas para ventanas a medida",
    url: absoluteUrl("/"),
    description,
    primaryImageOfPage: absoluteUrl(HERO_IMAGE_PATH),
    isPartOf: {
      "@type": "WebSite",
      name: siteConfig.name,
      url: siteConfig.siteUrl
    }
  };
}

function buildItemListJsonLd(products: HomeFeaturedProduct[]) {
  return {
    "@context": "https://schema.org",
    "@type": "ItemList",
    name: "Modelos destacados de rejas para ventanas",
    itemListElement: products.map((product, index) => ({
      "@type": "ListItem",
      position: index + 1,
      url: absoluteUrl(product.href),
      name: product.title
    }))
  };
}

function buildFaqJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: FAQ_ITEMS.map((item) => ({
      "@type": "Question",
      name: item.question,
      acceptedAnswer: {
        "@type": "Answer",
        text: item.answer
      }
    }))
  };
}

export async function generateMetadata(): Promise<Metadata> {
  const data = await getHomeData();
  const description = buildMetaDescription(data.featuredProducts.length);

  return buildMetadata({
    title: "Rejas para ventanas a medida | MetalWolft",
    description,
    path: "/",
    image: absoluteUrl(HERO_IMAGE_PATH)
  });
}

export default async function HomePage() {
  const data = await getHomeData();
  const description = buildMetaDescription(data.featuredProducts.length);
  const categoryIntro =
    data.categoryDescription ||
    "Especialistas en rejas para ventanas a medida, pensadas para proteger la vivienda con una instalación clara, acabados cuidados y atención directa antes de comprar.";

  return (
    <div className="mw-page mw-home-page">
      <PageContainer>
        <JsonLd data={buildOrganizationJsonLd()} />
        <JsonLd data={buildWebPageJsonLd(description)} />
        <JsonLd data={buildItemListJsonLd(data.featuredProducts)} />
        <JsonLd data={buildFaqJsonLd()} />

        <section className="mw-home-hero">
          <div className="mw-home-hero__copy">
            <p className="mw-eyebrow">Especialistas en rejas para ventanas</p>
            <h1 className="mw-title">Rejas para ventanas a medida</h1>
            <p className="mw-lead">
              Fabricamos rejas para ventanas a medida para que puedas elegir un modelo, configurar
              medidas, acabado y anclaje, y comprar directamente online. Enviamos a España
              peninsular; el servicio no incluye la instalación.
            </p>
            <div className="mw-actions">
              <Link className="mw-button mw-button--primary" href="/rejas-para-ventanas">
                Ver catálogo de rejas
              </Link>
              <Link
                className="mw-button mw-button--secondary"
                href="/medir-hueco-rejas-para-ventanas"
              >
                Cómo medir tu ventana
              </Link>
            </div>
            <ul className="mw-home-hero__points">
              <li>Modelos fabricados a medida para el hueco real de tu ventana.</li>
              <li>Guías prácticas para medir y elegir el anclaje antes de comprar.</li>
              <li>Atención directa por WhatsApp si necesitas ayuda antes de comprar.</li>
            </ul>
          </div>

          <div className="mw-home-hero__media">
            <div className="mw-home-hero__image">
              <Image
                src={HERO_IMAGE_PATH}
                alt="Reja para ventana fabricada a medida por MetalWolft"
                width={1280}
                height={960}
                priority
                sizes="(max-width: 1024px) 100vw, 42vw"
                unoptimized={HERO_IMAGE_PATH.split(/[?#]/)[0].toLowerCase().endsWith(".avif")}
              />
            </div>
            <div className="mw-home-hero__route">
              <p className="mw-note">Compra más fácil</p>
              <h2>Tu ruta más directa para acertar</h2>
              <ol className="mw-steps">
                <li>Elige el modelo que mejor encaja con tu ventana.</li>
                <li>Mide alto y ancho con la guía paso a paso.</li>
                <li>Configura medidas, anclaje y acabado.</li>
                <li>Recibe la reja en España peninsular y organiza su instalación.</li>
              </ol>
            </div>
          </div>
        </section>

        <section className="mw-home-trust" aria-label="Puntos de confianza">
          <article className="mw-home-trust__item">
            <strong>Fabricación a medida</strong>
            <span>Cada reja se fabrica según el hueco real de tu ventana.</span>
          </article>
          <article className="mw-home-trust__item">
            <strong>Envío peninsular</strong>
            <span>Entregamos los pedidos online en España peninsular.</span>
          </article>
          <article className="mw-home-trust__item">
            <strong>Ayuda por WhatsApp</strong>
            <span>Resolvemos dudas antes de elegir modelo, medidas o anclaje.</span>
          </article>
          <article className="mw-home-trust__item">
            <strong>Sin instalación incluida</strong>
            <span>Fabricamos y enviamos la reja; tú organizas su instalación.</span>
          </article>
        </section>

        <section className="mw-section" id="modelos-destacados">
          <p className="mw-eyebrow">Modelos destacados</p>
          <h2>Modelos reales de rejas para ventanas</h2>
          <p>
            {categoryIntro} Hemos seleccionado varios modelos reales para que puedas pasar del
            vistazo general a la ficha del producto con un solo clic.
          </p>
          {data.featuredProducts.length === 0 ? (
            <div className="mw-home-empty">
              <p role={data.catalogUnavailable ? "status" : undefined}>
                {data.catalogUnavailable
                  ? "No hemos podido cargar los modelos en este momento. Puedes seguir consultando las guías mientras se restablece el catálogo."
                  : "Ahora mismo no hay modelos destacados disponibles en esta portada."}
              </p>
              <div className="mw-actions">
                <Link
                  className="mw-button mw-button--primary"
                  href="/medir-hueco-rejas-para-ventanas"
                >
                  Consultar la guía de medición
                </Link>
              </div>
            </div>
          ) : (
            <div className="mw-home-product-grid">
              {data.featuredProducts.map((product) => (
                <article className="mw-home-product-card" key={product.id}>
                  <div className="mw-home-product-card__media">
                    {product.image ? (
                      <Image
                        src={product.image}
                        alt={product.title}
                        fill
                        sizes="(max-width: 767px) 100vw, (max-width: 1120px) 50vw, 33vw"
                        unoptimized={product.image.split(/[?#]/)[0].toLowerCase().endsWith(".avif")}
                      />
                    ) : (
                      <div className="mw-home-product-card__placeholder" aria-hidden="true">
                        <span>{product.badge}</span>
                      </div>
                    )}
                  </div>
                  <div className="mw-home-product-card__body">
                    <span className="mw-home-product-card__badge">{product.badge}</span>
                    <h3>{product.title}</h3>
                    <p>{product.description}</p>
                    <div className="mw-actions">
                      <Link className="mw-button mw-button--primary" href={product.href}>
                        {`Ver modelo ${product.title}`}
                      </Link>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="mw-section">
          <p className="mw-eyebrow">Cómo funciona</p>
          <h2>Comprar una reja a medida es más fácil cuando sigues el orden correcto</h2>
          <div className="mw-home-feature-grid">
            <article className="mw-home-feature-card">
              <span className="mw-home-feature-card__number">1</span>
              <h3>Elige el modelo</h3>
              <p>Compara diseños reales para decidir qué tipo de reja encaja mejor con tu vivienda.</p>
            </article>
            <article className="mw-home-feature-card">
              <span className="mw-home-feature-card__number">2</span>
              <h3>Mide el hueco</h3>
              <p>Toma alto y ancho con la guía adecuada para evitar errores antes de configurar.</p>
            </article>
            <article className="mw-home-feature-card">
              <span className="mw-home-feature-card__number">3</span>
              <h3>Configura medidas y acabado</h3>
              <p>Define anclaje, medidas y acabados para adaptar la reja a tu caso real.</p>
            </article>
            <article className="mw-home-feature-card">
              <span className="mw-home-feature-card__number">4</span>
              <h3>Recíbela en casa</h3>
              <p>Fabricamos el pedido y lo enviamos a España peninsular para que organices la instalación.</p>
            </article>
          </div>
        </section>

        <section className="mw-section">
          <p className="mw-eyebrow">Beneficios</p>
          <h2>Por qué elegir rejas para ventanas a medida</h2>
          <div className="mw-home-feature-grid">
            <article className="mw-home-benefit-card">
              <h3>Seguridad</h3>
              <p>Una reja bien fabricada aporta protección adicional y tranquilidad en el día a día.</p>
            </article>
            <article className="mw-home-benefit-card">
              <h3>Estética</h3>
              <p>El modelo, el acabado y las proporciones importan para que la ventana siga viéndose cuidada.</p>
            </article>
            <article className="mw-home-benefit-card">
              <h3>Fabricación a medida</h3>
              <p>No trabajamos con medidas genéricas: el pedido se ajusta al hueco real de tu vivienda.</p>
            </article>
            <article className="mw-home-benefit-card">
              <h3>Opciones de anclaje</h3>
              <p>Elige el tipo de fijación según el hueco y el soporte donde vas a instalar la reja.</p>
            </article>
          </div>
        </section>

        <section className="mw-section">
          <p className="mw-eyebrow">Guías útiles</p>
          <h2>Guías para medir, instalar y decidir mejor</h2>
          <div className="mw-home-guide-grid">
            <article className="mw-home-guide-card">
              <h3>Medir el hueco correctamente</h3>
              <p>Aprende a tomar las medidas con el criterio adecuado antes de configurar el pedido.</p>
              <Link className="mw-inline-link" href="/medir-hueco-rejas-para-ventanas">
                Ir a la guía de medición
              </Link>
            </article>
            <article className="mw-home-guide-card">
              <h3>Instalación y anclajes</h3>
              <p>Revisa qué anclaje puede encajar mejor. La guía es orientativa y MetalWolft no realiza la instalación.</p>
              <Link className="mw-inline-link" href="/instalation-rejas-para-ventanas">
                Ver guía de instalación
              </Link>
            </article>
            <article className="mw-home-guide-card">
              <h3>Rejas para ventanas sin obra</h3>
              <p>Consulta ideas y casos en los que una instalación limpia puede ser la mejor alternativa.</p>
              <Link className="mw-inline-link" href="/rejas-para-ventanas-sin-obra">
                Leer sobre rejas sin obra
              </Link>
            </article>
          </div>
        </section>

        <section className="mw-section mw-home-workshop">
          <div className="mw-home-workshop__copy">
            <p className="mw-eyebrow">Taller y confianza</p>
            <h2>Fabricación propia y atención directa</h2>
            <p>
              Fabricamos rejas para ventanas a medida en España y trabajamos cada pedido con una
              lógica sencilla: entender bien el hueco, proponer un modelo coherente y mantener una
              atención directa cuando el cliente necesita ayuda antes de comprar.
            </p>
            <p>
              No intentamos vender una solución genérica. La prioridad es que la reja encaje, se
              vea bien y llegue con información útil para que organices su instalación con criterio.
            </p>
          </div>
          <aside className="mw-home-workshop__panel" aria-label="Compromisos de taller">
            <p className="mw-note">Qué cuidamos</p>
            <ul className="mw-list">
              <li>Medidas ajustadas al hueco real.</li>
              <li>Orientación clara sobre instalación y anclaje.</li>
              <li>Acabados pensados para vivienda.</li>
              <li>Atención directa antes y después de configurar el pedido.</li>
            </ul>
          </aside>
        </section>

        <section className="mw-section" id="faq">
          <p className="mw-eyebrow">Preguntas frecuentes</p>
          <h2>Dudas habituales antes de pedir una reja para ventana</h2>
          <div className="mw-home-faq-list">
            {FAQ_ITEMS.map((item) => (
              <details className="mw-home-faq-item" key={item.question}>
                <summary>{item.question}</summary>
                <p>{item.answer}</p>
              </details>
            ))}
          </div>
        </section>

        <section className="mw-home-final-cta">
          <div className="mw-home-final-cta__box">
            <p className="mw-eyebrow">Siguiente paso</p>
            <h2>Explora el catálogo o consúltanos antes de comprar</h2>
            <p>
              Si ya tienes clara la idea, entra en el catálogo principal. Si todavía dudas con la
              medición, el acabado o el anclaje, puedes escribirnos y te ayudamos a encaminar
              el pedido.
            </p>
            <div className="mw-actions">
              <Link className="mw-button mw-button--primary" href="/rejas-para-ventanas">
                Ver catálogo de rejas
              </Link>
              <a className="mw-button mw-button--secondary" href={contactLinks.whatsapp}>
                Hablar por WhatsApp
              </a>
              <Link className="mw-button mw-button--secondary" href="/contact">
                Ir a contacto
              </Link>
            </div>
          </div>
        </section>
      </PageContainer>
    </div>
  );
}
