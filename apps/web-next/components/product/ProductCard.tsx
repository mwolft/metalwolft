import Link from "next/link";
import { ProductCardImage } from "@/components/product/ProductCardImage";
import type { ApiProduct } from "@/lib/api";

type ProductCardProps = {
  product: ApiProduct;
  href: string;
};

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
          <ProductCardImage alt={productName} src={product.imagen} />
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
