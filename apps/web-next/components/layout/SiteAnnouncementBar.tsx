"use client";

import { useEffect, useId, useRef, useState } from "react";

export function SiteAnnouncementBar() {
  const [isOpen, setIsOpen] = useState(false);
  const popoverId = useId();
  const popoverRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const handlePointerDown = (event: PointerEvent) => {
      if (
        event.target instanceof Node &&
        !popoverRef.current?.contains(event.target)
      ) {
        setIsOpen(false);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") {
        return;
      }

      setIsOpen(false);
      triggerRef.current?.focus();
    };

    const handleScroll = () => {
      setIsOpen(false);
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
  }, [isOpen]);

  return (
    <aside className="mw-announcement" aria-label="Información sobre envíos">
      <div className="mw-announcement__inner">
        <p className="mw-announcement__copy">Envío gratis a partir de 150 €</p>
        <div
          className="mw-announcement__popover"
          data-open={isOpen}
          ref={popoverRef}
        >
          <button
            aria-controls={popoverId}
            aria-expanded={isOpen}
            aria-label="Información sobre condiciones de envío"
            className="mw-announcement__trigger"
            onClick={() => setIsOpen((current) => !current)}
            ref={triggerRef}
            type="button"
          >
            <svg
              aria-hidden="true"
              className="mw-announcement__icon"
              fill="none"
              focusable="false"
              stroke="currentColor"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              viewBox="0 0 24 24"
            >
              <circle cx="12" cy="12" r="9" />
              <path d="M12 11v5" />
              <path d="M12 8h.01" />
            </svg>
          </button>
          <div
            aria-hidden={!isOpen}
            className="mw-announcement__panel"
            data-open={isOpen}
            id={popoverId}
          >
            <p>
              Envío gratuito en pedidos estándar a partir de 150 €. Los pedidos de
              grandes dimensiones o que requieran transporte especial pueden tener un
              coste adicional.
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
}
