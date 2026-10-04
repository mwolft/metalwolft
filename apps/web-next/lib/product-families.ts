export type ProductVersion = "fixed" | "hinged" | "door";

type ProductFamily = {
  name: string;
  versions: Partial<Record<ProductVersion, string>>;
};

export const PRODUCT_VERSION_LABELS: Record<ProductVersion, string> = {
  fixed: "Fija",
  hinged: "Abatible",
  door: "Para puerta",
};

const PRODUCT_VERSION_ORDER: ProductVersion[] = ["fixed", "hinged", "door"];

const PRODUCT_FAMILIES: ProductFamily[] = [
  { name: "Albany", versions: { fixed: "reja-fija-albany", hinged: "reja-abatible-albany", door: "reja-puerta-albany" } },
  { name: "Cortland", versions: { fixed: "reja-fija-cortland", hinged: "reja-abatible-cortland", door: "reja-puerta-cortland" } },
  { name: "Maryland", versions: { fixed: "reja-fija-maryland", hinged: "reja-abatible-maryland-para-ventanas", door: "reja-puerta-maryland" } },
  { name: "Essex", versions: { fixed: "reja-fija-essex", hinged: "reja-abatible-essex" } },
  { name: "Idaho", versions: { fixed: "reja-fija-idaho", hinged: "reja-abatible-idaho" } },
];

export function getProductFamily(slug: string) {
  for (const family of PRODUCT_FAMILIES) {
    const currentVersion = PRODUCT_VERSION_ORDER.find((version) => family.versions[version] === slug);
    if (currentVersion) {
      return {
        name: family.name,
        currentVersion,
        versions: PRODUCT_VERSION_ORDER.flatMap((version) => {
          const versionSlug = family.versions[version];
          return versionSlug
            ? [{ version, slug: versionSlug, label: PRODUCT_VERSION_LABELS[version], href: `/rejas-para-ventanas/${versionSlug}` }]
            : [];
        }),
      };
    }
  }

  return null;
}

export function getProductAlternativeLinks(slug: string) {
  const family = getProductFamily(slug);
  return family?.versions
    .filter(({ version }) => version !== family.currentVersion)
    .map(({ version, href }) => ({
      id: version,
      href,
      label: version === "fixed" ? "También fija" : version === "hinged" ? "También abatible" : "También para puerta",
    }));
}
