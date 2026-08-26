export type DesignServiceDraftItem = {
  product_id: number;
  product_slug: string;
  product_name: string;
  width_cm: number;
  height_cm: number;
};

export type DesignServiceBuilderInput = {
  id: string;
  product_id: string;
  width_cm: string;
  height_cm: string;
};

export type DesignServiceProductOption = {
  id: number;
  slug: string;
  name: string;
};

function parsePositiveDimension(value: string) {
  const normalized = value.trim().replace(",", ".");
  if (!/^\d+(?:\.\d+)?$/.test(normalized)) {
    return null;
  }

  const parsed = Number(normalized);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

function productForId(products: readonly DesignServiceProductOption[], value: string) {
  const productId = Number(value);
  return Number.isInteger(productId) && productId > 0
    ? products.find((product) => product.id === productId) || null
    : null;
}

export function isCompleteDesignServiceBuilderInput(
  input: DesignServiceBuilderInput,
  products: readonly DesignServiceProductOption[]
) {
  return Boolean(
    productForId(products, input.product_id) &&
      parsePositiveDimension(input.width_cm) !== null &&
      parsePositiveDimension(input.height_cm) !== null
  );
}

export function builderInputsToDraftItems(
  inputs: readonly DesignServiceBuilderInput[],
  products: readonly DesignServiceProductOption[]
) {
  const completeItems: DesignServiceDraftItem[] = [];
  const duplicateInputIds = new Set<string>();
  const seen = new Set<string>();

  for (const input of inputs) {
    const product = productForId(products, input.product_id);
    const width_cm = parsePositiveDimension(input.width_cm);
    const height_cm = parsePositiveDimension(input.height_cm);
    if (!product || width_cm === null || height_cm === null) {
      continue;
    }

    const item: DesignServiceDraftItem = {
      product_id: product.id,
      product_slug: product.slug,
      product_name: product.name,
      width_cm,
      height_cm
    };
    const key = `${item.product_id}:${item.width_cm}:${item.height_cm}`;
    if (seen.has(key)) {
      duplicateInputIds.add(input.id);
      continue;
    }

    seen.add(key);
    completeItems.push(item);
  }

  return {
    items: completeItems,
    duplicateInputIds
  };
}

export function draftItemToBuilderInput(item: DesignServiceDraftItem, id: string): DesignServiceBuilderInput {
  return {
    id,
    product_id: String(item.product_id),
    width_cm: String(item.width_cm),
    height_cm: String(item.height_cm)
  };
}
