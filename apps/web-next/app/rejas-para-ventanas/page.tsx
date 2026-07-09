import Link from "next/link";
import type { Metadata } from "next";
import { PageContainer } from "@/components/layout/PageContainer";
import { BreadcrumbJsonLd } from "@/components/seo/BreadcrumbJsonLd";
import { JsonLd } from "@/components/seo/JsonLd";
import {
  absoluteUrl,
  buildMetadata,
  siteConfig,
  trimTextAtWord
} from "@/lib/metadata";
import {
  ApiProduct,
  fetchCategories,
  fetchCategoryProducts,
  getApiBaseUrl
} from "@/lib/api";

type RejasCategoryData = {
  categoryName: string;
  categoryDescription: string | null;
  products: ApiProduct[];
};

const CATEGORY_SLUG = "rejas-para-ventanas";

function shouldAllowLocalApiFallback() {
  const apiBaseUrl = getApiBaseUrl().toLowerCase();

  return (
    apiBaseUrl.includes("localhost") ||
    apiBaseUrl.includes("127.0.0.1") ||
    apiBaseUrl.includes(".app.github.dev") ||
    apiBaseUrl.includes(".gitpod.io")
  );
}

function isApiUnavailableError(error: unknown) {
  if (error instanceof TypeError) {
    return true;
  }

  if (error instanceof Error) {
    return /fetch failed|econnrefused|enotfound|connect/i.test(error.message);
  }

  return false;
}

function buildIntroText(productCount: number, categoryDescription?: string | null) {
  const baseText =
    categoryDescription?.trim() ||
    "Fabricamos rejas para ventanas a medida con enfoque en seguridad, montaje limpio y soluciones pensadas para viviendas que necesitan una protección metálica duradera.";

  if (productCount > 0) {
    return `${baseText} Mostramos ${productCount} modelos reales del catálogo para que puedas comparar acabados, tipos de apertura y opciones de instalación sin obra desde la misma landing.`;
  }

  return baseText;
}

function buildMetaDescription(productCount: number) {
  const baseDescription =
    productCount > 0
      ? `Catálogo de rejas para ventanas a medida, rejas sin obra y rejas metálicas con ${productCount} modelos reales enlazados a sus fichas.`
      : "Catálogo de rejas para ventanas a medida, rejas sin obra y rejas metálicas fabricadas por MetalWolft.";

  return trimTextAtWord(baseDescription, 155);
}

async function getRejasCategoryData(): Promise<RejasCategoryData> {
  try {
    const [products, categories] = await Promise.all([
      fetchCategoryProducts(CATEGORY_SLUG),
      fetchCategories()
    ]);

    const category = categories.find((item) => item.slug === CATEGORY_SLUG) || null;

    return {
      categoryName: category?.nombre?.trim() || "Rejas para ventanas",
      categoryDescription: category?.descripcion || null,
      products
    };
  } catch (error) {
    if (shouldAllowLocalApiFallback() && isApiUnavailableError(error)) {
      return {
        categoryName: "Rejas para ventanas",
        categoryDescription: null,
        products: []
      };
    }

    throw error;
  }
}

function buildItemListJsonLd(products: ApiProduct[]) {
  return {
    "@context": "https://schema.org",
    "@type": "ItemList",
    name: "Rejas para ventanas",
    itemListElement: products.map((product, index) => ({
      "@type": "ListItem",
      position: index + 1,
      url: absoluteUrl(`/${CATEGORY_SLUG}/${product.slug}`),
      name: product.h1_seo || product.nombre
    }))
  };
}

function buildCollectionJsonLd(description: string) {
  return {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    name: "Rejas para ventanas",
    url: absoluteUrl(`/${CATEGORY_SLUG}`),
    description
  };
}

function buildProductExcerpt(product: ApiProduct) {
  const raw =
    product.descripcion_seo?.trim() ||
    product.descripcion?.trim() ||
    "Modelo de reja metálica fabricado a medida por MetalWolft.";

  return trimTextAtWord(raw, 180);
}

export async function generateMetadata(): Promise<Metadata> {
  const data = await getRejasCategoryData();
  const description = buildMetaDescription(data.products.length);
  const image = data.products[0]?.imagen || siteConfig.defaultOgImage;

  return buildMetadata({
    title: "Rejas para ventanas a medida y sin obra | MetalWolft",
    description,
    path: `/${CATEGORY_SLUG}`,
    image
  });
}

