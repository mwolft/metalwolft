export type ProductCardEditorialContent = {
  description: string;
  bestSellerLabel?: "Más vendida" | "Top ventas";
};

const PRODUCT_CARD_CONTENT: Record<string, ProductCardEditorialContent> = {
  "reja-fija-albany": { description: "Líneas horizontales · Estilo moderno", bestSellerLabel: "Más vendida" },
  "reja-fija-luton": { description: "Líneas diagonales · Diseño llamativo" },
  "reja-fija-idaho": { description: "Líneas horizontales · Acabado robusto", bestSellerLabel: "Top ventas" },
  "reja-fija-dakota": { description: "Diseño vertical · Sin bastidor" },
  "reja-fija-essex": { description: "Líneas verticales · Estilo clásico", bestSellerLabel: "Top ventas" },
  "reja-fija-cortland": { description: "Horizontales con detalles verticales" },
  "reja-fija-erie": { description: "Líneas horizontales · Refuerzo central" },
  "reja-fija-genesee": { description: "Horizontales · Refuerzos en las esquinas" },
  "reja-fija-livingston": { description: "Pletinas dobles horizontales" },
  "reja-fija-virginia": { description: "Líneas horizontales · Diseño sencillo" },
  "reja-fija-maryland": { description: "Líneas horizontales · Perfil cuadrado" },
  "reja-fija-clasica-charleston": { description: "Barrotes verticales · Detalles ornamentales" },
  "reja-fija-ithaca": { description: "Entramado diagonal en rombos" },
  "reja-fija-orleans-clasica": { description: "Diseño ornamental · Refuerzo central" },
  "reja-fija-vermont": { description: "Verticales con dos refuerzos horizontales" },
  "reja-fija-pittsburgh": { description: "Horizontales · Refuerzos en las esquinas" },
  "reja-mascotas-ohio": { description: "Separación reducida · Especial para mascotas" },
  "reja-abatible-maryland-para-ventanas": { description: "Apertura abatible · Diseño horizontal" },
  "reja-abatible-cortland": { description: "Apertura abatible · Diseño mixto" },
  "reja-abatible-albany": { description: "Apertura abatible · Líneas horizontales" },
  "reja-abatible-essex": { description: "Apertura abatible · Líneas verticales" },
  "reja-abatible-idaho": { description: "Tubos cuadrados · Verticales alternas" },
  "reja-puerta-albany": { description: "Para puertas · Líneas horizontales" },
  "reja-puerta-cortland": { description: "Para puertas · Diseño reforzado" },
  "reja-puerta-maryland": { description: "Para puertas · Perfil cuadrado" },
};

export function getProductCardContent(slug: string): ProductCardEditorialContent | undefined {
  return PRODUCT_CARD_CONTENT[slug];
}
