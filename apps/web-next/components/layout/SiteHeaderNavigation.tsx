"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { HeaderAccountMenu } from "@/components/layout/HeaderAccountMenu";
import { HeaderCartLink } from "@/components/layout/HeaderCartLink";
import {
  headerPrimaryCta,
  isNavigationLinkActive,
  primaryNavigationLinks
} from "@/lib/navigation";

const NAVIGATION_ID = "mw-primary-navigation";
const FOCUSABLE_SELECTOR =
  'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';

function isVisibleFocusableElement(element: HTMLElement) {
  return !element.hasAttribute("disabled") && element.getClientRects().length > 0;
}

export function SiteHeaderNavigation() {
  const pathname = usePathname();
  const navDisclosureRef = useRef<HTMLDivElement>(null);
  const toggleRef = useRef<HTMLButtonElement>(null);
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
    setIsMenuOpen(false);

    if (shouldRestoreFocus) {
      requestAnimationFrame(() => {
        toggleRef.current?.focus();
      });
    }
  };

  useEffect(() => {
    closeMenu(false);
  }, [pathname]);

  useEffect(() => {
    const disclosureElement = navDisclosureRef.current;

    if (!isMenuOpen || !disclosureElement) {
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

    const handlePointerDown = (event: PointerEvent) => {
      if (
        event.target instanceof Node &&
        !disclosureElement.contains(event.target)
      ) {
        closeMenu(false);
      }
    };

    const handleScroll = () => {
      closeMenu(false);
    };

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    window.addEventListener("scroll", handleScroll, {
      capture: true,
      passive: true,
    });

    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("scroll", handleScroll, { capture: true });
    };
  }, [isMenuOpen]);

  return (
    <>
      <div className="mw-header__nav-desktop">
        <nav className="mw-nav" aria-label="Navegación principal">
          <ul className="mw-nav-list">{renderNavigationLinks()}</ul>
        </nav>

        <HeaderAccountMenu />
        <HeaderCartLink />

        <Link className="mw-button mw-button--primary mw-header__cta" href={headerPrimaryCta.href}>
          {headerPrimaryCta.label}
        </Link>
      </div>

      <div className="mw-header__mobile-actions">
        <HeaderCartLink />
        <div
          className="mw-header__nav-group mw-nav-disclosure"
          data-open={isMenuOpen}
          ref={navDisclosureRef}
        >
          <button
            className="mw-nav-toggle"
            aria-controls={NAVIGATION_ID}
            aria-expanded={isMenuOpen}
            aria-label={isMenuOpen ? "Cerrar navegación principal" : "Abrir navegación principal"}
            onClick={() => setIsMenuOpen((current) => !current)}
            ref={toggleRef}
            type="button"
          >
            <span aria-hidden="true" />
            <span aria-hidden="true" />
            <span aria-hidden="true" />
            <span className="mw-visually-hidden">{isMenuOpen ? "Cerrar menú" : "Abrir menú"}</span>
          </button>

          <div className="mw-nav-shell mw-nav-shell--mobile">
            <nav className="mw-nav" id={NAVIGATION_ID} aria-label="Navegación principal">
              <ul className="mw-nav-list">{renderNavigationLinks(() => closeMenu(false))}</ul>
            </nav>

            <HeaderAccountMenu variant="mobile" onNavigate={() => closeMenu(false)} />

            <Link
              className="mw-button mw-button--primary mw-header__cta"
              href={headerPrimaryCta.href}
              onClick={() => closeMenu(false)}
            >
              {headerPrimaryCta.label}
            </Link>
          </div>
        </div>
      </div>
    </>
  );
}
