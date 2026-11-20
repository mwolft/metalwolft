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

export const ALBANY_MODEL_URL =
  "https://res.cloudinary.com/dewanllxn/image/upload/v1735066362/tj5xfmx7b0dqpvqdsxaf.glb";

type ModernGrilleViewerProps = {
  isActive: boolean;
  modelUrl?: string;
  label?: string;
};

type AlbanyModelProps = {
  autoRotate: boolean;
  onReady: () => void;
  modelUrl: string;
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

function AlbanyModel({ autoRotate, onReady, modelUrl }: AlbanyModelProps) {
  const rotatingGroupRef = useRef<Group>(null);
  const { scene } = useGLTF(modelUrl);
  const { model, offset, scale } = useMemo(() => {
    const clonedScene = scene.clone(true);
    const bounds = new Box3().setFromObject(clonedScene);
    const center = bounds.getCenter(new Vector3());
    const size = bounds.getSize(new Vector3());
    const largestDimension = Math.max(size.x, size.y, size.z);

    return {
      model: clonedScene,
      offset: [-center.x, -center.y, -center.z] as [number, number, number],
      scale: modelUrl === ALBANY_MODEL_URL || largestDimension <= 0 ? 3.5 : 3.5 / largestDimension
    };
  }, [modelUrl, scene]);

  useEffect(() => {
    if (modelUrl.startsWith("blob:")) {
      return () => useGLTF.clear(modelUrl);
    }
  }, [modelUrl]);

  useEffect(() => onReady(), [model, onReady]);

  useFrame((_, delta) => {
    if (autoRotate && rotatingGroupRef.current) {
      rotatingGroupRef.current.rotation.y += delta * 0.12;
    }
  });

  return (
    <group ref={rotatingGroupRef} rotation={[0.04, -0.3, 0]} scale={scale}>
      <primitive object={model} position={offset} />
    </group>
  );
}

export function ModernGrilleViewer({ isActive, modelUrl = ALBANY_MODEL_URL, label = "Modelo 3D interactivo de una reja Albany" }: ModernGrilleViewerProps) {
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
        aria-label={label}
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
          <AlbanyModel autoRotate={autoRotate} onReady={markModelReady} modelUrl={modelUrl} />
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
