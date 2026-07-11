export type NavigationLink = {
  href: string;
  label: string;
  matchPaths?: string[];
  matchPrefixes?: string[];
  allowAriaCurrent?: boolean;
};

export const primaryNavigationLinks: NavigationLink[] = [
  {
    href: "/rejas-para-ventanas",
    label: "Rejas para ventanas",
    matchPaths: ["/rejas-para-ventanas"],
    matchPrefixes: ["/rejas-para-ventanas/"]
  },
  {
    href: "/#modelos-destacados",
    label: "Modelos",
    matchPaths: ["/"],
    allowAriaCurrent: false
  },
  {
    href: "/blogs",
    label: "Guías",
    matchPaths: [
      "/blogs",
      "/medir-hueco-rejas-para-ventanas",
      "/instalation-rejas-para-ventanas",
      "/rejas-para-ventanas-sin-obra",
      "/rejas-para-ventanas-modernas"
    ]
  },
  {
    href: "/contact",
    label: "Contacto",
    matchPaths: ["/contact"]
  }
];

export const headerPrimaryCta = {
  href: "/rejas-para-ventanas",
  label: "Ver catálogo",
  mobileLabel: "Catálogo"
} as const;

export const footerCatalogLinks: NavigationLink[] = [
  {
    href: "/rejas-para-ventanas",
    label: "Catálogo de rejas"
  },
  {
    href: "/#modelos-destacados",
    label: "Modelos destacados"
  },
  {
    href: "/rejas-para-ventanas-sin-obra",
    label: "Rejas sin obra"
  },
  {
    href: "/rejas-para-ventanas-modernas",
    label: "Rejas modernas"
  }
];

export const footerGuideLinks: NavigationLink[] = [
  {
    href: "/blogs",
    label: "Todas las guías"
  },
  {
    href: "/medir-hueco-rejas-para-ventanas",
    label: "Cómo medir el hueco"
  },
  {
    href: "/instalation-rejas-para-ventanas",
    label: "Instalación sin obra"
  }
];

export function isNavigationLinkActive(link: NavigationLink, pathname: string | null) {
  if (!pathname) {
    return false;
  }

  if (link.matchPaths?.includes(pathname)) {
    return true;
  }

  return (link.matchPrefixes || []).some((prefix) => pathname.startsWith(prefix));
}
