"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";
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
}: {
  active: CatalogType;
  onFilterChange?: (filter: CatalogType) => void;
}) {
  return (
    <nav className="mw-catalog-type-nav" aria-label="Tipos de rejas para ventanas">
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

export function CatalogTypeFilter({ children }: { children: ReactNode }) {
  const [active, setActive] = useState<CatalogType>("all");

  useEffect(() => {
    try {
      const pending = sessionStorage.getItem(CATALOG_FILTER_STORAGE_KEY);
      sessionStorage.removeItem(CATALOG_FILTER_STORAGE_KEY);
      if (isLocalCatalogFilter(pending)) setActive(pending);
    } catch {
      // The default "Todas" view remains available without storage.
    }
  }, []);

  return (
    <>
      <CatalogTypeNavigation active={active} onFilterChange={setActive} />
      <div className="mw-product-grid" data-filter={active}>{children}</div>
    </>
  );
}
