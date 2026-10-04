import Link from "next/link";
import { ProductCardCarousel } from "@/components/product/ProductCardCarousel";
import { ProductCardImage } from "@/components/product/ProductCardImage";
import type { ApiProduct } from "@/lib/api";
import { formatCurrency } from "@/lib/configurator-pricing";
import { buildProductCardImages } from "@/lib/product-images";
import type { ProductVersion } from "@/lib/product-families";
import type { ProductCatalogType } from "@/lib/catalog-types";

type ProductCardProps = {
  product: ApiProduct;
  href: string;
  isBestSeller?: boolean;
  isNewDesign?: boolean;
  editorialDescription?: string;
  bestSellerLabel?: "Más vendida" | "Top ventas";
  versionLinks?: Array<{ id: ProductVersion; href: string; label: string }>;
  catalogType?: ProductCatalogType;
};

type ProductBadge = {
  id: "best-seller" | "new-design";
  label: string;
  className: string;
  icon: "trending-up" | "sparkles";
};

type ProductVariant = {
  id: ProductVersion;
  label: string;
  href?: string;
};

function ProductBadgeIcon({ icon }: { icon: ProductBadge["icon"] }) {
  if (icon === "sparkles") {
    return (
      <svg
        aria-hidden="true"
        className="mw-product-card__badge-icon"
        fill="none"
        focusable="false"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
        viewBox="0 0 24 24"
      >
        <path d="m12 3-1.9 5.1L5 10l5.1 1.9L12 17l1.9-5.1L19 10l-5.1-1.9L12 3Z" />
        <path d="m19 15-.8 2.2L16 18l2.2.8L19 21l.8-2.2L22 18l-2.2-.8L19 15Z" />
        <path d="m5 2-.6 1.4L3 4l1.4.6L5 6l.6-1.4L7 4l-1.4-.6L5 2Z" />
      </svg>
    );
  }

  return (
    <svg
      aria-hidden="true"
      className="mw-product-card__badge-icon"
      fill="none"
      focusable="false"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="2"
      viewBox="0 0 24 24"
    >
      <path d="m3 17 6-6 4 4 8-8" />
      <path d="M14 7h7v7" />
    </svg>
  );
}

function ProductVariantIcon() {
  return (
    <svg
      aria-hidden="true"
      className="mw-product-card__variant-icon"
      fill="none"
      focusable="false"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1.75"
      viewBox="0 0 24 24"
    >
      <rect height="12" rx="1.5" width="12" x="3.5" y="3.5" />
      <rect height="12" rx="1.5" width="12" x="8.5" y="8.5" />
    </svg>
  );
}

function HingedProductVariantIcon() {
  return (
    <svg
      aria-hidden="true"
      className="mw-product-card__variant-icon"
      fill="none"
      focusable="false"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1.75"
      viewBox="0 0 24 24"
    >
      <rect height="18" rx="1.25" width="7" x="3" y="3" />
      <path d="m10 4 10 4v8l-10 4z" />
      <path d="m12 9.6 5.5 2.2" />
      <path d="m12 14.2 5.5 2.2" />
    </svg>
  );
}

export function ProductCard({
  product,
  href,
  isBestSeller = false,
  isNewDesign = false,
  editorialDescription,
  bestSellerLabel = "Top ventas",
  versionLinks,
  catalogType
}: ProductCardProps) {
  const productName = product.h1_seo || product.nombre;
  const cardImages = buildProductCardImages(product);
  const hasCarousel = cardImages.length > 1;
  const cardDescription = editorialDescription?.trim();
  const description =
    cardDescription ||
    product.descripcion_seo?.trim() ||
    product.descripcion?.trim() ||
    "Modelo metálico fabricado a medida por MetalWolft.";
  const hasDiscount = Boolean(product.precio_rebajado && product.precio_rebajado > 0);
  const currentPrice = hasDiscount ? product.precio_rebajado! : product.precio;
  const badges = [
    isBestSeller
      ? {
          id: "best-seller",
          label: bestSellerLabel,
          className: "mw-product-card__badge--best-seller",
          icon: "trending-up"
        }
      : null,
    isNewDesign
      ? {
          id: "new-design",
          label: "Nuevo diseño",
          className: "mw-product-card__badge--new-design",
          icon: "sparkles"
        }
      : null
  ].filter((badge): badge is ProductBadge => badge !== null);
  const informationalVariants = [
    product.has_abatible === true
      ? { id: "hinged", label: "También abatible" }
      : null,
    product.has_door_model === true
      ? { id: "door", label: "También para puerta" }
      : null
  ].filter((variant): variant is ProductVariant => variant !== null);
  const variants: ProductVariant[] = versionLinks ?? informationalVariants;
  const accessibleDetails = [
    ...badges.map((badge) => badge.label),
    ...variants.filter((variant) => !variant.href).map((variant) => variant.label)
  ];
  const accessibleLabel = accessibleDetails.length
    ? `Ver modelo ${productName}, ${accessibleDetails.join(", ")}`
    : `Ver modelo ${productName}`;

  return (
    <article className="mw-product-card" data-product-type={catalogType}>
      <div className="mw-product-card__layout">
        <div className={`mw-product-card__media${hasCarousel ? " mw-product-card__media--carousel" : ""}`}>
          {hasCarousel ? (
            <ProductCardCarousel images={cardImages} productName={productName} href={href} />
          ) : (
            <ProductCardImage alt={productName} src={product.imagen} />
          )}
          {badges.length > 0 ? (
            <div className="mw-product-card__badges">
              {badges.map((badge) => (
                <span
                  className={`mw-product-card__badge ${badge.className}`}
                  key={badge.id}
                >
                  <ProductBadgeIcon icon={badge.icon} />
                  {badge.label}
                </span>
              ))}
            </div>
          ) : null}
        </div>
        <div className="mw-product-card__body">
          <Link className="mw-product-card__link" href={href} aria-label={accessibleLabel}>
            <h3 className="mw-product-card__title">{productName}</h3>
            <p className={`mw-product-card__description${cardDescription ? " mw-product-card__description--microcopy" : ""}`}>
              {description}
            </p>
            <div className="mw-product-card__price">
              <div className="mw-product-card__price-rates">
                {hasDiscount ? (
                  <del className="mw-product-card__price-original">
                    {formatCurrency(product.precio)} €/m²
                  </del>
                ) : null}
                <strong>{formatCurrency(currentPrice)} €/m²</strong>
              </div>
              <span className="mw-product-card__price-tax">IVA incluido</span>
            </div>
          </Link>
          {variants.length > 0 ? (
            <div className="mw-product-card__variants">
              {variants.map((variant) => {
                const content = <>
                  {variant.id === "hinged" ? (
                    <HingedProductVariantIcon />
                  ) : (
                    <ProductVariantIcon />
                  )}
                  {variant.label}
                </>;
                return variant.href ? (
                  <Link className="mw-product-card__variant mw-product-card__variant--link" href={variant.href} key={variant.id}>
                    {content}
                  </Link>
                ) : (
                  <span className="mw-product-card__variant" key={variant.id}>{content}</span>
                );
              })}
            </div>
          ) : null}
          <span className="mw-product-card__cta" aria-hidden="true">
            Ver modelo
          </span>
        </div>
      </div>
    </article>
  );
}
