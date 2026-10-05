"use client";

import type { ReactNode, Ref, RefObject } from "react";
import { createContext, useContext, useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  CATALOG_FILTER_STORAGE_KEY,
  isLocalCatalogFilter,
  type CatalogType,
} from "@/lib/catalog-types";

const CATEGORY_PATH = "/rejas-para-ventanas";
const COLLECTION_PATH = `${CATEGORY_PATH}/abatibles`;
const TYPES: Array<{ id: CatalogType; label: string }> = [
  { id: "all", label: "Todas" },
  { id: "fixed", label: "Fijas" },
  { id: "hinged", label: "Abatibles" },
  { id: "door", label: "Para puertas" },
  { id: "pets", label: "Mascotas" },
];

function rememberFilter(filter: CatalogType) {
  try {
    if (isLocalCatalogFilter(filter)) {
      sessionStorage.setItem(CATALOG_FILTER_STORAGE_KEY, filter);
    } else {
      sessionStorage.removeItem(CATALOG_FILTER_STORAGE_KEY);
    }
  } catch {
    // Navigation still works when session storage is unavailable.
  }
}

export function CatalogTypeNavigation({
  active,
  onFilterChange,
  navRef,
  fixedButtonRef,
}: {
  active: CatalogType;
  onFilterChange?: (filter: CatalogType) => void;
  navRef?: Ref<HTMLElement>;
  fixedButtonRef?: Ref<HTMLButtonElement>;
}) {
  return (
    <nav className="mw-catalog-type-nav" aria-label="Tipos de rejas para ventanas" ref={navRef}>
      {TYPES.map(({ id, label }) => {
        if (id === "hinged") {
          return active === "hinged" ? (
            <span aria-current="page" className="mw-catalog-type-nav__item mw-catalog-type-nav__item--active" key={id}>{label}</span>
          ) : (
            <Link className="mw-catalog-type-nav__item" href={COLLECTION_PATH} key={id}>{label}</Link>
          );
        }

        if (onFilterChange) {
          return (
            <button
              aria-pressed={active === id}
              className={`mw-catalog-type-nav__item${active === id ? " mw-catalog-type-nav__item--active" : ""}`}
              key={id}
              onClick={() => onFilterChange(id)}
              ref={id === "fixed" ? fixedButtonRef : undefined}
              type="button"
            >
              {label}
            </button>
          );
        }

        return (
          <Link className="mw-catalog-type-nav__item" href={CATEGORY_PATH} key={id} onClick={() => rememberFilter(id)}>
            {label}
          </Link>
        );
      })}
    </nav>
  );
}

type CatalogFilterContextValue = {
  active: CatalogType;
  setActive: (type: CatalogType) => void;
  navRef: RefObject<HTMLElement | null>;
  fixedButtonRef: RefObject<HTMLButtonElement | null>;
  showFixedProducts: () => void;
};

const CatalogFilterContext = createContext<CatalogFilterContextValue | null>(null);

function useCatalogFilter() {
  const context = useContext(CatalogFilterContext);
  if (!context) throw new Error("Catalog filter components require CatalogFilterProvider");
  return context;
}

export function CatalogFilterProvider({ children }: { children: ReactNode }) {
  const [active, setActive] = useState<CatalogType>("all");
  const navRef = useRef<HTMLElement>(null);
  const fixedButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    try {
      const pending = sessionStorage.getItem(CATALOG_FILTER_STORAGE_KEY);
      sessionStorage.removeItem(CATALOG_FILTER_STORAGE_KEY);
      if (isLocalCatalogFilter(pending)) setActive(pending);
    } catch {
      // The default "Todas" view remains available without storage.
    }
  }, []);

  function showFixedProducts() {
    setActive("fixed");
    fixedButtonRef.current?.focus({ preventScroll: true });
    navRef.current?.scrollIntoView({
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth",
      block: "start",
    });
  }

  return (
    <CatalogFilterContext.Provider value={{ active, setActive, navRef, fixedButtonRef, showFixedProducts }}>
      {children}
    </CatalogFilterContext.Provider>
  );
}

export function useShowFixedProducts() {
  return useCatalogFilter().showFixedProducts;
}

export function CatalogTypeFilter({ children }: { children: ReactNode }) {
  const { active, setActive, navRef, fixedButtonRef } = useCatalogFilter();

  return (
    <>
      <CatalogTypeNavigation active={active} onFilterChange={setActive} navRef={navRef} fixedButtonRef={fixedButtonRef} />
      <div className="mw-product-grid" data-filter={active} id="catalog-product-grid">{children}</div>
    </>
  );
}
