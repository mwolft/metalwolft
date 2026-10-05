"use client";

import Link from "next/link";
import { useShowFixedProducts } from "@/components/catalog/CatalogTypeNavigation";

const OPTIONS = [
  {
    title: "No necesito abrirla",
    description: "Protección permanente para tu ventana.",
    action: "Ver rejas fijas →",
  },
  {
    title: "Necesito poder abrirla",
    description: "Apertura para acceder a la ventana.",
    action: "Ver rejas abatibles →",
    href: "/rejas-para-ventanas/abatibles",
  },
  {
    title: "Quiero evitar obra",
    description: "Solución con instalación sin obra.",
    action: "Ver solución sin obra →",
    href: "/rejas-para-ventanas-sin-obra",
  },
] as const;

function OptionContent({ option }: { option: (typeof OPTIONS)[number] }) {
  return (
    <>
      <span className="mw-need-guide__option-title">{option.title}</span>
      <span className="mw-need-guide__option-description">{option.description}</span>
      <span className="mw-need-guide__option-action">{option.action}</span>
    </>
  );
}

export function NeedBasedProductGuide() {
  const onSelectFixed = useShowFixedProducts();

  return (
    <aside className="mw-panel mw-need-guide" aria-labelledby="mw-need-guide-title">
      <h2 id="mw-need-guide-title">¿Qué tipo de reja necesito?</h2>
      <p>Cada ventana y cada uso pueden necesitar una solución diferente. Elige tu caso y te ayudamos a encontrar la opción adecuada.</p>
      <ul className="mw-need-guide__grid">
        {OPTIONS.map((option) => (
          <li key={option.title}>
            {"href" in option ? (
              <Link className="mw-need-guide__option" href={option.href}>
                <OptionContent option={option} />
              </Link>
            ) : (
              <button className="mw-need-guide__option" type="button" aria-controls="catalog-product-grid" onClick={onSelectFixed}>
                <OptionContent option={option} />
              </button>
            )}
          </li>
        ))}
      </ul>
    </aside>
  );
}
