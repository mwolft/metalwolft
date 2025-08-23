import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";

export const RelatedProductsCarousel = ({
  categorySlug,       // obligatorio en Home si quieres forzar una categoría
  categoryName,       // opcional, para título dinámico
  currentProductId,   // opcional, se usa en PDP para excluir el producto actual
  productName,        // opcional, se usa en PDP para personalizar título
  title,              // opcional, título fijo (por ej. "Rejas para ventanas destacadas")
  limit               // opcional, recorte de nº de productos
}) => {
  const [relatedProducts, setRelatedProducts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const apiBaseUrl = process.env.REACT_APP_BACKEND_URL
    ? process.env.REACT_APP_BACKEND_URL
    : process.env.NODE_ENV === "production"
      ? "https://api.metalwolft.com"
      : "https://fuzzy-space-eureka-7v7jw6jv7v5jhp945-3001.app.github.dev/";

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        setIsLoading(true);
        const res = await fetch(`${apiBaseUrl}/api/category/${categorySlug}/products`);
        if (!res.ok) throw new Error("Error al cargar productos relacionados.");
        const data = await res.json();

        let list = currentProductId
          ? data.filter((p) => p.id !== currentProductId)
          : data;

        if (limit) list = list.slice(0, limit);

        setRelatedProducts(list);
      } catch (err) {
        console.error(err);
        setRelatedProducts([]);
      } finally {
        setIsLoading(false);
      }
    };

    if (categorySlug) fetchProducts();
  }, [categorySlug, currentProductId, limit]);

  const heading = title
    ? title
    : `Otras ${categoryName?.toLowerCase() || "rejas"} similares a ${productName || ""}`.trim();

  const buildProductLink = (p) => `/${categorySlug}/${p.slug}`;

  if (!categorySlug) return null;

  return (
    <div className="related-carousel-wrapper">
      <h2
        className="mb-3"
        style={{
          fontSize: "1.2rem",
          fontFamily: "Roboto, sans-serif",
          fontStyle:  "normal",
          fontWeight: "500",
          color: "#333",
          borderLeft: "4px solid #ff324d",
          paddingLeft: "0.75rem",
          marginTop: "1rem",
        }}
      >
        {heading}
      </h2>

      {isLoading ? (
        <div className="related-carousel-skeleton">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="related-card skeleton" />
          ))}
        </div>
      ) : relatedProducts.length === 0 ? (
        <p style={{ color: "#666" }}>No hay productos para mostrar ahora mismo.</p>
      ) : (
        <div className="related-carousel">
          {relatedProducts.map((product) => (
            <Link
              key={product.id}
              to={buildProductLink(product)}
              className="related-card"
            >
              <img
                src={product.imagen}
                alt={product.nombre}
                className="related-card-image"
                loading="lazy"
              />
              <div className="related-card-info">
                <p className="related-card-title">{product.nombre}</p>
                {product.precio_rebajado ? (
                  <p className="related-card-price">
                    <span className="original">{product.precio} €</span>
                    <span className="rebajado"> {product.precio_rebajado} €</span>
                  </p>
                ) : (
                  <p className="related-card-price">{product.precio} €</p>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};
