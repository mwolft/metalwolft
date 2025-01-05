import React, { useRef, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, useGLTF } from '@react-three/drei';
import * as THREE from 'three';

const MetalStructure = () => {
  const groupRef = useRef(); // Referencia para el grupo que contiene el modelo
  const { scene } = useGLTF('https://res.cloudinary.com/dewanllxn/image/upload/v1735066362/tj5xfmx7b0dqpvqdsxaf.glb');

  // Calcular el centro del bounding box y ajustar la posición
  useEffect(() => {
    const box = new THREE.Box3().setFromObject(scene); // Crea un bounding box alrededor del modelo
    const center = box.getCenter(new THREE.Vector3()); // Calcula el centro del modelo
    scene.position.set(-center.x, -center.y, -center.z); // Pposición para centrar el modelo
  }, [scene]);

  // Escalar el modelo
  scene.scale.set(3.8, 3.8, 3.8);

  // Rotación automática del grupo
  useFrame(() => {
    if (groupRef.current) {
      groupRef.current.rotation.y += 0.005; // Rotación automática en el eje Y
    }
  });

  return (
    <group ref={groupRef}>
      <primitive object={scene} />
    </group>
  );
};

const MetalStructureViewer = () => (
  <div style={{ position: 'relative', width: '100%', height: '400px' }}>
    {/* Imagen de 360 grados */}
    <img
      src="https://cdn-icons-png.flaticon.com/512/1758/1758455.png" 
      alt="rejas para ventana sin obra"
      style={{
        position: 'absolute',
        bottom: '10px',
        right: '10px',
        width: 'auto',
        height: '80px',
        zIndex: 10,
      }}
    />
    {/* Visor 3D */}
    <Canvas
      style={{ height: '400px', width: '100%' }}
      camera={{ position: [3, 1, 6] }} // Ajusta la cámara 
    >
      <ambientLight intensity={1} />
      <directionalLight position={[2, 5, 2]} intensity={2} />
      <MetalStructure />
      <OrbitControls />
    </Canvas>
  </div>
);

export default MetalStructureViewer;
