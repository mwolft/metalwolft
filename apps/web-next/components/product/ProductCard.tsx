import Link from "next/link";
import { ProductCardImage } from "@/components/product/ProductCardImage";
import type { ApiProduct } from "@/lib/api";

type ProductCardProps = {
  product: ApiProduct;
  href: string;
  isBestSeller?: boolean;
  isNewDesign?: boolean;
};

export function ProductCard({
  product,
  href,
  isBestSeller = false,
  isNewDesign = false
}: ProductCardProps) {
  const productName = product.h1_seo || product.nombre;
  const description =
    product.descripcion_seo?.trim() ||
    product.descripcion?.trim() ||
    "Modelo metálico fabricado a medida por MetalWolft.";
  const badges = [
    isBestSeller ? "Más vendido" : null,
    isNewDesign ? "Nuevo diseño" : null
  ].filter((badge): badge is string => Boolean(badge));
  const accessibleLabel = badges.length
    ? `Ver modelo ${productName}, ${badges.join(", ")}`
    : `Ver modelo ${productName}`;

  return (
    <article className="mw-product-card">
      <Link
        className="mw-product-card__link"
        href={href}
        aria-label={accessibleLabel}
      >
        <div className="mw-product-card__media">
          <ProductCardImage alt={productName} src={product.imagen} />
          {badges.length > 0 ? (
            <div className="mw-product-card__badges">
              {badges.map((badge) => (
                <span className="mw-product-card__badge" key={badge}>
                  {badge}
                </span>
              ))}
            </div>
          ) : null}
        </div>
        <div className="mw-product-card__body">
          <h3 className="mw-product-card__title">{productName}</h3>
          <p className="mw-product-card__description">{description}</p>
          <span className="mw-product-card__cta" aria-hidden="true">
            Ver modelo
          </span>
        </div>
      </Link>
    </article>
  );
}