export default async function RejasParaVentanasPage() {
  const data = await getRejasCategoryData();
  const introText = buildIntroText(data.products.length, data.categoryDescription);
  const description = buildMetaDescription(data.products.length);
  const featuredProducts = data.products.filter((product) => product.es_mas_vendido);

  return (
    <div className="mw-page">
      <PageContainer>
        <BreadcrumbJsonLd
          items={[
            { name: "Inicio", path: "/" },
            { name: "Rejas para ventanas", path: `/${CATEGORY_SLUG}` }
          ]}
        />
        <JsonLd data={buildCollectionJsonLd(description)} />
        <JsonLd data={buildItemListJsonLd(data.products)} />

        <nav className="mw-breadcrumbs" aria-label="Breadcrumb">
          <Link href="/">Inicio</Link>
          <span>/</span>
          <span aria-current="page">Rejas para ventanas</span>
        </nav>

        <section className="mw-hero">
          <div className="mw-hero__copy">
            <p className="mw-eyebrow">Catálogo principal</p>
            <h1 className="mw-title mw-title--compact">Rejas para ventanas a medida</h1>
            <p className="mw-lead">{introText}</p>
            <div className="mw-actions">
              <Link className="mw-button mw-button--primary" href="#modelos-reales">
                Ver modelos reales
              </Link>
              <Link className="mw-button mw-button--secondary" href="/medir-hueco-rejas-para-ventanas">
                Cómo medir el hueco
              </Link>
            </div>
          </div>

          <aside className="mw-panel" aria-label="Resumen de la landing">
            <p className="mw-note">Resumen de compra</p>
            <h2>{data.categoryName}</h2>
            <ul className="mw-list">
              <li>Rejas metálicas fabricadas a medida.</li>
              <li>Modelos visibles en esta categoría: {data.products.length}.</li>
              <li>Enlaces directos a guías y fichas de producto.</li>
            </ul>
          </aside>
        </section>

        <section className="mw-section">
          <h2>Rejas para ventanas a medida</h2>
          <p>
            Esta landing concentra la intención comercial principal del proyecto:
            ayudar a quien busca rejas para ventanas, rejas para ventanas a medida
            y soluciones metálicas fabricadas según el hueco real de cada vivienda.
          </p>
          <p>
            Aquí mostramos contenido legible desde servidor, un listado real de
            productos y enlaces directos a cada ficha para que puedas comparar
            diseño, apertura y acabado sin perder tiempo.
          </p>
        </section>

        <section className="mw-section">
          <h2>Rejas para ventanas sin obra</h2>
          <p>
            Muchos clientes buscan una instalación limpia y rápida. Por eso esta
            página enlaza directamente a la guía de medición, la guía de
            instalación sin obra y los contenidos de apoyo que explican acabados,
            montaje y tiempos de fabricación.
          </p>
          <div className="mw-actions">
            <Link className="mw-button mw-button--secondary" href="/instalation-rejas-para-ventanas">
              Guía de instalación sin obra
            </Link>
            <Link className="mw-button mw-button--secondary" href="/rejas-para-ventanas-sin-obra">
              Rejas sin obra
            </Link>
          </div>
        </section>

        <section className="mw-section" id="modelos-reales">
          <h2>Modelos reales de rejas metálicas</h2>
          <p>
            Este listado muestra productos reales del catálogo y te permite pasar
            de la visión general a cada ficha individual con un solo clic.
          </p>

          {featuredProducts.length > 0 ? (
            <>
              <h3>Productos destacados</h3>
              <ul className="mw-list">
                {featuredProducts.map((product) => (
                  <li key={`featured-${product.id}`}>
                    <Link href={`/${CATEGORY_SLUG}/${product.slug}`}>
                      {product.h1_seo || product.nombre}
                    </Link>
                  </li>
                ))}
              </ul>
            </>
          ) : null}

          {data.products.length === 0 ? (
            <p>
              La categoría existe, pero ahora mismo la API no devuelve productos
              visibles para esta landing.
            </p>
          ) : (
            <div className="mw-grid">
              {data.products.map((product) => {
                const productHref = `/${CATEGORY_SLUG}/${product.slug}`;

                return (
                  <article className="mw-card" key={product.id}>
                    {product.imagen ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={product.imagen} alt={product.h1_seo || product.nombre} />
                    ) : null}
                    <h3>{product.h1_seo || product.nombre}</h3>
                    <p>{buildProductExcerpt(product)}</p>
                    <div className="mw-actions">
                      <Link className="mw-button mw-button--primary" href={productHref}>
                        Ver ficha de {product.h1_seo || product.nombre}
                      </Link>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>

        <section className="mw-section">
          <h2>Guías y enlaces internos para elegir mejor</h2>
          <p>
            Estos enlaces ayudan a resolver dudas habituales sobre medición,
            instalación, estilo y montaje sin obra antes de elegir el modelo
            definitivo.
          </p>
          <ul className="mw-list">
            <li>
              <Link href="/medir-hueco-rejas-para-ventanas">
                Medir hueco para rejas para ventanas
              </Link>
            </li>
            <li>
              <Link href="/instalation-rejas-para-ventanas">
                Instalación de rejas para ventanas sin obra
              </Link>
            </li>
            <li>
              <Link href="/rejas-para-ventanas-modernas">
                Rejas para ventanas modernas
              </Link>
            </li>
            <li>
              <Link href="/rejas-para-ventanas-sin-obra">
                Rejas para ventanas sin obra
              </Link>
            </li>
          </ul>
        </section>

        <section className="mw-section">
          <h2>Fabricación y envío desde taller</h2>
          <p>
            Trabajamos con fabricación a medida, procesos claros y envío desde
            taller para que puedas elegir la reja adecuada con una base técnica
            sencilla y sin mezclar información comercial innecesaria.
          </p>
        </section>
      </PageContainer>
    </div>
  );
}
