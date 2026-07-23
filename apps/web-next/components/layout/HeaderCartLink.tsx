"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useCartSnapshot } from "@/components/cart/CartProvider";

export function HeaderCartLink() {
  const { lineCount, revision } = useCartSnapshot();
  const [isAnimating, setIsAnimating] = useState(false);
  const accessibleLabel =
    lineCount > 0
      ? `Carrito, ${lineCount} ${lineCount === 1 ? "configuración" : "configuraciones"}`
      : "Carrito";

  useEffect(() => {
    if (revision === 0) {
      return undefined;
    }

    setIsAnimating(true);
    const timeout = window.setTimeout(() => setIsAnimating(false), 520);
    return () => window.clearTimeout(timeout);
  }, [revision]);

  return (
    <Link
      className={`mw-header-cart${isAnimating ? " is-updated" : ""}`}
      href="/cart"
      aria-label={accessibleLabel}
      title={accessibleLabel}
    >
      <svg className="mw-header-cart__icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path
          d="M3.5 5h2.1l1.6 8.1a1 1 0 0 0 1 .8h8.5a1 1 0 0 0 1-.7l1.6-5.7H7.1"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <circle cx="10" cy="18.3" r="1.3" fill="currentColor" />
        <circle cx="17" cy="18.3" r="1.3" fill="currentColor" />
      </svg>
      {lineCount > 0 ? (
        <span className="mw-header-cart__badge" aria-hidden="true">
          {lineCount > 99 ? "99+" : lineCount}
        </span>
      ) : null}
    </Link>
  );
}
