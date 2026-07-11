"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import {
  headerPrimaryCta,
  isNavigationLinkActive,
  primaryNavigationLinks
} from "@/lib/navigation";

const NAVIGATION_ID = "mw-primary-navigation";
const BODY_OPEN_CLASS = "mw-nav-open";
const FOCUSABLE_SELECTOR =
  'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';

function isVisibleFocusableElement(element: HTMLElement) {
  return !element.hasAttribute("disabled") && element.getClientRects().length > 0;
}

export function SiteHeaderNavigation() {
  const pathname = usePathname();
  const [isHydrated, setIsHydrated] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const navGroupRef = useRef<HTMLDivElement>(null);
  const toggleButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    setIsMenuOpen(false);
  }, [pathname]);

  useEffect(() => {
    const navGroupElement = navGroupRef.current;

    if (!isMenuOpen || !navGroupElement) {
      document.body.classList.remove(BODY_OPEN_CLASS);
      return undefined;
    }

    const getFocusableElements = () =>
      Array.from(
        navGroupElement.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)
      ).filter(isVisibleFocusableElement);

    const closeMenuAndRestoreFocus = () => {
      setIsMenuOpen(false);
      requestAnimationFrame(() => {
        toggleButtonRef.current?.focus();
      });
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        closeMenuAndRestoreFocus();
        return;
      }

      if (event.key !== "Tab") {
        return;
      }

      const focusableElements = getFocusableElements();

      if (focusableElements.length === 0) {
        return;
      }

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];
      const activeElement = document.activeElement as HTMLElement | null;

      if (event.shiftKey) {
        if (!activeElement || activeElement === firstElement) {
          event.preventDefault();
          lastElement.focus();
        }

        return;
      }

      if (activeElement === lastElement) {
        event.preventDefault();
        firstElement.focus();
      }
    };

    document.body.classList.add(BODY_OPEN_CLASS);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.classList.remove(BODY_OPEN_CLASS);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isMenuOpen]);

  return (
    <div
      className={`mw-header__nav-group${isHydrated ? " is-hydrated" : ""}`}
      ref={navGroupRef}
    >
      <Link
        className="mw-button mw-button--primary mw-header__quick-cta"
        href={headerPrimaryCta.href}
      >
        {headerPrimaryCta.mobileLabel}
      </Link>

      <button
        className="mw-nav-toggle"
        type="button"
        aria-expanded={isMenuOpen}
        aria-controls={NAVIGATION_ID}
        aria-label={
          isMenuOpen ? "Cerrar navegación principal" : "Abrir navegación principal"
        }
        onClick={() => setIsMenuOpen((currentValue) => !currentValue)}
        ref={toggleButtonRef}
      >
        <span aria-hidden="true" />
        <span aria-hidden="true" />
        <span aria-hidden="true" />
      </button>

      <div className={`mw-nav-shell${isMenuOpen ? " is-open" : ""}`}>
        <nav className="mw-nav" id={NAVIGATION_ID} aria-label="Navegación principal">
          <ul className="mw-nav-list">
            {primaryNavigationLinks.map((link) => {
              const isActive = isNavigationLinkActive(link, pathname);
              const shouldSetAriaCurrent = isActive && link.allowAriaCurrent !== false;

              return (
                <li key={link.href}>
                  <Link
                    className={`mw-nav-link${isActive ? " is-active" : ""}`}
                    href={link.href}
                    aria-current={shouldSetAriaCurrent ? "page" : undefined}
                    onClick={() => setIsMenuOpen(false)}
                  >
                    {link.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        <Link
          className="mw-button mw-button--primary mw-header__cta"
          href={headerPrimaryCta.href}
          onClick={() => setIsMenuOpen(false)}
        >
          {headerPrimaryCta.label}
        </Link>
      </div>
    </div>
  );
}
