"use client";

import { Component, type ReactNode, useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";

const ModernGrilleViewer = dynamic(
  () =>
    import("@/components/visualization/ModernGrilleViewer").then(
      (module) => module.ModernGrilleViewer
    ),
  {
    ssr: false,
    loading: () => <ViewerFallback label="Cargando vista 3D..." />
  }
);

type ViewerErrorBoundaryProps = {
  children: ReactNode;
};

type ViewerErrorBoundaryState = {
  hasError: boolean;
};

class ViewerErrorBoundary extends Component<
  ViewerErrorBoundaryProps,
  ViewerErrorBoundaryState
> {
  state: ViewerErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): ViewerErrorBoundaryState {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return <ViewerFallback label="La vista 3D no está disponible en este dispositivo." />;
    }

    return this.props.children;
  }
}

function ViewerFallback({ label }: { label: string }) {
  return (
    <div className="mw-modern-grille-viewer__fallback" role="status">
      <span>{label}</span>
    </div>
  );
}

export function ModernGrilleViewerLoader() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [shouldLoad, setShouldLoad] = useState(false);
  const [isNearViewport, setIsNearViewport] = useState(false);

  useEffect(() => {
    const container = containerRef.current;

    if (!container || !("IntersectionObserver" in window)) {
      setShouldLoad(true);
      setIsNearViewport(true);
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsNearViewport(entry.isIntersecting);

        if (entry.isIntersecting) {
          setShouldLoad(true);
        }
      },
      { rootMargin: "240px 0px" }
    );

    observer.observe(container);

    return () => observer.disconnect();
  }, []);

  return (
    <div ref={containerRef} className="mw-modern-grille-viewer">
      {shouldLoad ? (
        <ViewerErrorBoundary>
          <ModernGrilleViewer isActive={isNearViewport} />
        </ViewerErrorBoundary>
      ) : (
        <ViewerFallback label="La vista 3D se cargará al acercarte a esta sección." />
      )}
    </div>
  );
}
