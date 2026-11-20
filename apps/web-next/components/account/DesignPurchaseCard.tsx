"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { type CustomerDesignPurchaseItem } from "@/lib/customer-orders-client";
import { isDesignPurchaseSeed, saveDesignPurchaseSeed } from "@/lib/design-purchase-seed";

export function DesignPurchaseCard({ item }: { item: CustomerDesignPurchaseItem }) {
  const router = useRouter();
  const [storageError, setStorageError] = useState(false);
  const product = item.product;
  const seed = product ? {
    categorySlug: product.category_slug,
    productSlug: product.slug,
    heightCm: item.height_cm ?? "",
    widthCm: item.width_cm ?? ""
  } : null;
  const canContinue = Boolean(product?.available_for_sale && seed && isDesignPurchaseSeed(seed));

  function continueToProduct() {
    if (!seed || !saveDesignPurchaseSeed(seed)) {
      setStorageError(true);
      return;
    }
    setStorageError(false);
    router.push(`/${seed.categorySlug}/${seed.productSlug}?desde_diseno=1`);
  }

  return (
    <div className="mw-design-purchase">
      <h5>Haz realidad tu diseño</h5>
      {canContinue ? (
        <>
          <p>Ya tenemos tu modelo y tus medidas. Solo tienes que elegir el acabado y completar la configuración de tu reja.</p>
          <button className="mw-button mw-button--primary" type="button" onClick={continueToProduct}>Comprar esta reja</button>
          {storageError ? <p role="alert">No pudimos preparar tus medidas en este navegador. Comprueba que el almacenamiento de sesión esté disponible.</p> : null}
          <small>Podrás consultar el precio antes de realizar la compra.</small>
        </>
      ) : (
        <p>{!product || !product.available_for_sale
          ? "Este modelo no está disponible para comprar online. Contacta con MetalWolft si quieres consultarnos."
          : "Estas medidas no pueden precargarse. Contacta con MetalWolft para revisar tu diseño."}</p>
      )}
    </div>
  );
}
