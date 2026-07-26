import Link from "next/link";
import type { Metadata } from "next";
import {
  CategoryFeatureGrid,
  type CategoryFeatureItem
} from "@/components/catalog/CategoryFeatureGrid";
import { PageContainer } from "@/components/layout/PageContainer";
import { DeliveryEstimate } from "@/components/product/DeliveryEstimate";
import { ProductCard } from "@/components/product/ProductCard";
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
import { fetchDeliveryEstimate } from "@/lib/delivery-estimate";

type RejasCategoryData = {
  categoryName: string;
  categoryDescription: string | null;
  products: ApiProduct[];
};

const CATEGORY_SLUG = "rejas-para-ventanas";
const CATEGORY_FEATURES = [
  {
    title: "Medidas personalizadas",
    description:
      "Indica el alto y el ancho necesarios para adaptar la fabricación al hueco de tu ventana."
  },
  {
    title: "Colores y acabados",
    description:
      "Selecciona entre las opciones habilitadas para el modelo durante la configuración."
  },
  {
    title: "Opciones de anclaje",
    description:
      "Elige el sistema de fijación adecuado entre las alternativas disponibles al configurar la reja."
  },
  {
    title: "Presupuesto calculado",
    description:
      "El precio se calcula según el modelo, las medidas, el anclaje y la cantidad seleccionada."
  }
] satisfies readonly CategoryFeatureItem[];

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
    return `${baseText} Mostramos ${productCount} modelos del catálogo para que puedas comparar acabados, tipos de apertura y opciones de instalación sin obra desde la misma landing.`;
  }

  return baseText;
}

function buildMetaDescription(productCount: number) {
  const baseDescription =
    productCount > 0
      ? `Catálogo de rejas para ventanas a medida, rejas sin obra y rejas metálicas con ${productCount} modelos enlazados a sus fichas.`
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
  const [data, deliveryEstimate] = await Promise.all([
    getRejasCategoryData(),
    fetchDeliveryEstimate()
  ]);
  const introText = buildIntroText(data.products.length, data.categoryDescription);
  const description = buildMetaDescription(data.products.length);

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
            <h1 className="mw-title mw-title--compact">Rejas para ventanas a medida: modelos y precios</h1>
            <p className="mw-lead">{introText}</p>
            <div className="mw-actions">
              <Link className="mw-button mw-button--primary" href="#modelos-reales">
                Ver modelos
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

        <DeliveryEstimate estimate={deliveryEstimate} variant="category" />

        <section className="mw-section" id="modelos-reales">
          <h2>Modelos de rejas metálicas</h2>
          <p>
            Este listado muestra productos del catálogo y te permite pasar
            de la visión general a cada ficha individual con un solo clic.
          </p>

          {data.products.length === 0 ? (
            <p>
              La categoría existe, pero ahora mismo la API no devuelve productos
              visibles para esta landing.
            </p>
          ) : (
            <div className="mw-product-grid">
              {data.products.map((product) => {
                const productHref = `/${CATEGORY_SLUG}/${product.slug}`;

                return (
                  <ProductCard
                    href={productHref}
                    isBestSeller={product.es_mas_vendido}
                    isNewDesign={product.es_nuevo_diseno}
                    key={product.id}
                    product={product}
                  />
                );
              })}
            </div>
          )}
        </section>

        <CategoryFeatureGrid
          introduction="Cada modelo se adapta a las medidas y opciones elegidas al realizar el pedido."
          items={CATEGORY_FEATURES}
          title="Configura tu reja a medida"
        />

        <section className="mw-section">
          <h2>Cómo elegir una reja para tu ventana</h2>
          <p>
            Al comparar los modelos, fíjate en la distribución de los barrotes, la
            presencia de elementos horizontales y el nivel decorativo del diseño.
          </p>
          <p>
            El modelo que elijas se fabricará adaptado a las medidas que indiques al
            configurar el pedido.
          </p>
        </section>

        <section className="mw-section">
          <h2>Qué debes comprobar antes de hacer el pedido</h2>
          <p>
            Antes de hacer el pedido, mide correctamente el hueco y comprueba el
            soporte donde se fijará la reja.
          </p>
          <p>
            MetalWolft fabrica y envía la reja, pero no realiza la instalación.
            Consulta las guías de medición e instalación antes de comprar.
          </p>
          <div className="mw-actions">
            <Link className="mw-button mw-button--secondary" href="/medir-hueco-rejas-para-ventanas">
              Cómo medir el hueco
            </Link>
            <Link className="mw-button mw-button--secondary" href="/instalation-rejas-para-ventanas">
              Cómo instalar una reja
            </Link>
          </div>
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
          <h2>Fabricación y entrega de tu reja</h2>
          <p>
            La fabricación comienza después de recibir el pedido y se realiza según
            las medidas y la configuración elegidas.
          </p>
          <p>
            Una vez terminada, la reja se prepara para el transporte y se envía a
            domicilio en España peninsular.
          </p>
        </section>
      </PageContainer>
    </div>
  );
}
