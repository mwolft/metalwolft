import Link from "next/link";
import type { Metadata } from "next";
import { PageContainer } from "@/components/layout/PageContainer";
import { BreadcrumbJsonLd } from "@/components/seo/BreadcrumbJsonLd";
import { JsonLd } from "@/components/seo/JsonLd";
import { absoluteUrl, buildMetadata, siteConfig } from "@/lib/metadata";
import { ApiProduct, fetchCategories, fetchCategoryProducts } from "@/lib/api";

type RejasCategoryData = {
  categoryName: string;
  categoryDescription: string | null;
  products: ApiProduct[];
};

const CATEGORY_SLUG = "rejas-para-ventanas";

function trimText(value: string, maxLength: number) {
  const normalized = value.replace(/\s+/g, " ").trim();
  if (normalized.length <= maxLength) {
    return normalized;
  }

  const sliced = normalized.slice(0, maxLength + 1);
  const lastSpace = sliced.lastIndexOf(" ");
  return `${sliced.slice(0, lastSpace > 80 ? lastSpace : maxLength).trim()}...`;
}

function buildIntroText(productCount: number, categoryDescription?: string | null) {
  const baseText =
    categoryDescription?.trim() ||
    "Fabricamos rejas para ventanas a medida con enfoque en seguridad, montaje limpio y soluciones pensadas para viviendas que necesitan una proteccion metalica duradera.";

  if (productCount > 0) {
    return `${baseText} Mostramos ${productCount} modelos reales del catalogo para que puedas comparar acabados, tipos de apertura y opciones de instalacion sin obra desde la misma landing.`;
  }

  return baseText;
}

function buildMetaDescription(productCount: number) {
  const baseDescription =
    productCount > 0
      ? `Catalogo de rejas para ventanas a medida, rejas sin obra y rejas metalicas con ${productCount} modelos reales enlazados a sus fichas.`
      : "Catalogo de rejas para ventanas a medida, rejas sin obra y rejas metalicas fabricadas por MetalWolft.";

  return trimText(baseDescription, 155);
}

async function getRejasCategoryData(): Promise<RejasCategoryData> {
  const [products, categories] = await Promise.all([
    fetchCategoryProducts(CATEGORY_SLUG),
    fetchCategories().catch(() => [])
  ]);

  const category = categories.find((item) => item.slug === CATEGORY_SLUG) || null;

  return {
    categoryName: category?.nombre?.trim() || "Rejas para ventanas",
    categoryDescription: category?.descripcion || null,
    products
  };
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
    "Modelo de reja metalica fabricado a medida por MetalWolft.";

  return trimText(raw, 180);
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

        <div className="mw-breadcrumbs" aria-label="Breadcrumb">
          <span>Inicio</span>
          <span>/</span>
          <span>Rejas para ventanas</span>
        </div>

        <section className="mw-hero">
          <div className="mw-hero__copy">
            <p className="mw-eyebrow">Landing principal</p>
            <h1 className="mw-title mw-title--compact">Rejas para ventanas a medida</h1>
            <p className="mw-lead">{introText}</p>
            <div className="mw-actions">
              <Link className="mw-button mw-button--primary" href="#modelos-reales">
                Ver modelos reales
              </Link>
              <Link className="mw-button mw-button--secondary" href="/medir-hueco-rejas-para-ventanas">
                Como medir el hueco
              </Link>
            </div>
          </div>

          <aside className="mw-panel" aria-label="Resumen de la landing">
            <p className="mw-note">Resumen de compra</p>
            <h2>{data.categoryName}</h2>
            <ul className="mw-list">
              <li>Rejas metalicas fabricadas a medida.</li>
              <li>Modelos visibles en esta categoria: {data.products.length}.</li>
              <li>Enlaces directos a guias y fichas de producto.</li>
            </ul>
          </aside>
        </section>

        <section className="mw-section">
          <h2>Rejas para ventanas a medida</h2>
          <p>
            Esta landing concentra la intencion comercial principal del proyecto:
            ayudar a quien busca rejas para ventanas, rejas para ventanas a medida
            y soluciones metalicas fabricadas segun el hueco real de cada vivienda.
          </p>
          <p>
            Aqui mostramos contenido legible desde servidor, un listado real de
            productos y enlaces directos a cada ficha para que puedas comparar
            diseno, apertura y acabado sin perder tiempo.
          </p>
        </section>

        <section className="mw-section">
          <h2>Rejas para ventanas sin obra</h2>
          <p>
            Muchos clientes buscan una instalacion limpia y rapida. Por eso esta
            pagina enlaza directamente a la guia de medicion, la guia de
            instalacion sin obra y los contenidos de apoyo que explican acabados,
            montaje y tiempos de fabricacion.
          </p>
          <div className="mw-actions">
            <Link className="mw-button mw-button--secondary" href="/instalation-rejas-para-ventanas">
              Guia de instalacion sin obra
            </Link>
            <Link className="mw-button mw-button--secondary" href="/rejas-para-ventanas-sin-obra">
              Rejas sin obra
            </Link>
          </div>
        </section>

        <section className="mw-section" id="modelos-reales">
          <h2>Modelos reales de rejas metalicas</h2>
          <p>
            Este listado muestra productos reales del catalogo y te permite pasar
            de la vision general a cada ficha individual con un solo clic.
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
              La categoria existe, pero ahora mismo la API no devuelve productos
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
                        Ver producto
                      </Link>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>

        <section className="mw-section">
          <h2>Guias y enlaces internos para elegir mejor</h2>
          <p>
            Estos enlaces ayudan a resolver dudas habituales sobre medicion,
            instalacion, estilo y montaje sin obra antes de elegir el modelo
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
                Instalacion de rejas para ventanas sin obra
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
          <h2>Fabricacion y envio desde taller</h2>
          <p>
            Trabajamos con fabricacion a medida, procesos claros y envio desde
            taller para que puedas elegir la reja adecuada con una base tecnica
            sencilla y sin mezclar informacion comercial innecesaria.
          </p>
        </section>
      </PageContainer>
    </div>
  );
}
