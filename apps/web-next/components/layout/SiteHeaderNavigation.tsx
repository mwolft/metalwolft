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
  'summary, a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';

function isVisibleFocusableElement(element: HTMLElement) {
  return !element.hasAttribute("disabled") && element.getClientRects().length > 0;
}

export function SiteHeaderNavigation() {
  const pathname = usePathname();
  const navDisclosureRef = useRef<HTMLDetailsElement>(null);
  const toggleRef = useRef<HTMLElement>(null);
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const renderNavigationLinks = (onNavigate?: () => void) =>
    primaryNavigationLinks.map((link) => {
      const isActive = isNavigationLinkActive(link, pathname);
      const shouldSetAriaCurrent = isActive && link.allowAriaCurrent !== false;

      return (
        <li key={link.href}>
          <Link
            className={`mw-nav-link${isActive ? " is-active" : ""}`}
            href={link.href}
            aria-current={shouldSetAriaCurrent ? "page" : undefined}
            onClick={onNavigate}
          >
            {link.label}
          </Link>
        </li>
      );
    });

  const closeMenu = (shouldRestoreFocus = false) => {
    const disclosureElement = navDisclosureRef.current;

    if (disclosureElement) {
      disclosureElement.open = false;
    }

    setIsMenuOpen(false);

    if (shouldRestoreFocus) {
      requestAnimationFrame(() => {
        toggleRef.current?.focus();
      });
    }
  };

  useEffect(() => {
    setIsMenuOpen(Boolean(navDisclosureRef.current?.open));
  }, []);

  useEffect(() => {
    closeMenu(false);
  }, [pathname]);

  useEffect(() => {
    const disclosureElement = navDisclosureRef.current;

    if (!isMenuOpen || !disclosureElement) {
      document.body.classList.remove(BODY_OPEN_CLASS);
      return undefined;
    }

    const getFocusableElements = () =>
      Array.from(
        disclosureElement.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)
      ).filter(isVisibleFocusableElement);

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        closeMenu(true);
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
    <>
      <div className="mw-header__nav-desktop">
        <nav className="mw-nav" aria-label="Navegación principal">
          <ul className="mw-nav-list">{renderNavigationLinks()}</ul>
        </nav>

        <Link className="mw-button mw-button--primary mw-header__cta" href={headerPrimaryCta.href}>
          {headerPrimaryCta.label}
        </Link>
      </div>

      <details
        className="mw-header__nav-group mw-nav-disclosure"
        onToggle={(event) => setIsMenuOpen(event.currentTarget.open)}
        ref={navDisclosureRef}
      >
        <summary
          className="mw-nav-toggle"
          aria-controls={NAVIGATION_ID}
          aria-expanded={isMenuOpen}
          aria-label={isMenuOpen ? "Cerrar navegación principal" : "Abrir navegación principal"}
          ref={toggleRef}
        >
          <span aria-hidden="true" />
          <span aria-hidden="true" />
          <span aria-hidden="true" />
          <span className="mw-visually-hidden">{isMenuOpen ? "Cerrar menú" : "Abrir menú"}</span>
        </summary>

        <div className="mw-nav-shell mw-nav-shell--mobile">
          <nav className="mw-nav" id={NAVIGATION_ID} aria-label="Navegación principal">
            <ul className="mw-nav-list">{renderNavigationLinks(() => closeMenu(false))}</ul>
          </nav>

          <Link
            className="mw-button mw-button--primary mw-header__cta"
            href={headerPrimaryCta.href}
            onClick={() => closeMenu(false)}
          >
            {headerPrimaryCta.label}
          </Link>
        </div>
      </details>
    </>
  );
}
