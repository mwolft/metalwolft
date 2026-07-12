import {
  ANCHORAGE_METAL_CLAWS,
  type AnchorageValue,
  getAnchorageOption
} from "./configurator-options";

export type ConfiguratorPriceInput = {
  rawHeight: string;
  rawWidth: string;
  pricePerM2: number;
  discountedPricePerM2?: number | null;
  anchorage: AnchorageValue;
};

export type ConfiguratorPriceQuote =
  | {
      ok: true;
      height: number;
      width: number;
      area: number;
      pricePerM2Used: number;
      baseUnitPrice: number;
      anchorageSupplement: number;
      unitPrice: number;
      formattedUnitPrice: string;
    }
  | {
      ok: false;
      error: string;
    };

function parseDimension(value: string) {
  const normalized = value.trim().replace(",", ".");
  if (!normalized) {
    return null;
  }

  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : null;
}

export function formatCurrency(value: number) {
  return new Intl.NumberFormat("es-ES", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value);
}

export function roundCurrency(value: number) {
  return Math.round((value + Number.EPSILON) * 100) / 100;
}

export function getDimensionValidationError(rawHeight: string, rawWidth: string) {
  const height = parseDimension(rawHeight);
  const width = parseDimension(rawWidth);

  if (height === null || width === null) {
    return "Introduce alto y ancho válidos en centímetros.";
  }

  if (height < 30 || width < 30) {
    return "El alto y el ancho deben ser de al menos 30 cm.";
  }

  if (height > 250 || width > 250) {
    return "El alto y el ancho no pueden superar 250 cm.";
  }

  if (height + width > 400) {
    return "La suma de alto y ancho no puede superar 400 cm.";
  }

  return "";
}

export function calculateConfiguratorPrice(input: ConfiguratorPriceInput): ConfiguratorPriceQuote {
  const dimensionError = getDimensionValidationError(input.rawHeight, input.rawWidth);
  if (dimensionError) {
    return { ok: false, error: dimensionError };
  }

  if (input.anchorage === ANCHORAGE_METAL_CLAWS) {
    return { ok: false, error: "Esta opción de instalación no está disponible actualmente." };
  }

  const anchorageOption = getAnchorageOption(input.anchorage);
  if (anchorageOption.disabled) {
    return { ok: false, error: "Esta opción de instalación no está disponible actualmente." };
  }

  const height = parseDimension(input.rawHeight) as number;
  const width = parseDimension(input.rawWidth) as number;
  const pricePerM2Used =
    input.discountedPricePerM2 && input.discountedPricePerM2 > 0
      ? input.discountedPricePerM2
      : input.pricePerM2;
  const area = (height * width) / 10000;
  const multiplier =
    area >= 0.9
      ? 1
      : area >= 0.8
        ? 1.1
        : area >= 0.7
          ? 1.15
          : area >= 0.6
            ? 1.2
            : area >= 0.5
              ? 1.3
              : area >= 0.4
                ? 1.55
                : area >= 0.3
                  ? 1.9
                  : area >= 0.2
                    ? 2.5
                    : 3;

  const baseUnitPrice = roundCurrency(Math.max(area * pricePerM2Used * multiplier, 95));
  const unitPrice = roundCurrency(baseUnitPrice + anchorageOption.supplement);

  return {
    ok: true,
    height,
    width,
    area,
    pricePerM2Used,
    baseUnitPrice,
    anchorageSupplement: anchorageOption.supplement,
    unitPrice,
    formattedUnitPrice: formatCurrency(unitPrice)
  };
}
