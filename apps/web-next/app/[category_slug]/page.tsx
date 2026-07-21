import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
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
  params: Promise<CategoryPageParams>;
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
    `Descubre ${categoryName.toLowerCase()} a medida de MetalWolft, con soluciones metálicas pensadas para mejorar seguridad, instalación y acabado final.`;

  if (productCount > 0 && !category?.descripcion?.trim()) {
    return `${raw} Actualmente mostramos ${productCount} modelos reales para que puedas comparar acabados, aperturas y accesos directos a cada ficha de producto.`;
  }

  return raw;
}

function buildCategoryTitle(category: ApiCategory | null, slug: string) {
  return `${buildCategoryName(category, slug)} | MetalWolft`;
}

function buildCategoryMetaDescription(category: ApiCategory | null, slug: string, productCount: number) {
  const raw = buildCategoryDescription(category, slug, productCount);
  return trimTextAtWord(raw, 155);
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

function buildCollectionJsonLd(categoryName: string, categorySlug: string, description: string) {
  return {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    name: categoryName,
    url: absoluteUrl(`/${categorySlug}`),
    description
  };
}

function buildProductExcerpt(product: ApiProduct) {
  const raw =
    product.descripcion_seo?.trim() ||
    product.descripcion?.trim() ||
    "Producto metálico fabricado a medida por MetalWolft.";

  return trimTextAtWord(raw, 180);
}

export async function generateMetadata({
  params
}: CategoryPageProps): Promise<Metadata> {
  const resolvedParams = await params;
  const data = await getCategoryPageDataForMetadata(resolvedParams);

  if (!data) {
    return buildMetadata({
      title: "Categoria no encontrada",
      description: "La categoria solicitada no esta disponible.",
      path: `/${resolvedParams.category_slug}`
    });
  }

  return buildMetadata({
    title: buildCategoryTitle(data.category, resolvedParams.category_slug),
    description: buildCategoryMetaDescription(
      data.category,
      resolvedParams.category_slug,
      data.products.length
    ),
    path: `/${resolvedParams.category_slug}`,
    image: getCategoryImage(data.category, data.products)
  });
}

export default async function CategoryPage({ params }: CategoryPageProps) {
  const resolvedParams = await params;
  const data = await getCategoryPageData(resolvedParams);

  if (!data) {
    notFound();
  }

  const categoryName = buildCategoryName(data.category, resolvedParams.category_slug);
  const introDescription = buildCategoryDescription(
    data.category,
    resolvedParams.category_slug,
    data.products.length
  );

  return (
    <div className="mw-page">
      <PageContainer>
        <BreadcrumbJsonLd
          items={[
            { name: "Inicio", path: "/" },
            { name: categoryName, path: `/${resolvedParams.category_slug}` }
          ]}
        />
        <JsonLd
          data={buildCollectionJsonLd(categoryName, resolvedParams.category_slug, introDescription)}
        />
        <JsonLd
          data={buildItemListJsonLd(categoryName, resolvedParams.category_slug, data.products)}
        />

        <nav className="mw-breadcrumbs" aria-label="Breadcrumb">
          <Link href="/">Inicio</Link>
          <span>/</span>
          <span aria-current="page">{categoryName}</span>
        </nav>

        <section className="mw-hero">
          <div className="mw-hero__copy">
            <p className="mw-eyebrow">Catálogo</p>
            <h1 className="mw-title mw-title--compact">{categoryName}</h1>
            <p className="mw-lead">{introDescription}</p>
          </div>

          <aside className="mw-panel" aria-label="Resumen de la categoría">
            <p className="mw-note">Resumen de categoría</p>
            <h2>Qué encontrarás en esta categoría</h2>
            <ul className="mw-list">
              <li>Modelos visibles: {data.products.length}</li>
              <li>Acceso directo a cada ficha de producto.</li>
              <li>Información orientada a fabricación a medida.</li>
            </ul>
          </aside>
        </section>

        <section className="mw-section">
          <h2>Modelos disponibles</h2>
          <p>
            Revisa esta selección de modelos para comparar acabados, medidas y
            soluciones metálicas pensadas para exterior. Cada ficha enlaza a su
            detalle técnico y a las opciones de fabricación a medida.
          </p>
          {data.products.length === 0 ? (
            <p>
              Esta categoría existe en el catálogo, pero ahora mismo no devuelve
              productos visibles desde la API pública.
            </p>
          ) : (
            <div className="mw-grid">
              {data.products.map((product) => {
                const productHref = `/${resolvedParams.category_slug}/${product.slug}`;

                return (
                  <article className="mw-card" key={product.id}>
                    {product.imagen ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={product.imagen} alt={product.nombre} />
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
          <h2>Fabricación, medidas y envío</h2>
          <p>
            Cada categoría está pensada para ayudarte a pasar de una vista
            general a la ficha exacta del producto, con información clara sobre
            medidas, acabados, instalación y envío directo desde taller.
          </p>
        </section>
      </PageContainer>
    </div>
  );
}
