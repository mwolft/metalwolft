export function SiteAnnouncementBar() {
  return (
    <aside className="mw-announcement" aria-label="Información sobre envíos">
      <div className="mw-announcement__inner">
        <p className="mw-announcement__copy">Envío gratis a partir de 150 €</p>
        <details className="mw-announcement__details">
          <summary className="mw-announcement__summary">
            <span className="mw-visually-hidden">
              Consultar condiciones del envío gratuito
            </span>
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
          </summary>
          <div className="mw-announcement__panel">
            <p>
              Envío gratuito en pedidos estándar a partir de 150 €. Los pedidos de
              grandes dimensiones o que requieran transporte especial pueden tener un
              coste adicional.
            </p>
          </div>
        </details>
      </div>
    </aside>
  );
}
