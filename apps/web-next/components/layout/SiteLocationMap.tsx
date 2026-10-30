"use client";

import { useState } from "react";

const MAP_URL = "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3101.6781877419185!2d-3.932309424299715!3d38.97701567170709!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0xd6bc316fab2423f%3A0xfd159ecd86499a10!2sC.%20Socu%C3%A9llamos%2C%2014%2C%2013005%20Ciudad%20Real%2C%20Cdad.%20Real!5e0!3m2!1ses-419!2ses!4v1793360626781!5m2!1ses-419!2ses";
const EXACT_LOCATION_URL = "https://maps.app.goo.gl/m6hyDrRwTSzptAkDA";

export function SiteLocationMap() {
  const [showMap, setShowMap] = useState(false);

  return (
    <div className="mw-footer__map-preview">
      {showMap ? (
        <iframe
          loading="lazy"
          referrerPolicy="strict-origin-when-cross-origin"
          src={MAP_URL}
          title="Mapa de la próxima ubicación del taller en Calle Socuéllamos 14, Ciudad Real"
        />
      ) : (
        <button onClick={() => setShowMap(true)} type="button">
          Ver ubicación en el mapa
          <span>El mapa se carga desde Google al pulsar.</span>
        </button>
      )}
      <a href={EXACT_LOCATION_URL} rel="noopener noreferrer" target="_blank">
        Ver ubicación en Google Maps
      </a>
    </div>
  );
}
