import { useEffect } from "react";
import { useLocation } from "react-router-dom";

export const GA4SPAListener = () => {
  const location = useLocation();

  useEffect(() => {
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({
      event: "page_view_spa",
      page_path: location.pathname,
      page_location: window.location.href
    });
  }, [location]);

  return null;
};
