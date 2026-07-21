"use client";

import { type CSSProperties, useEffect, useId, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { clearSession, getToken } from "@/lib/auth-client";
import {
  type CartItem,
  CartClientError,
  addCartItem,
  getCart,
  isSessionError,
  updateCartItemQuantity
} from "@/lib/cart-client";
import {
  DEFAULT_ANCHORAGE,
  DEFAULT_COLOR,
  type AnchorageValue,
  type ConfiguratorColorValue,
  anchorageOptions,
  colorOptions,
  colorGroups,
  getColorOption
} from "@/lib/configurator-options";
import {
  calculateConfiguratorPrice,
  formatCurrency,
  getDimensionValidationError,
  type ConfiguratorPriceQuote
} from "@/lib/configurator-pricing";
import {
  PRODUCT_UNAVAILABLE_MESSAGE,
  isAvailableForSale
} from "@/lib/product-lifecycle";

type ProductConfiguratorProps = {
  productId: number;
  categorySlug: string;
  productSlug: string;
  productName: string;
  pricePerM2: number;
  discountedPricePerM2?: number | null;
  availableForSale: boolean;
};

const PENDING_PRODUCT_CONFIG_STORAGE_KEY = "mw_pending_product_config";

type ColorStyle = CSSProperties & {
  "--mw-configurator-color": string;
};

type PendingProductConfig = {
  productId: number;
  categorySlug: string;
  productSlug: string;
  alto: number;
  ancho: number;
  anclaje: AnchorageValue;
  color: ConfiguratorColorValue;
};

type LegacyPendingProductConfig = {
  productId?: unknown;
  product_id?: unknown;
  categorySlug?: unknown;
  category_slug?: unknown;
  productSlug?: unknown;
  product_slug?: unknown;
  alto?: unknown;
  ancho?: unknown;
  height?: unknown;
  width?: unknown;
  anclaje?: unknown;
  mounting?: unknown;
  color?: unknown;
};

function normalizeDecimalInput(value: string) {
  return value.replace(",", ".");
}

function isValidQuote(
  quote: ConfiguratorPriceQuote | null
): quote is Extract<ConfiguratorPriceQuote, { ok: true }> {
  return Boolean(quote?.ok);
}

function isAnchorageValue(value: unknown): value is AnchorageValue {
  return typeof value === "string" && anchorageOptions.some((option) => option.value === value);
}

function isColorValue(value: unknown): value is ConfiguratorColorValue {
  return typeof value === "string" && colorOptions.some((option) => option.value === value);
}

function normalizePendingNumber(value: unknown) {
  const parsed = Number(typeof value === "string" ? normalizeDecimalInput(value) : value);
  return Number.isFinite(parsed) ? parsed : null;
}

function readPendingProductConfig(
  productId: number,
  categorySlug: string,
  productSlug: string
): PendingProductConfig | null {
  const rawPendingConfig = window.sessionStorage.getItem(PENDING_PRODUCT_CONFIG_STORAGE_KEY);
  if (!rawPendingConfig) {
    return null;
  }

  try {
    const parsed = JSON.parse(rawPendingConfig) as LegacyPendingProductConfig;
    const pendingProductId = Number(parsed.productId ?? parsed.product_id ?? productId);
    const pendingCategorySlug = parsed.categorySlug ?? parsed.category_slug;
    const pendingProductSlug = parsed.productSlug ?? parsed.product_slug;
    const alto = normalizePendingNumber(parsed.alto ?? parsed.height);
    const ancho = normalizePendingNumber(parsed.ancho ?? parsed.width);
    const anclaje = parsed.anclaje ?? parsed.mounting;
    const pendingColor = parsed.color;

    if (
      pendingProductId !== productId ||
      pendingCategorySlug !== categorySlug ||
      pendingProductSlug !== productSlug ||
      alto === null ||
      ancho === null ||
      !isAnchorageValue(anclaje) ||
      !isColorValue(pendingColor)
    ) {
      return null;
    }

    return {
      productId,
      categorySlug,
      productSlug,
      alto,
      ancho,
      anclaje,
      color: pendingColor
    };
  } catch {
    window.sessionStorage.removeItem(PENDING_PRODUCT_CONFIG_STORAGE_KEY);
    return null;
  }
}

function savePendingProductConfig(config: PendingProductConfig) {
  window.sessionStorage.setItem(PENDING_PRODUCT_CONFIG_STORAGE_KEY, JSON.stringify(config));
}

function sameDimension(storedValue: number | null, configuredValue: number) {
  return typeof storedValue === "number" && Math.abs(storedValue - configuredValue) < 0.001;
}

export function ProductConfigurator({
  productId,
  categorySlug,
  productSlug,
  productName,
  pricePerM2,
  discountedPricePerM2,
  availableForSale
}: ProductConfiguratorProps) {
  const router = useRouter();
  const [height, setHeight] = useState("");
  const [width, setWidth] = useState("");
  const [anchorage, setAnchorage] = useState<AnchorageValue>(DEFAULT_ANCHORAGE);
  const [color, setColor] = useState<ConfiguratorColorValue>(DEFAULT_COLOR);
  const [previewColor, setPreviewColor] = useState<ConfiguratorColorValue | null>(null);
  const [calculatedQuote, setCalculatedQuote] = useState<ConfiguratorPriceQuote | null>(null);
  const [calculationError, setCalculationError] = useState("");
  const [needsRecalculation, setNeedsRecalculation] = useState(false);
  const [cartStatus, setCartStatus] = useState<"idle" | "adding" | "success" | "error">("idle");
  const [cartFeedback, setCartFeedback] = useState("");
  const dimensionHelpId = useId();
  const dimensionErrorId = useId();
  const cartFeedbackId = useId();

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
  const productPath = `/${categorySlug}/${productSlug}`;
  const canAddToCart =
    availableForSale && isValidQuote(calculatedQuote) && !needsRecalculation;
  const isAddingToCart = cartStatus === "adding";

  const previewStyle = useMemo<ColorStyle>(
    () => ({
      "--mw-configurator-color": activeColor.hex,
      backgroundColor: activeColor.hex
    }),
    [activeColor.hex]
  );

  useEffect(() => {
    const pendingConfig = readPendingProductConfig(productId, categorySlug, productSlug);
    if (!pendingConfig) {
      return;
    }

    const restoredHeight = String(pendingConfig.alto);
    const restoredWidth = String(pendingConfig.ancho);
    const restoredQuote = calculateConfiguratorPrice({
      rawHeight: restoredHeight,
      rawWidth: restoredWidth,
      pricePerM2,
      discountedPricePerM2,
      anchorage: pendingConfig.anclaje
    });

    setHeight(restoredHeight);
    setWidth(restoredWidth);
    setAnchorage(pendingConfig.anclaje);
    setColor(pendingConfig.color);
    setCalculatedQuote(restoredQuote);
    setCalculationError(restoredQuote.ok ? "" : restoredQuote.error);
    setNeedsRecalculation(false);
    setCartStatus("idle");
    setCartFeedback(
      restoredQuote.ok
        ? "Configuración restaurada. Ya puedes añadirla al carrito."
        : "Revisa la configuración restaurada antes de añadirla al carrito."
    );
    window.sessionStorage.removeItem(PENDING_PRODUCT_CONFIG_STORAGE_KEY);
  }, [categorySlug, discountedPricePerM2, pricePerM2, productId, productSlug]);

  const invalidateCalculatedPrice = () => {
    setCartStatus("idle");
    setCartFeedback("");

    if (isValidQuote(calculatedQuote)) {
      setCalculatedQuote(null);
      setNeedsRecalculation(true);
    }
  };

  const handleCalculate = () => {
    if (!availableForSale) {
      return;
    }

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
    setCartStatus("idle");
    setCartFeedback("");
  };

  const buildPendingConfig = (
    quote: Extract<ConfiguratorPriceQuote, { ok: true }>
  ): PendingProductConfig => ({
    productId,
    categorySlug,
    productSlug,
    alto: quote.height,
    ancho: quote.width,
    anclaje: anchorage,
    color
  });

  const saveCurrentConfigAndLogin = (quote: Extract<ConfiguratorPriceQuote, { ok: true }>) => {
    savePendingProductConfig(buildPendingConfig(quote));
    router.push(`/login?next=${encodeURIComponent(productPath)}`);
  };

  const findExistingCartItem = (
    items: CartItem[],
    quote: Extract<ConfiguratorPriceQuote, { ok: true }>
  ) =>
    items.find(
      (item) =>
        item.producto_id === productId &&
        sameDimension(item.alto, quote.height) &&
        sameDimension(item.ancho, quote.width) &&
        item.anclaje === anchorage &&
        item.color === color
    );

  const handleAddToCart = async () => {
    if (!isAvailableForSale({ available_for_sale: availableForSale })) {
      setCartStatus("error");
      setCartFeedback(PRODUCT_UNAVAILABLE_MESSAGE);
      return;
    }

    if (!canAddToCart || isAddingToCart) {
      return;
    }

    const quote = calculatedQuote;
    if (!isValidQuote(quote)) {
      return;
    }

    const token = getToken();
    if (!token) {
      saveCurrentConfigAndLogin(quote);
      return;
    }

    setCartStatus("adding");
    setCartFeedback("");

    try {
      const currentCart = await getCart(token);
      const existingCartItem = findExistingCartItem(currentCart, quote);

      if (existingCartItem) {
        await updateCartItemQuantity(token, existingCartItem, Number(existingCartItem.quantity || 1) + 1);
      } else {
        await addCartItem(token, {
          product_id: productId,
          alto: quote.height,
          ancho: quote.width,
          anclaje: anchorage,
          color,
          quantity: 1
        });
      }

      window.sessionStorage.removeItem(PENDING_PRODUCT_CONFIG_STORAGE_KEY);
      setCartStatus("success");
      setCartFeedback("Producto añadido al carrito.");
    } catch (error) {
      if (isSessionError(error)) {
        clearSession();
        saveCurrentConfigAndLogin(quote);
        return;
      }

      setCartStatus("error");
      setCartFeedback(
        error instanceof CartClientError && error.status === 0
          ? "No se pudo conectar con el carrito. Inténtalo de nuevo."
          : "No se pudo añadir el producto al carrito. Inténtalo de nuevo."
      );
    }
  };

  if (!availableForSale) {
    return (
      <section className="mw-product-configurator" aria-label={`Disponibilidad de ${productName}`}>
        <p className="mw-alert" role="status">
          {PRODUCT_UNAVAILABLE_MESSAGE}
        </p>
      </section>
    );
  }

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
            {canAddToCart ? (
              <div className="mw-configurator-cart-actions">
                <button
                  className="mw-button mw-button--primary"
                  disabled={isAddingToCart}
                  onClick={handleAddToCart}
                  type="button"
                >
                  {isAddingToCart ? "Añadiendo..." : "Añadir al carrito"}
                </button>
                {cartStatus === "success" ? (
                  <Link className="mw-button mw-button--secondary" href="/cart">
                    Ver carrito
                  </Link>
                ) : null}
              </div>
            ) : null}
            {cartFeedback ? (
              <p
                aria-live="polite"
                className={`mw-configurator-cart-feedback${
                  cartStatus === "error" ? " mw-configurator-cart-feedback--error" : ""
                }`}
                id={cartFeedbackId}
              >
                {cartFeedback}
              </p>
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
