"use client";

import { useEffect, useState } from "react";

const SCROLL_THRESHOLD = 480;

export function BackToTopButton() {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const updateVisibility = () => {
      setIsVisible(window.scrollY >= SCROLL_THRESHOLD);
    };

    updateVisibility();
    window.addEventListener("scroll", updateVisibility, { passive: true });
    return () => {
      window.removeEventListener("scroll", updateVisibility);
    };
  }, []);

  if (!isVisible) {
    return null;
  }

  function scrollToTop() {
    const behavior = window.matchMedia("(prefers-reduced-motion: reduce)").matches
      ? "auto"
      : "smooth";
    window.scrollTo({ top: 0, behavior });
  }

  return (
    <button
      aria-label="Volver arriba"
      className="mw-back-to-top"
      onClick={scrollToTop}
      type="button"
    >
      <span aria-hidden="true">↑</span>
    </button>
  );
}
