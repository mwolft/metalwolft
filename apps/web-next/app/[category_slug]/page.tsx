import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { PageContainer } from "@/components/layout/PageContainer";
import { BreadcrumbJsonLd } from "@/components/seo/BreadcrumbJsonLd";
import { JsonLd } from "@/components/seo/JsonLd";
import { absoluteUrl, buildMetadata, siteConfig } from "@/lib/metadata";
import {
  ApiCategory,
  ApiProduct,
  ApiRequestError,
  fetchCategories,
  fetchCategoryProducts
} from "@/lib/api";

type CategoryPageParams = {
  category_slug: string;
};

type CategoryPageProps = {
  params: CategoryPageParams;
};

type CategoryPageData = {
  category: ApiCategory | null;
  products: ApiProduct[];
};

function humanizeSlug(slug: string) {
  return slug
    .split("-")
    .filter(Boolean)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}

function buildCategoryName(category: ApiCategory | null, slug: string) {
  return category?.nombre?.trim() || humanizeSlug(slug);
}

function buildCategoryDescription(category: ApiCategory | null, slug: string, productCount: number) {
  const categoryName = buildCategoryName(category, slug);
  const raw =
    category?.descripcion?.trim() ||
    `Descubre ${categoryName.toLowerCase()} fabricadas a medida por MetalWolft, con soluciones pensadas para seguridad, instalacion practica y envio directo desde taller.`;

  if (productCount > 0 && !category?.descripcion?.trim()) {
    return `${raw} Actualmente mostramos ${productCount} modelos disponibles para que puedas revisar acabados, aperturas y enlaces a cada ficha de producto.`;
  }

  return raw;
}

function buildCategoryTitle(category: ApiCategory | null, slug: string) {
  return `${buildCategoryName(category, slug)} | MetalWolft`;
}

function buildCategoryMetaDescription(category: ApiCategory | null, slug: string, productCount: number) {
  const raw = buildCategoryDescription(category, slug, productCount);
  return raw.length > 155 ? `${raw.slice(0, 152)}...` : raw;
}

function getCategoryImage(category: ApiCategory | null, products: ApiProduct[]) {
  return category?.image_url || products[0]?.imagen || siteConfig.defaultOgImage;
}

async function getCategoryPageData(params: CategoryPageParams): Promise<CategoryPageData | null> {
  try {
    const [products, categories] = await Promise.all([
      fetchCategoryProducts(params.category_slug),
      fetchCategories().catch(() => [])
    ]);

    const category = categories.find((item) => item.slug === params.category_slug) || null;
    return {
      category,
      products
    };
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 404) {
      return null;
    }

    throw error;
  }
}

async function getCategoryPageDataForMetadata(params: CategoryPageParams): Promise<CategoryPageData | null> {
  try {
    return await getCategoryPageData(params);
  } catch {
    return null;
  }
}

function buildItemListJsonLd(categoryName: string, categorySlug: string, products: ApiProduct[]) {
  return {
    "@context": "https://schema.org",
    "@type": "ItemList",
    name: categoryName,
    itemListElement: products.map((product, index) => ({
      "@type": "ListItem",
      position: index + 1,
      url: absoluteUrl(`/${categorySlug}/${product.slug}`),
      name: product.h1_seo || product.nombre
    }))
  };
}

export async function generateMetadata({
  params
}: CategoryPageProps): Promise<Metadata> {
  const data = await getCategoryPageDataForMetadata(params);

  if (!data) {
    return buildMetadata({
      title: "Categoria no encontrada",
      description: "La categoria solicitada no esta disponible.",
      path: `/${params.category_slug}`
    });
  }

  return buildMetadata({
    title: buildCategoryTitle(data.category, params.category_slug),
    description: buildCategoryMetaDescription(
      data.category,
      params.category_slug,
      data.products.length
    ),
    path: `/${params.category_slug}`,
    image: getCategoryImage(data.category, data.products)
  });
}

export default async function CategoryPage({ params }: CategoryPageProps) {
  const data = await getCategoryPageData(params);

  if (!data) {
    notFound();
  }

  const categoryName = buildCategoryName(data.category, params.category_slug);
  const introDescription = buildCategoryDescription(
    data.category,
    params.category_slug,
    data.products.length
  );

  return (
    <div className="mw-page">
      <PageContainer>
        <BreadcrumbJsonLd
          items={[
            { name: "Inicio", path: "/" },
            { name: categoryName, path: `/${params.category_slug}` }
          ]}
        />
        <JsonLd data={buildItemListJsonLd(categoryName, params.category_slug, data.products)} />

        <div className="mw-breadcrumbs" aria-label="Breadcrumb">
          <span>Inicio</span>
          <span>/</span>
          <span>{categoryName}</span>
        </div>

        <section className="mw-hero">
          <div className="mw-hero__copy">
            <p className="mw-eyebrow">Catalogo</p>
            <h1 className="mw-title mw-title--compact">{categoryName}</h1>
            <p className="mw-lead">{introDescription}</p>
          </div>

          <aside className="mw-panel" aria-label="Resumen de la categoria">
            <p className="mw-note">Resumen de categoria</p>
            <h2>{categoryName}</h2>
            <ul className="mw-list">
              <li>Modelos visibles: {data.products.length}</li>
              <li>Enlaces directos a cada ficha de producto.</li>
              <li>Informacion orientada a fabricacion a medida.</li>
            </ul>
          </aside>
        </section>

        <section className="mw-section">
          <h2>Modelos disponibles</h2>
          {data.products.length === 0 ? (
            <p>
              Esta categoria existe en el catalogo, pero ahora mismo no devuelve
              productos visibles desde la API publica.
            </p>
          ) : (
            <div className="mw-grid">
              {data.products.map((product) => {
                const productHref = `/${params.category_slug}/${product.slug}`;
                const productDescription =
                  product.descripcion_seo?.trim() ||
                  product.descripcion?.trim() ||
                  "Producto a medida fabricado por MetalWolft.";

                return (
                  <article className="mw-card" key={product.id}>
                    {product.imagen ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={product.imagen} alt={product.nombre} />
                    ) : null}
                    <h3>{product.h1_seo || product.nombre}</h3>
                    <p>{productDescription}</p>
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
          <h2>Fabricacion, medidas y envio</h2>
          <p>
            Cada categoria esta pensada para ayudarte a pasar de una vista
            general a la ficha exacta del producto, con informacion clara sobre
            medidas, acabados y envio desde taller.
          </p>
        </section>
      </PageContainer>
    </div>
  );
}
