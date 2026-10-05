"use client";

import type { ReactNode, Ref } from "react";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { NeedBasedProductGuide } from "@/components/catalog/NeedBasedProductGuide";
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

export function CatalogTypeFilter({ children, showNeedGuide = false }: { children: ReactNode; showNeedGuide?: boolean }) {
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
    <>
      <CatalogTypeNavigation active={active} onFilterChange={setActive} navRef={navRef} fixedButtonRef={fixedButtonRef} />
      <div className="mw-product-grid" data-filter={active} id="catalog-product-grid">{children}</div>
      {showNeedGuide ? <NeedBasedProductGuide onSelectFixed={showFixedProducts} /> : null}
    </>
  );
}
