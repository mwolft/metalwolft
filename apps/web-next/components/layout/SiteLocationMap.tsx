const EXACT_LOCATION_URL = "https://maps.app.goo.gl/m6hyDrRwTSzptAkDA";

export function SiteLocationMap() {
  return (
    <a
      className="mw-footer__map-link"
      href={EXACT_LOCATION_URL}
      rel="noopener noreferrer"
      target="_blank"
    >
      <svg aria-hidden="true" fill="none" viewBox="0 0 24 24">
        <path d="M12 21s7-6.2 7-12a7 7 0 1 0-14 0c0 5.8 7 12 7 12Z" />
        <circle cx="12" cy="9" r="2.5" />
      </svg>
      <span>Ver ubicación en Google Maps</span>
    </a>
  );
}
