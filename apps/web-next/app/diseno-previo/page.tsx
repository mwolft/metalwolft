import type { Metadata } from "next";
import { DesignServiceBuilder } from "@/components/design-service/DesignServiceBuilder";
import { PageContainer } from "@/components/layout/PageContainer";
import { fetchCategoryProducts, type ApiProduct } from "@/lib/api";
import { type DesignServiceProductOption } from "@/lib/design-service-builder";
import { type DesignServiceDraftItem } from "@/lib/design-service-draft";
import { buildMetadata } from "@/lib/metadata";
import { parseDesignServiceSeed } from "@/lib/design-service-seed";

const DESIGN_CATEGORY_SLUG = "rejas-para-ventanas";

export const revalidate = 300;

export const metadata: Metadata = buildMetadata({
  title: "Diseño previo a medida para rejas | MetalWolft",
  description:
    "Visualiza una reja a medida antes de encargarla. Elige el modelo y las medidas para recibir una representación previa con entrega estimada en 24 h.",
  path: "/diseno-previo"
});

type DesignServicePageProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

function mapProduct(product: ApiProduct): DesignServiceProductOption {
  return { id: product.id, slug: product.slug, name: product.nombre };
}

async function getDesignProducts() {
  try {
    return (await fetchCategoryProducts(DESIGN_CATEGORY_SLUG))
      .filter((product) => product.available_for_sale)
      .map(mapProduct);
  } catch {
    return [];
  }
}

function valueFromSearchParams(value: string | string[] | undefined) {
  return typeof value === "string" ? value : null;
}

function seedFromSearchParams(
  searchParams: Record<string, string | string[] | undefined>,
  products: DesignServiceProductOption[]
): DesignServiceDraftItem | null {
  const seed = parseDesignServiceSeed(
    new URLSearchParams({
      producto: valueFromSearchParams(searchParams.producto) || "",
      ancho: valueFromSearchParams(searchParams.ancho) || "",
      alto: valueFromSearchParams(searchParams.alto) || ""
    })
  );
  if (!seed) return null;

  const product = products.find((candidate) => candidate.slug === seed.product_slug);
  return product
    ? {
        product_id: product.id,
        product_slug: product.slug,
        product_name: product.name,
        width_cm: seed.width_cm,
        height_cm: seed.height_cm
      }
    : null;
}

export default async function DesignServicePage({ searchParams }: DesignServicePageProps) {
  const [products, resolvedSearchParams] = await Promise.all([getDesignProducts(), searchParams]);
  const initialSeed = seedFromSearchParams(resolvedSearchParams, products);

  return (
    <PageContainer>
      <div className="mw-design-page">
        <header className="mw-design-hero">
          <div className="mw-design-hero__copy">
            <p className="mw-eyebrow">Diseño previo a medida</p>
            <h1 className="mw-title mw-title--compact">Visualiza tu reja antes de encargarla</h1>
            <p className="mw-lead">
              Te preparamos una representación previa del modelo adaptada a las medidas que necesitas,
              para que puedas valorar sus proporciones antes de realizar el pedido.
            </p>
          </div>
          <div className="mw-design-hero__facts" aria-label="Información del servicio">
            <p><strong>Desde 24,95 € IVA incluido</strong></p>
            <p><strong>Entrega estimada: 24 h</strong></p>
            <p>No es un plano técnico ni una simulación exacta de la instalación.</p>
          </div>
        </header>
        {products.length ? (
          <DesignServiceBuilder products={products} initialSeed={initialSeed} />
        ) : (
          <section className="mw-section mw-design-page__unavailable">
            <h2>No podemos cargar los modelos en este momento</h2>
            <p>Vuelve a intentarlo en unos minutos para preparar tu diseño previo.</p>
          </section>
        )}
      </div>
    </PageContainer>
  );
}
