"use client";

import { type CSSProperties, useId, useMemo, useState } from "react";
import Link from "next/link";
import {
  DEFAULT_ANCHORAGE,
  DEFAULT_COLOR,
  type AnchorageValue,
  type ConfiguratorColorValue,
  anchorageOptions,
  colorGroups,
  getColorOption
} from "@/lib/configurator-options";
import {
  calculateConfiguratorPrice,
  formatCurrency,
  getDimensionValidationError,
  type ConfiguratorPriceQuote
} from "@/lib/configurator-pricing";

type ProductConfiguratorProps = {
  productName: string;
  pricePerM2: number;
  discountedPricePerM2?: number | null;
};

type ColorStyle = CSSProperties & {
  "--mw-configurator-color": string;
};

function normalizeDecimalInput(value: string) {
  return value.replace(",", ".");
}

function isValidQuote(
  quote: ConfiguratorPriceQuote | null
): quote is Extract<ConfiguratorPriceQuote, { ok: true }> {
  return Boolean(quote?.ok);
}

export function ProductConfigurator({
  productName,
  pricePerM2,
  discountedPricePerM2
}: ProductConfiguratorProps) {
  const [height, setHeight] = useState("");
  const [width, setWidth] = useState("");
  const [anchorage, setAnchorage] = useState<AnchorageValue>(DEFAULT_ANCHORAGE);
  const [color, setColor] = useState<ConfiguratorColorValue>(DEFAULT_COLOR);
  const [previewColor, setPreviewColor] = useState<ConfiguratorColorValue | null>(null);
  const [calculatedQuote, setCalculatedQuote] = useState<ConfiguratorPriceQuote | null>(null);
  const [calculationError, setCalculationError] = useState("");
  const [needsRecalculation, setNeedsRecalculation] = useState(false);
  const dimensionHelpId = useId();
  const dimensionErrorId = useId();

  const activeColor = getColorOption(previewColor ?? color);
  const selectedColor = getColorOption(color);
  const dimensionError = getDimensionValidationError(height, width);
  const dimensionsReadyForQuote = !dimensionError;
  const effectivePricePerM2 =
    discountedPricePerM2 && discountedPricePerM2 > 0 ? discountedPricePerM2 : pricePerM2;
  const hasDiscount = Boolean(discountedPricePerM2 && discountedPricePerM2 > 0);

  const promptMessage = needsRecalculation
    ? "Has cambiado la configuración. Vuelve a calcular el precio."
    : dimensionsReadyForQuote
      ? "Medidas listas. Calcula el precio para continuar."
      : "Introduce tus medidas y calcula el precio para ver el coste final.";

  const promptClassName = `mw-configurator-prompt${
    needsRecalculation ? " mw-configurator-prompt--warning" : dimensionsReadyForQuote ? " mw-configurator-prompt--ready" : ""
  }`;

  const previewStyle = useMemo<ColorStyle>(
    () => ({
      "--mw-configurator-color": activeColor.hex,
      backgroundColor: activeColor.hex
    }),
    [activeColor.hex]
  );

  const invalidateCalculatedPrice = () => {
    if (isValidQuote(calculatedQuote)) {
      setCalculatedQuote(null);
      setNeedsRecalculation(true);
    }
  };

  const handleCalculate = () => {
    setNeedsRecalculation(false);
    const quote = calculateConfiguratorPrice({
      rawHeight: height,
      rawWidth: width,
      pricePerM2,
      discountedPricePerM2,
      anchorage
    });

    setCalculatedQuote(quote);
    setCalculationError(quote.ok ? "" : quote.error);
  };

  return (
    <section className="mw-product-configurator" aria-label={`Configurar ${productName}`}>
      <div className="mw-configurator-price-base">
        <span>Precio:</span>
        {hasDiscount ? (
          <>
            <span className="mw-configurator-price-base__original">
              {formatCurrency(pricePerM2)} €/m²
            </span>
            <strong>{formatCurrency(effectivePricePerM2)} €/m²</strong>
          </>
        ) : (
          <strong>{formatCurrency(pricePerM2)} €/m²</strong>
        )}
      </div>

      <div className="mw-product-purchase-guide" aria-label="Cómo comprar esta reja">
        <p className="mw-product-purchase-guide__label">Cómo comprar</p>
        <div className="mw-product-purchase-guide__steps">
          <span>
            <strong>1</strong>
            Introduce medidas
          </span>
          <span>
            <strong>2</strong>
            Calcula el precio
          </span>
          <span>
            <strong>3</strong>
            Revisa la configuración
          </span>
        </div>
        <div className="mw-product-trust-badges" aria-label="Señales de confianza">
          <span>IVA incluido</span>
          <span>Fabricación a medida</span>
          <span>Ayuda por WhatsApp si la necesitas</span>
        </div>
      </div>

      <div className="mw-configurator-form" aria-live="polite">
        <div className="mw-configurator-grid mw-configurator-grid--dimensions">
          <label className="mw-configurator-field">
            <span>Alto (cm)</span>
            <input
              type="text"
              value={height}
              placeholder="Ej.: 120.1"
              inputMode="decimal"
              aria-describedby={`${dimensionHelpId}${calculationError ? ` ${dimensionErrorId}` : ""}`}
              aria-invalid={Boolean(calculationError)}
              onWheel={(event) => event.currentTarget.blur()}
              onChange={(event) => {
                invalidateCalculatedPrice();
                setCalculationError("");
                setHeight(normalizeDecimalInput(event.target.value));
              }}
            />
          </label>

          <label className="mw-configurator-field">
            <span>Ancho (cm)</span>
            <input
              type="text"
              value={width}
              inputMode="decimal"
              aria-describedby={`${dimensionHelpId}${calculationError ? ` ${dimensionErrorId}` : ""}`}
              aria-invalid={Boolean(calculationError)}
              onWheel={(event) => event.currentTarget.blur()}
              onChange={(event) => {
                invalidateCalculatedPrice();
                setCalculationError("");
                setWidth(normalizeDecimalInput(event.target.value));
              }}
            />
          </label>
        </div>

        {calculationError ? (
          <p className="mw-configurator-error" id={dimensionErrorId} role="alert">
            {calculationError}
          </p>
        ) : null}

        <p className="mw-configurator-helper" id={dimensionHelpId}>
          Introduce alto y ancho en centímetros para calcular el precio exacto de tu reja.
        </p>

        <div className="mw-configurator-help">
          <p className="mw-configurator-help__title">¿No estás seguro de las medidas?</p>
          <p>Consulta nuestra guía para medir tu ventana antes de calcular el precio.</p>
          <Link href="/medir-hueco-rejas-para-ventanas">Ver guía de medición</Link>
        </div>

        <div className="mw-configurator-grid">
          <label className="mw-configurator-field">
            <span>Instalación</span>
            <select
              value={anchorage}
              onChange={(event) => {
                invalidateCalculatedPrice();
                setCalculationError("");
                setAnchorage(event.target.value as AnchorageValue);
              }}
            >
              {anchorageOptions.map((option) => (
                <option key={option.value} value={option.value} disabled={option.disabled}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <div className="mw-configurator-selected-color">
            <span>Seleccionado:</span>
            <strong>{selectedColor.label}</strong>
            <div
              className={`mw-configurator-color-preview${
                activeColor.finish === "forja" ? " mw-configurator-color-preview--forja" : ""
              }`}
              style={previewStyle}
              aria-hidden="true"
            />
          </div>
        </div>

        <fieldset className="mw-configurator-colors">
          <legend>Color</legend>
          {colorGroups.map((group) => (
            <div className="mw-configurator-color-group" key={group.label}>
              <p>{group.label}</p>
              <div className="mw-configurator-swatches">
                {group.options.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    className={`mw-configurator-swatch${
                      option.finish === "forja" ? " mw-configurator-swatch--forja" : ""
                    }${color === option.value ? " is-selected" : ""}`}
                    style={{ "--mw-configurator-color": option.hex } as ColorStyle}
                    aria-pressed={color === option.value}
                    onMouseEnter={() => setPreviewColor(option.value)}
                    onMouseLeave={() => setPreviewColor(null)}
                    onFocus={() => setPreviewColor(option.value)}
                    onBlur={() => setPreviewColor(null)}
                    onClick={() => {
                      invalidateCalculatedPrice();
                      setCalculationError("");
                      setColor(option.value);
                    }}
                  >
                    <span className="mw-configurator-swatch__dot" aria-hidden="true" />
                    <span>{option.label}</span>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </fieldset>

        <div className="mw-configurator-calculate">
          <button className="mw-button mw-button--primary" type="button" onClick={handleCalculate}>
            Calcular precio ahora
          </button>
        </div>

        {isValidQuote(calculatedQuote) ? (
          <div className="mw-configurator-result">
            <span>Precio calculado para tus medidas</span>
            <strong>{calculatedQuote.formattedUnitPrice} €</strong>
            <p>IVA incluido para esta configuración.</p>
            {calculatedQuote.area < 1 ? (
              <p className="mw-configurator-result__warning">Área &lt; 1 m² incrementa coste.</p>
            ) : null}
          </div>
        ) : (
          <div className={promptClassName}>
            <p>{promptMessage}</p>
          </div>
        )}
      </div>
    </section>
  );
}
