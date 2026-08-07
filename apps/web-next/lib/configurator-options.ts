import fallbackConfiguration from "./configurator-configuration-fallback.json";
import type { ProductConfigurationResponse } from "./product-configuration-client";

export type AnchorageValue = string;
export type ConfiguratorColorValue = string;
export type ScrewOptionValue = string;

type ColorVisual = {
  hex: string;
  swatchClass?: "forja";
};

const DEFAULT_COLOR_VISUAL: ColorVisual = { hex: "#d1d5db" };

// The normal flow gets commercial metadata from Flask; this map only controls presentation.
const COLOR_VISUALS: Record<string, ColorVisual> = {
  satinado_blanco: { hex: "#ffffff" },
  satinado_negro: { hex: "#000000" },
  satinado_gris: { hex: "#494949" },
  satinado_verde: { hex: "#183022" },
  forja_negro: { hex: "#1a1a1a", swatchClass: "forja" },
  forja_gris: { hex: "#7a7d80", swatchClass: "forja" },
  forja_marron: { hex: "#5a3a2a", swatchClass: "forja" },
  forja_azul: { hex: "#2e4579", swatchClass: "forja" },
  forja_verde: { hex: "#506c39", swatchClass: "forja" },
  forja_dorado: { hex: "#947d30", swatchClass: "forja" }
};

const fallback = fallbackConfiguration as ProductConfigurationResponse;

// This snapshot is reserved for the explicit network-error compatibility path.
export const ANCHORAGE_INTERIOR_HOLES = fallback.anchorages[0].value;
export const ANCHORAGE_FRONT_PLATES = fallback.anchorages[1].value;
export const ANCHORAGE_METAL_CLAWS = fallback.anchorages[2].value;
export const LOCAL_CONFIGURATOR_DIMENSIONS = fallback.dimensions;

export function buildLocalProductConfiguration(productId: number): ProductConfigurationResponse {
  return { ...fallback, product_id: productId };
}

export function getFallbackAnchorage(value: AnchorageValue) {
  return fallback.anchorages.find((option) => option.value === value);
}

export function getColorVisual(value: ConfiguratorColorValue) {
  return COLOR_VISUALS[value] ?? DEFAULT_COLOR_VISUAL;
}
