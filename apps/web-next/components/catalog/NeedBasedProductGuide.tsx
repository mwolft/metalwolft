"use client";

import Link from "next/link";

const OPTIONS = [
  {
    title: "No necesito abrirla",
    description: "Si buscas una protección permanente, una reja fija puede ser la opción adecuada.",
    action: "Ver rejas fijas →",
  },
  {
    title: "Necesito poder abrirla",
    description: "Si necesitas abrir la reja para acceder a la ventana, puedes elegir uno de nuestros modelos abatibles.",
    action: "Ver rejas abatibles →",
    href: "/rejas-para-ventanas/abatibles",
  },
  {
    title: "Quiero evitar obra",
    description: "Si prefieres una instalación sin obra, disponemos de una solución específica para este tipo de montaje.",
    action: "Ver solución sin obra →",
    href: "/rejas-para-ventanas-sin-obra",
  },
  {
    title: "Quiero proteger a mi mascota",
    description: "Si tienes gatos u otras mascotas, disponemos de una reja diseñada específicamente para esta necesidad.",
    action: "Ver reja para mascotas →",
    href: "/rejas-para-ventanas/reja-mascotas-ohio",
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

export function NeedBasedProductGuide({ onSelectFixed }: { onSelectFixed: () => void }) {
  return (
    <section className="mw-need-guide" aria-labelledby="mw-need-guide-title">
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
    </section>
  );
}
