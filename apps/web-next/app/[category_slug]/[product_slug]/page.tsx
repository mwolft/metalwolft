import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { PageContainer } from "@/components/layout/PageContainer";
import { ProductConfigurator } from "@/components/product/ProductConfigurator";
import { BreadcrumbJsonLd } from "@/components/seo/BreadcrumbJsonLd";
import { JsonLd } from "@/components/seo/JsonLd";
import {
  absoluteUrl,
  buildMetadata,
  siteConfig,
  trimTextAtWord
} from "@/lib/metadata";
import {
  ApiRequestError,
  fetchProductBySlug,
  type ApiProduct
} from "@/lib/api";

type ProductPageParams = {
  category_slug: string;
  product_slug: string;
};

type ProductPageProps = {
  params: Promise<ProductPageParams>;
};

async function getProduct(params: ProductPageParams): Promise<ApiProduct | null> {
  try {
    return await fetchProductBySlug(params.category_slug, params.product_slug);
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 404) {
      return null;
    }

    throw error;
  }
}

async function getProductForMetadata(params: ProductPageParams): Promise<ApiProduct | null> {
  try {
    return await fetchProductBySlug(params.category_slug, params.product_slug);
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 404) {
      return null;
    }

    return null;
  }
}

function buildProductTitle(product: ApiProduct) {
  return (
    product.titulo_seo ||
    `${product.nombre} | ${product.categoria_nombre || "Rejas para ventanas"}`
  );
}

function buildProductDescriptionFallback(product: ApiProduct) {
  const categoryName =
    (product.categoria_nombre || "rejas metálicas").toLowerCase();

  return `${product.nombre} fabricada a medida por MetalWolft, con una solución segura y un acabado metálico pensado para ${categoryName}.`;
}

function buildProductDescription(product: ApiProduct) {
  const seoDescription = product.descripcion_seo?.trim();
  const technicalDescription = product.descripcion?.trim();
  const shouldUseFallback =
    !seoDescription &&
    (!technicalDescription ||
      technicalDescription.length < 90 ||
      /(?:\d+x\d+|\bmm\b|bastidor|chapa|perfil|pletina|tubo|hierro)/i.test(
        technicalDescription
      ));
  const raw =
    seoDescription ||
    (shouldUseFallback ? buildProductDescriptionFallback(product) : technicalDescription) ||
    "Producto de carpintería metálica a medida fabricado por MetalWolft.";

  return trimTextAtWord(raw, 155);
}

function getProductImage(product: ApiProduct) {
  return product.imagen || product.images?.[0]?.image_url || siteConfig.defaultOgImage;
}

function buildProductJsonLd(product: ApiProduct) {
  const canonicalPath = `/${product.category_slug}/${product.slug}`;
  const image = getProductImage(product);
  const productImages = product.images ?? [];

  return {
    "@context": "https://schema.org",
    "@type": "Product",
    name: product.h1_seo || product.nombre,
    description: product.descripcion,
    image: [image, ...productImages.map((item) => item.image_url)].filter(Boolean),
    sku: product.slug,
    mpn: String(product.id),
    category: product.categoria_nombre,
    brand: {
      "@type": "Brand",
      name: siteConfig.name
    },
    url: absoluteUrl(canonicalPath)
  };
}

export async function generateMetadata({
  params
}: ProductPageProps): Promise<Metadata> {
  const resolvedParams = await params;
  const product = await getProductForMetadata(resolvedParams);

  if (!product) {
    return buildMetadata({
      title: "Producto no encontrado",
      description: "La ficha de producto solicitada no está disponible.",
      path: `/${resolvedParams.category_slug}/${resolvedParams.product_slug}`
    });
  }

  return buildMetadata({
    title: buildProductTitle(product),
    description: buildProductDescription(product),
    path: `/${product.category_slug}/${product.slug}`,
    image: getProductImage(product)
  });
}

