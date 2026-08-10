"use client";

import {
  type CSSProperties,
  type ReactNode,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState
} from "react";
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
import { useNotification } from "@/components/notifications/NotificationProvider";
import {
  type AnchorageValue,
  type ConfiguratorColorValue,
  type ScrewOptionValue,
  buildLocalProductConfiguration,
  getColorVisual
} from "@/lib/configurator-options";
import {
  DEFAULT_SCREW_OPTION,
  NOT_APPLICABLE_SCREW_OPTION,
  selectCompatibleScrewOption
} from "@/lib/screw-option";
import {
  ProductConfigurationClientError,
  type ProductConfigurationResponse,
  isTemporaryConfigurationNetworkError,
  requestProductConfiguration
} from "@/lib/product-configuration-client";
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
import {
  ProductQuoteClientError,
  type ProductQuoteResponse,
  isTemporaryQuoteNetworkError,
  requestProductQuote
} from "@/lib/product-quote-client";
import { pushGtmEvent } from "@/lib/analytics";

type ProductConfiguratorProps = {
  productId: number;
  categorySlug: string;
  productSlug: string;
  productName: string;
  pricePerM2: number;
  discountedPricePerM2?: number | null;
  availableForSale: boolean;
  deliveryEstimate?: ReactNode;
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
  screwOption: ScrewOptionValue;
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
  screwOption?: unknown;
  screw_option?: unknown;
};

type LocalValidQuote = Extract<ConfiguratorPriceQuote, { ok: true }>;
type DisplayedQuote = Omit<LocalValidQuote, "pricePerM2Used"> & {
  pricePerM2Used?: number;
  source: "flask" | "local-fallback";
};

type RenderedColorOption = ProductConfigurationResponse["colors"][number] & {
  hex: string;
  swatchClass?: "forja";
};

type RenderedColorGroup = {
  value: string;
  label: string;
  options: RenderedColorOption[];
};

const QUOTE_DEBOUNCE_MS = 400;

function normalizeDecimalInput(value: string) {
  return value.replace(",", ".");
}

function isValidQuote(
  quote: DisplayedQuote | null
): quote is DisplayedQuote {
  return quote !== null;
}

function isAbortError(error: unknown) {
  return (
    typeof error === "object" &&
    error !== null &&
    "name" in error &&
    error.name === "AbortError"
  );
}

function parseQuoteDimension(value: string) {
  const normalized = normalizeDecimalInput(value.trim());
  if (!normalized) {
    return null;
  }

  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : null;
}

function toDisplayedAuthoritativeQuote(quote: ProductQuoteResponse): DisplayedQuote {
  return {
    ok: true,
    height: quote.alto,
    width: quote.ancho,
    area: (quote.alto * quote.ancho) / 10_000,
    baseUnitPrice: quote.base_unit_price,
    anchorageSupplement: quote.anchorage_supplement,
    unitPrice: quote.unit_price,
    formattedUnitPrice: formatCurrency(quote.unit_price),
    source: "flask"
  };
}

