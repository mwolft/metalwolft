export const ANCHORAGE_INTERIOR_HOLES = "Sin obra: con agujeros interiores";
export const ANCHORAGE_FRONT_PLATES = "Sin obra: con pletinas";
export const ANCHORAGE_METAL_CLAWS = "Con obra: con garras metálicas";

export const DEFAULT_ANCHORAGE = ANCHORAGE_INTERIOR_HOLES;
export const DEFAULT_COLOR = "satinado_blanco";

export type AnchorageValue =
  | typeof ANCHORAGE_INTERIOR_HOLES
  | typeof ANCHORAGE_FRONT_PLATES
  | typeof ANCHORAGE_METAL_CLAWS;

export type ConfiguratorColorValue =
  | "satinado_blanco"
  | "satinado_negro"
  | "satinado_gris"
  | "satinado_verde"
  | "forja_negro"
  | "forja_gris"
  | "forja_marron"
  | "forja_azul"
  | "forja_verde"
  | "forja_dorado";

export type AnchorageOption = {
  value: AnchorageValue;
  label: string;
  supplement: number;
  disabled?: boolean;
};

export type ConfiguratorColorOption = {
  value: ConfiguratorColorValue;
  label: string;
  hex: string;
  finish: "satinado" | "forja";
};

export const anchorageOptions: AnchorageOption[] = [
  {
    value: ANCHORAGE_INTERIOR_HOLES,
    label: ANCHORAGE_INTERIOR_HOLES,
    supplement: 0
  },
  {
    value: ANCHORAGE_FRONT_PLATES,
    label: "Sin obra: con pletinas (+24,95 €)",
    supplement: 24.95
  },
  {
    value: ANCHORAGE_METAL_CLAWS,
    label: "Con obra: con garras metálicas (no disponible)",
    supplement: 39.95,
    disabled: true
  }
];

export const colorGroups: Array<{
  label: string;
  options: ConfiguratorColorOption[];
}> = [
  {
    label: "Satinado liso",
    options: [
      { value: "satinado_blanco", label: "Blanco liso", hex: "#ffffff", finish: "satinado" },
      { value: "satinado_negro", label: "Negro liso", hex: "#000000", finish: "satinado" },
      { value: "satinado_gris", label: "Gris medio liso", hex: "#494949", finish: "satinado" },
      { value: "satinado_verde", label: "Verde carruajes liso", hex: "#183022", finish: "satinado" }
    ]
  },
  {
    label: "Efecto forja",
    options: [
      { value: "forja_negro", label: "Negro forja", hex: "#1a1a1a", finish: "forja" },
      { value: "forja_gris", label: "Gris acero forja", hex: "#7a7d80", finish: "forja" },
      { value: "forja_marron", label: "Marrón castaño forja", hex: "#5a3a2a", finish: "forja" },
      { value: "forja_azul", label: "Azul forja", hex: "#2e4579", finish: "forja" },
      { value: "forja_verde", label: "Verde bronce forja", hex: "#506c39", finish: "forja" },
      { value: "forja_dorado", label: "Dorado forja", hex: "#947d30", finish: "forja" }
    ]
  }
];

export const colorOptions = colorGroups.flatMap((group) => group.options);

export function getAnchorageOption(value: AnchorageValue) {
  return anchorageOptions.find((option) => option.value === value) ?? anchorageOptions[0];
}

export function getColorOption(value: ConfiguratorColorValue) {
  return colorOptions.find((option) => option.value === value) ?? colorOptions[0];
}
