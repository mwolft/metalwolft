"use client";

import { useEffect, useRef, useState } from "react";

const SCROLL_THRESHOLD = 760;

export function BackToTopButton() {
  const isVisibleRef = useRef(false);
  const [isRendered, setIsRendered] = useState(false);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    let frameId = 0;
    const updateVisibility = () => {
      const shouldBeVisible = window.scrollY >= SCROLL_THRESHOLD;
      if (shouldBeVisible === isVisibleRef.current) {
        return;
      }

      isVisibleRef.current = shouldBeVisible;
      if (shouldBeVisible) {
        setIsRendered(true);
        frameId = window.requestAnimationFrame(() => setIsVisible(true));
      } else {
        window.cancelAnimationFrame(frameId);
        frameId = 0;
        setIsVisible(false);
      }
    };

    updateVisibility();
    window.addEventListener("scroll", updateVisibility, { passive: true });
    return () => {
      window.cancelAnimationFrame(frameId);
      window.removeEventListener("scroll", updateVisibility);
    };
  }, []);

  if (!isRendered) {
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
      aria-hidden={!isVisible}
      className={`mw-back-to-top${isVisible ? " is-visible" : ""}`}
      onClick={scrollToTop}
      onTransitionEnd={() => {
        if (!isVisibleRef.current) {
          setIsRendered(false);
        }
      }}
      tabIndex={isVisible ? 0 : -1}
      type="button"
    >
      <svg aria-hidden="true" viewBox="0 0 24 24">
        <path d="M4.5 16.1a1.65 1.65 0 0 1 0-2.33l6.34-6.35a1.65 1.65 0 0 1 2.33 0l6.34 6.35a1.65 1.65 0 1 1-2.33 2.33L12 10.93l-5.17 5.17a1.65 1.65 0 0 1-2.33 0Z" fill="currentColor" />
      </svg>
    </button>
  );
}
