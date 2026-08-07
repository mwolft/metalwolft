export type LegalLink = {
  href: string;
  label: string;
};

export const legalFooterLinks: LegalLink[] = [
  { href: "/politica-privacidad", label: "Política de privacidad" },
  { href: "/politica-cookies", label: "Política de cookies" },
  { href: "/politica-devolucion", label: "Política de devoluciones" },
  { href: "/cambios-politica-cookies", label: "Cambios en la política de cookies" },
  { href: "/license", label: "Licencia de imágenes" }
];

export function buildLegalRelatedLinks(currentPath: string): LegalLink[] {
  return [
    ...legalFooterLinks.filter((link) => link.href !== currentPath),
    { href: "/contact", label: "Contacto" }
  ];
}
