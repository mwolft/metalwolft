export const PRODUCT_UNAVAILABLE_MESSAGE =
    "Este producto ya no está disponible para nuevos pedidos.";

export const isAvailableForSale = (product) =>
    product?.available_for_sale === true;