function toDisplayedFallbackQuote(quote: LocalValidQuote): DisplayedQuote {
  return { ...quote, source: "local-fallback" };
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && Boolean(value.trim());
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
    const pendingScrewOption = parsed.screwOption ?? parsed.screw_option ?? DEFAULT_SCREW_OPTION;

    if (
      pendingProductId !== productId ||
      pendingCategorySlug !== categorySlug ||
      pendingProductSlug !== productSlug ||
      alto === null ||
      ancho === null ||
      !isNonEmptyString(anclaje) ||
      !isNonEmptyString(pendingColor)
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
      color: pendingColor,
      screwOption: isNonEmptyString(pendingScrewOption)
        ? pendingScrewOption
        : DEFAULT_SCREW_OPTION
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
  availableForSale,
  deliveryEstimate
}: ProductConfiguratorProps) {
  const { notify } = useNotification();
  const router = useRouter();
  const [height, setHeight] = useState("");
  const [width, setWidth] = useState("");
  const [anchorage, setAnchorage] = useState<AnchorageValue>("");
  const [color, setColor] = useState<ConfiguratorColorValue>("");
  const [screwOption, setScrewOption] = useState<ScrewOptionValue>(DEFAULT_SCREW_OPTION);
  const [previewColor, setPreviewColor] = useState<ConfiguratorColorValue | null>(null);
  const [productConfiguration, setProductConfiguration] =
    useState<ProductConfigurationResponse | null>(null);
  const [configurationStatus, setConfigurationStatus] = useState<
    "loading" | "ready" | "fallback" | "error"
  >(availableForSale ? "loading" : "ready");
  const [configurationMessage, setConfigurationMessage] = useState("");
  const [calculatedQuote, setCalculatedQuote] = useState<DisplayedQuote | null>(null);
  const [calculationError, setCalculationError] = useState("");
  const [quoteNotice, setQuoteNotice] = useState("");
  const [quoteStatus, setQuoteStatus] = useState<"idle" | "loading">("idle");
  const [quoteRequestVersion, setQuoteRequestVersion] = useState(0);
  const [needsRecalculation, setNeedsRecalculation] = useState(false);
  const activeQuoteController = useRef<AbortController | null>(null);
  const lastTrackedQuoteKey = useRef<string | null>(null);
  const [cartStatus, setCartStatus] = useState<"idle" | "adding" | "success" | "error">("idle");
  const [cartFeedback, setCartFeedback] = useState("");
  const dimensionHelpId = useId();
  const dimensionErrorId = useId();
  const cartFeedbackId = useId();
  const screwOptionsName = useId();

  const configuredAnchorageOptions = useMemo(() => {
    if (!productConfiguration) {
      return [];
    }

    return productConfiguration.anchorages.map((rule) => {
      const supplementLabel =
        rule.enabled && rule.supplement > 0
          ? ` (+${formatCurrency(rule.supplement)} €)`
          : "";
      return {
        ...rule,
        value: rule.value as AnchorageValue,
        label: rule.enabled ? `${rule.label}${supplementLabel}` : `${rule.label} (no disponible)`,
        disabled: !rule.enabled
      };
    });
  }, [productConfiguration]);
  const configuredColorGroups = useMemo(() => {
    if (!productConfiguration) {
      return [];
    }

    const groups = new Map<string, RenderedColorGroup>();
    productConfiguration.colors
      .filter((option) => option.enabled)
      .forEach((option) => {
        const visual = getColorVisual(option.value);
        const renderedOption = { ...option, ...visual };
        const currentGroup = groups.get(option.finish);
        if (currentGroup) {
          currentGroup.options.push(renderedOption);
          return;
        }
        groups.set(option.finish, {
          value: option.finish,
          label: option.finish === "liso" ? "Satinado" : option.finish_label,
          options: [renderedOption]
        });
      });
    return Array.from(groups.values());
  }, [productConfiguration]);
  const configuredColors = useMemo(
    () => configuredColorGroups.flatMap((group) => group.options),
    [configuredColorGroups]
  );
  const configuredScrewOptions = useMemo(
    () =>
      (productConfiguration?.screw_options[anchorage] ?? []).filter(
        (option) => option.enabled
      ),
    [anchorage, productConfiguration]
  );
  const standardScrewLength = useMemo(
    () =>
      configuredScrewOptions.find((option) => option.value === DEFAULT_SCREW_OPTION)
        ?.length_mm ?? null,
    [configuredScrewOptions]
  );
  const selectedAnchorage = productConfiguration?.anchorages.find(
    (option) => option.value === anchorage
  );
  const selectedAnchorageRequiresScrews = selectedAnchorage?.screw_required ?? true;
  const configurationReady =
    configurationStatus === "ready" || configurationStatus === "fallback";
  const controlsDisabled = !configurationReady;
  const activeColorValue = previewColor ?? color;
  const activeColorVisual = getColorVisual(activeColorValue);
  const dimensionError = productConfiguration
    ? getDimensionValidationError(height, width, productConfiguration.dimensions)
    : "";
  const dimensionsReadyForQuote = Boolean(productConfiguration) && !dimensionError;
  const effectivePricePerM2 =
    discountedPricePerM2 && discountedPricePerM2 > 0 ? discountedPricePerM2 : pricePerM2;
  const hasDiscount = Boolean(discountedPricePerM2 && discountedPricePerM2 > 0);

  const promptMessage =
    quoteStatus === "loading"
      ? "Calculando el presupuesto..."
      : needsRecalculation
        ? "La configuración ha cambiado. Actualizando el presupuesto..."
        : dimensionsReadyForQuote
          ? "Medidas listas. El precio se calculará automáticamente."
          : "Introduce tus medidas para ver el coste final.";

  const promptClassName = `mw-configurator-prompt${
    needsRecalculation ? " mw-configurator-prompt--warning" : dimensionsReadyForQuote ? " mw-configurator-prompt--ready" : ""
  }`;
  const productPath = `/${categorySlug}/${productSlug}`;
  const canAddToCart =
    availableForSale &&
    configurationReady &&
    isValidQuote(calculatedQuote) &&
    quoteStatus !== "loading" &&
    !needsRecalculation;
  const isAddingToCart = cartStatus === "adding";

  useEffect(() => {
    if (cartStatus !== "success") {
      return undefined;
    }

    const timeout = window.setTimeout(() => {
      setCartStatus("idle");
      setCartFeedback("");
    }, 2400);

    return () => window.clearTimeout(timeout);
  }, [cartStatus]);

  const previewStyle = useMemo<ColorStyle>(
    () => ({
      "--mw-configurator-color": activeColorVisual.hex,
      backgroundColor: activeColorVisual.hex
    }),
    [activeColorVisual.hex]
  );

  useEffect(() => {
    if (!availableForSale) {
      return;
    }

    const controller = new AbortController();
    setProductConfiguration(null);
    setConfigurationStatus("loading");
    setConfigurationMessage("Cargando configuración disponible...");

    requestProductConfiguration(productId, { signal: controller.signal })
      .then((configuration) => {
        if (controller.signal.aborted) {
          return;
        }
        setProductConfiguration(configuration);
        setConfigurationStatus("ready");
        setConfigurationMessage("");
      })
      .catch((error) => {
        if (controller.signal.aborted || isAbortError(error)) {
          return;
        }

        if (isTemporaryConfigurationNetworkError(error)) {
          setProductConfiguration(buildLocalProductConfiguration(productId));
          setConfigurationStatus("fallback");
          setConfigurationMessage(
            "Configuración temporal cargada localmente por un problema de conexión."
          );
          return;
        }

        setProductConfiguration(null);
        setConfigurationStatus("error");
        setConfigurationMessage(
          error instanceof ProductConfigurationClientError
            ? error.message
            : "No se pudo cargar la configuración del producto."
        );
      });

    return () => controller.abort();
  }, [availableForSale, productId]);

  useEffect(() => {
    if (!configurationReady || !productConfiguration) {
      return;
    }

    const enabledAnchorages = configuredAnchorageOptions.filter((option) => !option.disabled);
    setAnchorage((current) => {
      if (enabledAnchorages.some((option) => option.value === current)) {
        return current;
      }
      return (
        enabledAnchorages.find(
          (option) => option.value === productConfiguration.defaults.anchorage
        )?.value ??
        enabledAnchorages[0]?.value ??
        current
      );
    });
    setColor((current) => {
      if (configuredColors.some((option) => option.value === current)) {
        return current;
      }
      return (
        configuredColors.find((option) => option.value === productConfiguration.defaults.color)
          ?.value ??
        configuredColors[0]?.value ??
        current
      );
    });
  }, [
    configurationReady,
    configuredAnchorageOptions,
    configuredColors,
    productConfiguration
  ]);

  useEffect(() => {
    if (!configurationReady || !productConfiguration) {
      return;
    }

    setScrewOption((current) =>
      selectedAnchorageRequiresScrews
        ? selectCompatibleScrewOption(
            current,
            configuredScrewOptions,
            productConfiguration.defaults.screw_option
          )
        : NOT_APPLICABLE_SCREW_OPTION
    );
  }, [
    configurationReady,
    configuredScrewOptions,
    productConfiguration,
    selectedAnchorageRequiresScrews
  ]);

  useEffect(() => {
    const pendingConfig = readPendingProductConfig(productId, categorySlug, productSlug);
    if (!pendingConfig) {
      return;
    }

    const restoredHeight = String(pendingConfig.alto);
    const restoredWidth = String(pendingConfig.ancho);

    setHeight(restoredHeight);
    setWidth(restoredWidth);
    setAnchorage(pendingConfig.anclaje);
    setColor(pendingConfig.color);
    setScrewOption(pendingConfig.screwOption);
    setCalculatedQuote(null);
    setCalculationError("");
    setQuoteNotice("");
    setNeedsRecalculation(true);
    setCartStatus("idle");
    setCartFeedback("Configuración restaurada. Actualizando el presupuesto.");
    window.sessionStorage.removeItem(PENDING_PRODUCT_CONFIG_STORAGE_KEY);
  }, [categorySlug, productId, productSlug]);

  useEffect(() => {
    if (!availableForSale || !configurationReady || !productConfiguration) {
      return;
    }

    const parsedHeight = parseQuoteDimension(height);
    const parsedWidth = parseQuoteDimension(width);
    if (parsedHeight === null || parsedWidth === null) {
      setCalculatedQuote(null);
      setQuoteNotice("");
      setQuoteStatus("idle");
      setNeedsRecalculation(false);
      setCalculationError(
        height.trim() || width.trim()
          ? getDimensionValidationError(height, width, productConfiguration.dimensions)
          : ""
      );
      return;
    }

    const controller = new AbortController();
    activeQuoteController.current = controller;
    const timer = window.setTimeout(async () => {
      setQuoteStatus("loading");
      setCalculationError("");
      setQuoteNotice("");

      try {
        const quote = await requestProductQuote(
          {
            productId,
            alto: parsedHeight,
            ancho: parsedWidth,
            anclaje: anchorage,
            color,
            screw_option: screwOption,
            quantity: 1
          },
          { signal: controller.signal }
        );

        if (controller.signal.aborted) {
          return;
        }

        setCalculatedQuote(toDisplayedAuthoritativeQuote(quote));
        const quoteKey = [
          productId,
          quote.alto,
          quote.ancho,
          quote.anclaje,
          quote.color,
          quote.screw_option,
          quote.unit_price
        ].join(":");
        if (lastTrackedQuoteKey.current !== quoteKey) {
          lastTrackedQuoteKey.current = quoteKey;
          pushGtmEvent({
            event: "calcular_precio",
            product_name: productName,
            product_slug: productSlug,
            height_cm: quote.alto,
            width_cm: quote.ancho,
            area_m2: (quote.alto * quote.ancho) / 10_000,
            final_price: quote.unit_price.toFixed(2)
          });
        }
        setNeedsRecalculation(false);
      } catch (error) {
        if (controller.signal.aborted || isAbortError(error)) {
          return;
        }

        if (isTemporaryQuoteNetworkError(error)) {
          if (screwOption !== DEFAULT_SCREW_OPTION) {
            setCalculatedQuote(null);
            setCalculationError(
              "No se pudo verificar el suplemento de tornillería. Inténtalo de nuevo."
            );
            setNeedsRecalculation(false);
            return;
          }

          const fallbackQuote = calculateConfiguratorPrice({
            rawHeight: height,
            rawWidth: width,
            pricePerM2,
            discountedPricePerM2,
            anchorage
          });

          if (fallbackQuote.ok) {
            setCalculatedQuote(toDisplayedFallbackQuote(fallbackQuote));
            setQuoteNotice(
              "Precio temporal calculado localmente por un problema de conexión."
            );
            setNeedsRecalculation(false);
          } else {
            setCalculatedQuote(null);
            setCalculationError(fallbackQuote.error);
            setNeedsRecalculation(false);
          }
        } else {
          setCalculatedQuote(null);
          setCalculationError(
            error instanceof ProductQuoteClientError
              ? error.message
              : "No se pudo calcular el presupuesto."
          );
          setNeedsRecalculation(false);
        }
      } finally {
        if (!controller.signal.aborted) {
          setQuoteStatus("idle");
        }
        if (activeQuoteController.current === controller) {
          activeQuoteController.current = null;
        }
      }
    }, QUOTE_DEBOUNCE_MS);

    return () => {
      window.clearTimeout(timer);
      controller.abort();
      if (activeQuoteController.current === controller) {
        activeQuoteController.current = null;
      }
    };
  }, [
    anchorage,
    availableForSale,
    color,
    configurationReady,
    discountedPricePerM2,
    height,
    pricePerM2,
    productId,
    productConfiguration,
    quoteRequestVersion,
    screwOption,
    width
  ]);

  const invalidateCalculatedPrice = () => {
    activeQuoteController.current?.abort();
    setCartStatus("idle");
    setCartFeedback("");
    setCalculatedQuote(null);
    setCalculationError("");
    setQuoteNotice("");
    setQuoteStatus("idle");
    setNeedsRecalculation(true);
  };

  const handleCalculate = () => {
    if (!availableForSale || !configurationReady) {
      return;
    }

    invalidateCalculatedPrice();
    setQuoteRequestVersion((version) => version + 1);
  };

  const buildPendingConfig = (quote: DisplayedQuote): PendingProductConfig => ({
    productId,
    categorySlug,
    productSlug,
    alto: quote.height,
    ancho: quote.width,
    anclaje: anchorage,
    color,
    screwOption
  });

  const saveCurrentConfigAndLogin = (quote: DisplayedQuote) => {
    savePendingProductConfig(buildPendingConfig(quote));
    router.push(`/login?next=${encodeURIComponent(productPath)}`);
  };

  const findExistingCartItem = (
    items: CartItem[],
    quote: DisplayedQuote
  ) =>
    items.find(
      (item) =>
        item.producto_id === productId &&
        sameDimension(item.alto, quote.height) &&
        sameDimension(item.ancho, quote.width) &&
        item.anclaje === anchorage &&
        item.color === color &&
        (item.screw_option ?? DEFAULT_SCREW_OPTION) === screwOption
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
          screw_option: screwOption,
          quantity: 1
        });
      }

      window.sessionStorage.removeItem(PENDING_PRODUCT_CONFIG_STORAGE_KEY);
      setCartStatus("success");
      setCartFeedback("Añadido al carrito.");
      notify({
        title: "Añadido al carrito",
        message: `${productName} · ${quote.height} × ${quote.width} cm`,
        tone: "success",
        dismissLabel: "Seguir comprando",
        action: { label: "Ver carrito", href: "/cart" }
      });
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
              disabled={controlsDisabled}
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
              disabled={controlsDisabled}
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
        {configurationMessage ? (
          <p
            className={
              configurationStatus === "error"
                ? "mw-configurator-error"
                : "mw-configurator-helper"
            }
            role={configurationStatus === "error" ? "alert" : "status"}
          >
            {configurationMessage}
          </p>
        ) : null}

        <div className="mw-configurator-help">
          <p className="mw-configurator-help__title">¿No estás seguro de las medidas?</p>
          <p>Consulta nuestra guía para medir tu ventana antes de calcular el precio.</p>
          <Link href="/medir-hueco-rejas-para-ventanas">Ver guía de medición</Link>
        </div>

        <div className="mw-configurator-grid">
          <label className="mw-configurator-field">
            <span>Instalación</span>
            <select
              disabled={controlsDisabled}
              value={anchorage}
              onChange={(event) => {
                invalidateCalculatedPrice();
                setCalculationError("");
                setAnchorage(event.target.value as AnchorageValue);
              }}
            >
              {configuredAnchorageOptions.map((option) => (
                <option
                  key={option.value}
                  value={option.value}
                  disabled={option.disabled}
                  title={option.description}
                >
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        {selectedAnchorageRequiresScrews && configuredScrewOptions.length ? (
          <fieldset className="mw-configurator-screws">
            <legend>Tornillería</legend>
            <div className="mw-configurator-screws__options">
              {configuredScrewOptions.map((option) => (
                <label
                  className={`mw-configurator-screw-option${
                    screwOption === option.value ? " is-selected" : ""
                  }`}
                  key={option.value}
                >
                  <input
                    checked={screwOption === option.value}
                    disabled={controlsDisabled}
                    name={screwOptionsName}
                    type="radio"
                    value={option.value}
                    onChange={() => {
                      if (screwOption === option.value) {
                        return;
                      }
                      invalidateCalculatedPrice();
                      setCalculationError("");
                      setScrewOption(option.value);
                    }}
                  />
                  <span>
                    <strong>
                      {option.label} · {option.length_mm} mm
                    </strong>
                    <small>
                      {option.length_mm === 80
                        ? "Para fijación directa sobre base maciza."
                        : option.value === "long_150"
                          ? "Para revestimientos o mayor profundidad de fijación."
                          : option.description}
                    </small>
                    {option.length_mm === 80 ? <small>Incluida en el pedido</small> : null}
                    {option.supplement > 0 ? (
                      <small>+{formatCurrency(option.supplement)} €</small>
                    ) : null}
                  </span>
                </label>
              ))}
            </div>
            {standardScrewLength !== null ? (
              <p className="mw-configurator-screws__help">
                <strong>¿Qué longitud elegir?</strong>{" "}
                {standardScrewLength} mm para fijación directa sobre ladrillo, hormigón u otra
                base maciza. 150 mm cuando haya que atravesar revestimientos o alcanzar una base
                de fijación más profunda.
              </p>
            ) : null}
          </fieldset>
        ) : null}

        <fieldset className="mw-configurator-colors">
          <legend>Color</legend>
          <p className="mw-configurator-colors__help">
            Acabado con esmalte sintético de alta resistencia.
          </p>
          {configuredColorGroups.map((group) => (
            <div className="mw-configurator-color-group" key={group.label}>
              <p>{group.label}</p>
              <div className="mw-configurator-swatches">
                {group.options.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    disabled={controlsDisabled}
                    className={`mw-configurator-swatch${
                      option.swatchClass === "forja" ? " mw-configurator-swatch--forja" : ""
                    }${color === option.value ? " is-selected" : ""}`}
                    style={{ "--mw-configurator-color": option.hex } as ColorStyle}
                    aria-pressed={color === option.value}
                    aria-label={
                      option.value === "forja_negro"
                        ? `${option.label}, recomendado por MetalWolft`
                        : option.label
                    }
                    onMouseEnter={() => setPreviewColor(option.value)}
                    onMouseLeave={() => setPreviewColor(null)}
                    onFocus={() => setPreviewColor(option.value)}
                    onBlur={() => setPreviewColor(null)}
                    onClick={() => {
                      if (color === option.value) {
                        return;
                      }
                      invalidateCalculatedPrice();
                      setCalculationError("");
                      setColor(option.value);
                    }}
                  >
                    <span className="mw-configurator-swatch__dot" aria-hidden="true" />
                    {option.value === "forja_negro" ? (
                      <>
                        <span
                          className="mw-configurator-swatch__recommendation-marker"
                          aria-hidden="true"
                        />
                        <span
                          className="mw-configurator-swatch__recommendation-hint"
                          aria-hidden="true"
                        >
                          Negro forja · Recomendado
                        </span>
                      </>
                    ) : null}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </fieldset>

        <div className="mw-configurator-selected-color">
          <div
            className={`mw-configurator-color-preview${
              activeColorVisual.swatchClass === "forja"
                ? " mw-configurator-color-preview--forja"
                : ""
            }`}
            style={previewStyle}
            aria-hidden="true"
          />
          {color === "forja_negro" ? (
            <p className="mw-configurator-color-recommendation">
              Recomendado por MetalWolft
            </p>
          ) : null}
        </div>

        <div className="mw-configurator-calculate">
          <button
            className="mw-button mw-button--primary"
            disabled={controlsDisabled || quoteStatus === "loading"}
            type="button"
            onClick={handleCalculate}
          >
            {quoteStatus === "loading" ? "Calculando..." : "Actualizar precio ahora"}
          </button>
        </div>

        {isValidQuote(calculatedQuote) ? (
          <div className="mw-configurator-result">
            <span>Precio calculado para tus medidas</span>
            <strong>{calculatedQuote.formattedUnitPrice} €</strong>
            <p>IVA incluido para esta configuración.</p>
            {quoteNotice ? (
              <p className="mw-configurator-result__warning" role="status">
                {quoteNotice}
              </p>
            ) : null}
            {deliveryEstimate}
            {canAddToCart ? (
              <div className="mw-configurator-cart-actions">
                <button
                  className={`mw-button mw-button--primary${
                    cartStatus === "success" ? " is-cart-success" : ""
                  }`}
                  disabled={isAddingToCart}
                  onClick={handleAddToCart}
                  type="button"
                >
                  {isAddingToCart
                    ? "Añadiendo..."
                    : cartStatus === "success"
                      ? "Añadido"
                      : "Añadir al carrito"}
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
