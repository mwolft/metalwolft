class ProductNotAvailableForSaleError(ValueError):
    pass


def ensure_product_available_for_sale(product):
    if not product.available_for_sale:
        raise ProductNotAvailableForSaleError(
            "Este producto ya no esta disponible para la venta."
        )
    return product


def publicly_discoverable_products_query():
    from api.models import Products

    return Products.query.filter(
        Products.published.is_(True),
        Products.available_for_sale.is_(True),
    )


def publicly_accessible_products_query():
    from api.models import Products

    return Products.query.filter(Products.published.is_(True))
