import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";

export const RelatedProductsCarousel = ({ categorySlug, categoryName, currentProductId, productName }) => {
    const [relatedProducts, setRelatedProducts] = useState([]);

    useEffect(() => {
        const fetchRelatedProducts = async () => {
            try {
                const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/category/${categorySlug}/products`);
                if (!res.ok) throw new Error("Error al cargar productos relacionados.");
                const data = await res.json();

                // Filtramos el producto actual si viene por props
                const filtered = data.filter(p => p.id !== currentProductId).slice(0, 8);
                setRelatedProducts(filtered);
            } catch (err) {
                console.error(err);
            }
        };

        if (categorySlug) fetchRelatedProducts();
    }, [categorySlug, currentProductId]);

    return (
        <div className="related-carousel-wrapper">
            <h2
                className="mb-3"
                style={{
                    fontSize: '1.1rem',
                    fontWeight: '500',
                    color: '#333',
                    borderLeft: '4px solid #ff324d',
                    paddingLeft: '0.75rem',
                    marginTop: '3rem',
                }}
            >
                Otras {categoryName?.toLowerCase() || 'rejas'} similares a {productName}
            </h2>
            <div className="related-carousel">
                {relatedProducts.map(product => (
                    <Link
                        key={product.id}
                        to={`/${categorySlug}/${product.slug}`}
                        className="related-card"
                    >
                        <img
                            src={product.imagen}
                            alt={product.nombre}
                            className="related-card-image"
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
        </div>
    );
};
