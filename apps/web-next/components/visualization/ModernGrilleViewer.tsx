"use client";

import {
  Suspense,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState
} from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, useGLTF } from "@react-three/drei";
import { Box3, Group, Vector3 } from "three";

const ALBANY_MODEL_URL =
  "https://res.cloudinary.com/dewanllxn/image/upload/v1735066362/tj5xfmx7b0dqpvqdsxaf.glb";

type ModernGrilleViewerProps = {
  isActive: boolean;
};

type AlbanyModelProps = {
  autoRotate: boolean;
  onReady: () => void;
};

function usePrefersReducedMotion() {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(true);

  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    const updatePreference = () => setPrefersReducedMotion(mediaQuery.matches);

    updatePreference();
    mediaQuery.addEventListener("change", updatePreference);

    return () => mediaQuery.removeEventListener("change", updatePreference);
  }, []);

  return prefersReducedMotion;
}

function AlbanyModel({ autoRotate, onReady }: AlbanyModelProps) {
  const rotatingGroupRef = useRef<Group>(null);
  const { scene } = useGLTF(ALBANY_MODEL_URL);
  const { model, offset } = useMemo(() => {
    const clonedScene = scene.clone(true);
    const center = new Box3().setFromObject(clonedScene).getCenter(new Vector3());

    return {
      model: clonedScene,
      offset: [-center.x, -center.y, -center.z] as [number, number, number]
    };
  }, [scene]);

  useEffect(() => onReady(), [model, onReady]);

  useFrame((_, delta) => {
    if (autoRotate && rotatingGroupRef.current) {
      rotatingGroupRef.current.rotation.y += delta * 0.12;
    }
  });

  return (
    <group ref={rotatingGroupRef} rotation={[0.04, -0.3, 0]} scale={3.5}>
      <primitive object={model} position={offset} />
    </group>
  );
}

export function ModernGrilleViewer({ isActive }: ModernGrilleViewerProps) {
  const prefersReducedMotion = usePrefersReducedMotion();
  const [hasInteracted, setHasInteracted] = useState(false);
  const [modelReady, setModelReady] = useState(false);
  const markModelReady = useCallback(() => setModelReady(true), []);
  const autoRotate = isActive && !prefersReducedMotion && !hasInteracted;

  return (
    <>
      {!modelReady ? (
        <div className="mw-modern-grille-viewer__loading" role="status">
          Cargando modelo 3D...
        </div>
      ) : null}
      <Canvas
        aria-label="Modelo 3D interactivo de una reja Albany"
        role="img"
        camera={{ position: [4, 2.1, 7], fov: 45, near: 0.1, far: 100 }}
        dpr={[1, 1.5]}
        frameloop={autoRotate ? "always" : "demand"}
        gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
      >
        <ambientLight intensity={1.25} />
        <directionalLight position={[3, 5, 4]} intensity={2.2} />
        <directionalLight position={[-4, 1, -3]} intensity={0.7} />
        <Suspense fallback={null}>
          <AlbanyModel autoRotate={autoRotate} onReady={markModelReady} />
        </Suspense>
        <OrbitControls
          enableDamping
          dampingFactor={0.08}
          enablePan={false}
          minDistance={5.2}
          maxDistance={9}
          minPolarAngle={Math.PI * 0.28}
          maxPolarAngle={Math.PI * 0.72}
          rotateSpeed={0.55}
          zoomSpeed={0.65}
          target={[0, 0, 0]}
          onStart={() => setHasInteracted(true)}
        />
      </Canvas>
    </>
  );
}

useGLTF.preload(ALBANY_MODEL_URL);
