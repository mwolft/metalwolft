import Image from "next/image";
import Link from "next/link";
import type { ApiProduct } from "@/lib/api";

type ProductCardProps = {
  product: ApiProduct;
  href: string;
};

const PRODUCT_IMAGE_SIZES =
  "(min-width: 1200px) 340px, (min-width: 900px) 29vw, (min-width: 620px) 44vw, calc(100vw - 5rem)";

export function ProductCard({ product, href }: ProductCardProps) {
  const productName = product.h1_seo || product.nombre;
  const description =
    product.descripcion_seo?.trim() ||
    product.descripcion?.trim() ||
    "Modelo metálico fabricado a medida por MetalWolft.";

  return (
    <article className="mw-product-card">
      <Link
        className="mw-product-card__link"
        href={href}
        aria-label={`Ver modelo ${productName}`}
      >
        <div className="mw-product-card__media">
          {product.imagen ? (
            <Image
              src={product.imagen}
              alt={productName}
              fill
              sizes={PRODUCT_IMAGE_SIZES}
            />
          ) : (
            <span className="mw-product-card__image-fallback">Imagen no disponible</span>
          )}
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
