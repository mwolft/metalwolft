"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useAuthSession } from "@/hooks/useAuthSession";

type HeaderAccountMenuProps = {
  variant?: "desktop" | "mobile";
  onNavigate?: () => void;
};

function isProtectedAfterLogout() {
  const pathname = window.location.pathname;

  if (pathname === "/checkout") {
    return true;
  }

  if (pathname === "/mi-cuenta" || pathname.startsWith("/mi-cuenta/")) {
    return true;
  }

  if (pathname !== "/cart") {
    return false;
  }

  const step = new URLSearchParams(window.location.search).get("step");
  return step === "details" || step === "payment";
}

export function HeaderAccountMenu({ variant = "desktop", onNavigate }: HeaderAccountMenuProps) {
  const router = useRouter();
  const { isAuthenticated, isReady, logout } = useAuthSession();
  const menuRef = useRef<HTMLDetailsElement>(null);
  const summaryRef = useRef<HTMLElement>(null);
  const [isOpen, setIsOpen] = useState(false);

  const closeMenu = (shouldRestoreFocus = false) => {
    if (menuRef.current) {
      menuRef.current.open = false;
    }

    setIsOpen(false);

    if (shouldRestoreFocus) {
      requestAnimationFrame(() => {
        summaryRef.current?.focus();
      });
    }
  };

  const handleLogout = () => {
    const shouldRedirect = isProtectedAfterLogout();

    logout();
    closeMenu(false);
    onNavigate?.();

    if (shouldRedirect) {
      router.replace("/login");
    }
  };

  useEffect(() => {
    if (!isOpen) {
      return undefined;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        closeMenu(true);
      }
    };

    const handlePointerDown = (event: PointerEvent) => {
      if (!menuRef.current?.contains(event.target as Node)) {
        closeMenu(false);
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    document.addEventListener("pointerdown", handlePointerDown);

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.removeEventListener("pointerdown", handlePointerDown);
    };
  }, [isOpen]);

  if (variant === "mobile") {
    if (!isReady || !isAuthenticated) {
      return (
        <Link className="mw-account-mobile-link" href="/login" onClick={onNavigate}>
          Iniciar sesión
        </Link>
      );
    }

    return (
      <div className="mw-account-mobile" aria-label="Cuenta cliente">
        <Link className="mw-account-mobile-link" href="/mi-cuenta" onClick={onNavigate}>
          Mi cuenta
        </Link>
        <button className="mw-account-mobile__action" type="button" onClick={handleLogout}>
          Cerrar sesión
        </button>
      </div>
    );
  }

  if (!isReady || !isAuthenticated) {
    return (
      <Link className="mw-account-link" href="/login">
        Iniciar sesión
      </Link>
    );
  }

  return (
    <details
      className="mw-account-menu"
      onToggle={(event) => setIsOpen(event.currentTarget.open)}
      ref={menuRef}
    >
      <summary
        className="mw-account-menu__summary"
        aria-expanded={isOpen}
        aria-label={isOpen ? "Cerrar menú de cuenta" : "Abrir menú de cuenta"}
        ref={summaryRef}
      >
        Mi cuenta
      </summary>
      <div className="mw-account-menu__panel">
        <Link className="mw-account-menu__action" href="/mi-cuenta" onClick={() => closeMenu(false)}>
          Resumen
        </Link>
        <Link
          className="mw-account-menu__action"
          href="/mi-cuenta/pedidos"
          onClick={() => closeMenu(false)}
        >
          Mis pedidos
        </Link>
        <button className="mw-account-menu__action" type="button" onClick={handleLogout}>
          Cerrar sesión
        </button>
      </div>
    </details>
  );
}
