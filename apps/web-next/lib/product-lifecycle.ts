export const PRODUCT_UNAVAILABLE_MESSAGE =
  "Este producto ya no está disponible para nuevos pedidos.";

export type ProductAvailability = {
  available_for_sale: boolean;
};

export function isAvailableForSale(product: ProductAvailability) {
  return product.available_for_sale === true;
}
