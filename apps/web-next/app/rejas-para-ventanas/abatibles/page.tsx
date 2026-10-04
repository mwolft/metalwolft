import Link from "next/link";
import type { Metadata } from "next";
import { CatalogTypeNavigation } from "@/components/catalog/CatalogTypeNavigation";
import { PageContainer } from "@/components/layout/PageContainer";
import { ProductCard } from "@/components/product/ProductCard";
import { BreadcrumbJsonLd } from "@/components/seo/BreadcrumbJsonLd";
import { JsonLd } from "@/components/seo/JsonLd";
import { fetchCategoryProducts } from "@/lib/api";
import { selectAbatibleCollection } from "@/lib/abatible-collection";
import { buildMetadata, absoluteUrl } from "@/lib/metadata";
import { getProductCardContent } from "@/lib/product-card-content";
import { getProductAlternativeLinks } from "@/lib/product-families";

const CATEGORY_PATH = "/rejas-para-ventanas";
const COLLECTION_PATH = CATEGORY_PATH + "/abatibles";
const TITLE = "Rejas abatibles para ventanas a medida";
const DESCRIPTION = "Compara 5 rejas abatibles para ventanas fabricadas a medida. Consulta diseños y precios por m² y entra en cada modelo para configurar tus medidas.";

export const metadata: Metadata = buildMetadata({
  title: TITLE + " | MetalWolft",
  description: DESCRIPTION,
  path: COLLECTION_PATH,
});

export default async function AbatiblesPage() {
  const products = selectAbatibleCollection(await fetchCategoryProducts("rejas-para-ventanas"));

  return (
    <div className="mw-page">
      <PageContainer>
        <BreadcrumbJsonLd items={[
          { name: "Inicio", path: "/" },
          { name: "Rejas para ventanas", path: CATEGORY_PATH },
          { name: "Rejas abatibles", path: COLLECTION_PATH },
        ]} />
        <JsonLd data={{
          "@context": "https://schema.org",
          "@type": "ItemList",
          name: TITLE,
          itemListElement: products.map((product, index) => ({
            "@type": "ListItem",
            position: index + 1,
            name: product.h1_seo || product.nombre,
            url: absoluteUrl(CATEGORY_PATH + "/" + product.slug),
          })),
        }} />

        <nav className="mw-breadcrumbs" aria-label="Breadcrumb">
          <Link href={CATEGORY_PATH}>Rejas para ventanas</Link>
          <span>/</span>
          <span aria-current="page">Rejas abatibles</span>
        </nav>

        <header className="mw-abatible-collection__header">
          <h1 className="mw-title mw-title--compact">{TITLE}</h1>
          <p className="mw-lead">
            Compara nuestros cinco modelos abatibles fabricados a medida y elige el diseño que mejor encaje en tu ventana. Consulta sus tarifas y entra en cada modelo para indicar tus medidas y obtener el precio.
          </p>
        </header>

        <CatalogTypeNavigation active="hinged" />

        <section className="mw-abatible-collection__models" aria-labelledby="abatible-models-title">
          <h2 id="abatible-models-title">Compara nuestros modelos abatibles</h2>
          <p>
            Albany, Cortland, Essex, Idaho y Maryland comparten apertura abatible y fabricación a medida, pero ofrecen diseños diferentes. Compara las cinco opciones y entra en la ficha del modelo que prefieras.
          </p>
          <div className="mw-product-grid">
            {products.map((product) => {
              const cardContent = getProductCardContent(product.slug);
              return (
                <ProductCard
                  key={product.id}
                  product={product}
                  href={CATEGORY_PATH + "/" + product.slug}
                  editorialDescription={cardContent?.description}
                  bestSellerLabel={cardContent?.bestSellerLabel}
                  versionLinks={getProductAlternativeLinks(product.slug)}
                  isBestSeller={product.es_mas_vendido}
                  isNewDesign={product.es_nuevo_diseno}
                />
              );
            })}
          </div>
        </section>

        <section className="mw-abatible-collection__features" aria-labelledby="abatible-features-title">
          <h2 id="abatible-features-title">Cómo son nuestras rejas abatibles</h2>
          <div className="mw-abatible-collection__feature-grid">
            <div><h3>Fabricadas a medida</h3><p>Cada modelo se fabrica según el alto y ancho indicados.</p></div>
            <div><h3>Apertura abatible</h3><p>Las hojas pueden abrirse para permitir acceso a la ventana.</p></div>
            <div><h3>Cierre</h3><p>Los cinco modelos incluyen cerradura y pasadores interiores.</p></div>
            <div><h3>Cinco diseños distintos</h3><p>Cambia la distribución y forma de los tubos y pletinas.</p></div>
          </div>
        </section>
      </PageContainer>
    </div>
  );
}
