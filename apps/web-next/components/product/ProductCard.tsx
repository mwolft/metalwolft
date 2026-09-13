import Link from "next/link";
import { ProductCardImage } from "@/components/product/ProductCardImage";
import type { ApiProduct } from "@/lib/api";

type ProductCardProps = {
  product: ApiProduct;
  href: string;
  isBestSeller?: boolean;
  isNewDesign?: boolean;
};

type ProductBadge = {
  id: "best-seller" | "new-design";
  label: string;
  className: string;
};

type ProductVariant = {
  id: "hinged" | "door";
  label: string;
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
    isBestSeller
      ? {
          id: "best-seller",
          label: "Más vendido",
          className: "mw-product-card__badge--best-seller"
        }
      : null,
    isNewDesign
      ? {
          id: "new-design",
          label: "Nuevo diseño",
          className: "mw-product-card__badge--new-design"
        }
      : null
  ].filter((badge): badge is ProductBadge => badge !== null);
  const variants = [
    product.has_abatible === true
      ? { id: "hinged", label: "Disponible en versión abatible" }
      : null,
    product.has_door_model === true
      ? { id: "door", label: "Disponible en versión para puerta" }
      : null
  ].filter((variant): variant is ProductVariant => variant !== null);
  const accessibleDetails = [
    ...badges.map((badge) => badge.label),
    ...variants.map((variant) => variant.label)
  ];
  const accessibleLabel = accessibleDetails.length
    ? `Ver modelo ${productName}, ${accessibleDetails.join(", ")}`
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
                <span
                  className={`mw-product-card__badge ${badge.className}`}
                  key={badge.id}
                >
                  {badge.label}
                </span>
              ))}
            </div>
          ) : null}
        </div>
        <div className="mw-product-card__body">
          <h3 className="mw-product-card__title">{productName}</h3>
          <p className="mw-product-card__description">{description}</p>
          {variants.length > 0 ? (
            <div className="mw-product-card__variants">
              {variants.map((variant) => (
                <span className="mw-product-card__variant" key={variant.id}>
                  {variant.label}
                </span>
              ))}
            </div>
          ) : null}
          <span className="mw-product-card__cta" aria-hidden="true">
            Ver modelo
          </span>
        </div>
      </Link>
    </article>
  );
}
