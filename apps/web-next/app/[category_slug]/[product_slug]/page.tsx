import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { PageContainer } from "@/components/layout/PageContainer";
import { BreadcrumbJsonLd } from "@/components/seo/BreadcrumbJsonLd";
import { JsonLd } from "@/components/seo/JsonLd";
import { absoluteUrl, buildMetadata, siteConfig } from "@/lib/metadata";
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
  params: ProductPageParams;
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

function buildProductDescription(product: ApiProduct) {
  const raw =
    product.descripcion_seo?.trim() ||
    product.descripcion?.trim() ||
    "Producto de carpintería metálica a medida fabricado por MetalWolft.";

  return raw.length > 155 ? `${raw.slice(0, 152)}...` : raw;
}

function getProductImage(product: ApiProduct) {
  return (
    product.imagen ||
    product.images?.[0]?.image_url ||
    siteConfig.defaultOgImage
  );
}

function buildProductJsonLd(product: ApiProduct) {
  const canonicalPath = `/${product.category_slug}/${product.slug}`;
  const image = getProductImage(product);

  return {
    "@context": "https://schema.org",
    "@type": "Product",
    name: product.h1_seo || product.nombre,
    description: product.descripcion,
    image: [image, ...product.images.map((item) => item.image_url)].filter(Boolean),
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
  const product = await getProductForMetadata(params);

  if (!product) {
    return buildMetadata({
      title: "Producto no encontrado",
      description: "La ficha de producto solicitada no está disponible.",
      path: `/${params.category_slug}/${params.product_slug}`
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
  const product = await getProduct(params);

  if (!product) {
    notFound();
  }

  const h1 = product.h1_seo || product.nombre;
  const canonicalPath = `/${product.category_slug}/${product.slug}`;
  const visibleDescription =
    product.descripcion?.trim() ||
    "Descripción técnica no disponible en este momento.";

  return (
    <div className="mw-page">
      <PageContainer>
        <BreadcrumbJsonLd
          items={[
            { name: "Inicio", path: "/" },
            { name: product.categoria_nombre || "Catálogo", path: `/${product.category_slug}` },
            { name: h1, path: canonicalPath }
          ]}
        />
        <JsonLd data={buildProductJsonLd(product)} />

        <div className="mw-breadcrumbs" aria-label="Breadcrumb">
          <span>Inicio</span>
          <span>/</span>
          <span>{product.categoria_nombre || "Catálogo"}</span>
          <span>/</span>
          <span>{h1}</span>
        </div>

        <section className="mw-hero">
          <div className="mw-hero__copy">
            <p className="mw-eyebrow">Ficha de producto</p>
            <h1 className="mw-title mw-title--compact">{h1}</h1>
            <p className="mw-lead">{visibleDescription}</p>
          </div>

          <aside className="mw-panel" aria-label="Resumen del producto">
            <p className="mw-note">Resumen técnico</p>
            <h2>{product.nombre}</h2>
            <ul className="mw-list">
              <li>Categoría: {product.categoria_nombre}</li>
              {product.subcategoria_nombre ? (
                <li>Subcategoría: {product.subcategoria_nombre}</li>
              ) : null}
              <li>Slug: {product.slug}</li>
              {product.has_abatible ? <li>Incluye variante abatible.</li> : null}
              {product.has_door_model ? <li>Incluye variante puerta.</li> : null}
            </ul>
          </aside>
        </section>

        <section className="mw-section">
          <h2>Descripción técnica</h2>
          <p>{visibleDescription}</p>
        </section>

        {product.images.length > 0 ? (
          <section className="mw-section">
            <h2>Imágenes del producto</h2>
            <div className="mw-grid">
              {product.images.slice(0, 4).map((image) => (
                <article className="mw-card" key={image.id}>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={image.image_url} alt={h1} />
                </article>
              ))}
            </div>
          </section>
        ) : null}

        <section className="mw-section">
          <h2>Arquitectura preparada para siguientes fases</h2>
          <p>
            Esta ficha ya sale renderizada desde servidor y deja preparada la
            migración posterior del configurador, contenido SEO ampliado y enlaces
            internos hacia la categoría principal.
          </p>
        </section>
      </PageContainer>
    </div>
  );
}