export default async function ProductPage({ params }: ProductPageProps) {
  const resolvedParams = await params;
  const product = await getProduct(resolvedParams);

  if (!product) {
    notFound();
  }

  const h1 = product.h1_seo || product.nombre;
  const canonicalPath = `/${product.category_slug}/${product.slug}`;
  const categoryPath = `/${product.category_slug}`;
  const productImages = product.images ?? [];
  const visibleDescription =
    product.descripcion?.trim() || "Descripción técnica no disponible en este momento.";

  return (
    <div className="mw-page">
      <PageContainer>
        <BreadcrumbJsonLd
          items={[
            { name: "Inicio", path: "/" },
            { name: product.categoria_nombre || "Catálogo", path: categoryPath },
            { name: h1, path: canonicalPath }
          ]}
        />
        <JsonLd data={buildProductJsonLd(product)} />

        <nav className="mw-breadcrumbs" aria-label="Breadcrumb">
          <Link href="/">Inicio</Link>
          <span>/</span>
          <Link href={categoryPath}>{product.categoria_nombre || "Catálogo"}</Link>
          <span>/</span>
          <span aria-current="page">{h1}</span>
        </nav>

        <section className="mw-hero">
          <div className="mw-hero__copy">
            <p className="mw-eyebrow">Modelo a medida</p>
            <h1 className="mw-title mw-title--compact">{h1}</h1>
            <p className="mw-lead">{visibleDescription}</p>
            <div className="mw-actions">
              <Link className="mw-button mw-button--primary" href={categoryPath}>
                Ver más modelos de la categoría
              </Link>
              <Link className="mw-button mw-button--secondary" href="/rejas-para-ventanas-sin-obra">
                Rejas para ventanas sin obra
              </Link>
            </div>
          </div>

          <aside className="mw-panel mw-product-panel" aria-label="Configurar producto">
            <ProductConfigurator
              productId={product.id}
              categorySlug={product.category_slug}
              productSlug={product.slug}
              productName={product.nombre}
              pricePerM2={product.precio}
              discountedPricePerM2={product.precio_rebajado}
              availableForSale={product.available_for_sale}
            />

            <div className="mw-product-summary">
              <p className="mw-note">Resumen de fabricación</p>
              <h2>{product.nombre}</h2>
              <ul className="mw-list">
                <li>
                  Categoría:{" "}
                  <Link href={categoryPath}>{product.categoria_nombre || "Catálogo"}</Link>
                </li>
                {product.subcategoria_nombre ? (
                  <li>Subcategoría: {product.subcategoria_nombre}</li>
                ) : null}
                {product.has_abatible ? <li>Disponible en versión abatible.</li> : null}
                {product.has_door_model ? <li>Disponible en versión puerta.</li> : null}
                <li>Fabricación a medida y envío directo desde taller.</li>
              </ul>
            </div>
          </aside>
        </section>

        <section className="mw-section">
          <h2>Descripción técnica</h2>
          <p>{visibleDescription}</p>
          <p>
            Esta ficha resume el modelo, sus acabados y el planteamiento de
            fabricación para ayudarte a valorar si encaja con el hueco de tu
            ventana y con el nivel de seguridad que buscas para tu vivienda.
          </p>
        </section>

        {productImages.length > 0 ? (
          <section className="mw-section">
            <h2>Imágenes del producto</h2>
            <div className="mw-grid">
              {productImages.slice(0, 4).map((image) => (
                <article className="mw-card" key={image.id}>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={image.image_url} alt={h1} />
                </article>
              ))}
            </div>
          </section>
        ) : null}

        <section className="mw-section">
          <h2>Instalación y medición</h2>
          <p>
            Antes de pedir una reja metálica a medida conviene revisar el hueco,
            el tipo de apoyo y la instalación prevista. Por eso enlazamos
            directamente a las guías que ayudan a medir mejor y a preparar una
            instalación sin obra cuando el proyecto lo permite.
          </p>
          <div className="mw-actions">
            <Link className="mw-button mw-button--secondary" href="/medir-hueco-rejas-para-ventanas">
              Cómo medir el hueco
            </Link>
            <Link className="mw-button mw-button--secondary" href="/instalation-rejas-para-ventanas">
              Guía de instalación
            </Link>
          </div>
        </section>

        <section className="mw-section">
          <h2>Fabricación a medida</h2>
          <p>
            Cada modelo se plantea para fabricar la reja según medidas reales,
            con un acabado metálico adaptado al tipo de vivienda y al uso
            previsto. Si quieres comparar alternativas, puedes volver a la
            categoría y revisar otros modelos fijos o abatibles antes de tomar
            una decisión.
          </p>
          <ul className="mw-list">
            <li>
              <Link href={categoryPath}>
                Ver todos los modelos de {product.categoria_nombre || "la categoría"}
              </Link>
            </li>
            <li>
              <Link href="/rejas-para-ventanas-sin-obra">
                Rejas para ventanas sin obra
              </Link>
            </li>
          </ul>
        </section>
      </PageContainer>
    </div>
  );
}
