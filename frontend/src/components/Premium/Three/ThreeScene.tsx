/**
 * Premium Three.js Scene Component
 * 
 * Creates an immersive 3D background with floating particles and geometric shapes
 * for the landing page hero section.
 */

import { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Stars, Float, MeshDistortMaterial } from '@react-three/drei';
import * as THREE from 'three';

// Floating geometric shapes
function FloatingShape({ position, color, scale = 1 }: { position: [number, number, number], color: string, scale?: number }) {
  const meshRef = useRef<THREE.Mesh>(null);
  
  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.x = state.clock.elapsedTime * 0.2;
      meshRef.current.rotation.y = state.clock.elapsedTime * 0.3;
      meshRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime) * 0.5;
    }
  });

  return (
    <Float speed={2} rotationIntensity={1} floatIntensity={2}>
      <mesh ref={meshRef} position={position} scale={scale}>
        <icosahedronGeometry args={[1, 1]} />
        <MeshDistortMaterial
          color={color}
          attach="material"
          distort={0.3}
          speed={2}
          roughness={0.2}
          metalness={0.8}
        />
      </mesh>
    </Float>
  );
}

// Particle system
function ParticleField() {
  const count = 100;
  const positions = useMemo(() => {
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 20;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 20;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 20;
    }
    return positions;
  }, [count]);

  return (
    <points>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={count}
          array={positions}
          itemSize={3}
          args={[positions, 3]}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.05}
        color="#ffffff"
        transparent
        opacity={0.6}
        sizeAttenuation
      />
    </points>
  );
}

// Main Three.js scene
export function ThreeScene() {
  return (
    <div className="absolute inset-0 z-0">
      <Canvas
        camera={{ position: [0, 0, 10], fov: 60 }}
        gl={{ antialias: true, alpha: true }}
        dpr={[1, 2]}
      >
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1} />
        <pointLight position={[-10, -10, -10]} intensity={0.5} color="#4f46e5" />
        
        {/* Background stars */}
        <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
        
        {/* Floating geometric shapes */}
        <FloatingShape position={[-4, 2, -5]} color="#4f46e5" scale={0.8} />
        <FloatingShape position={[4, -2, -3]} color="#7c3aed" scale={1.2} />
        <FloatingShape position={[0, 4, -8]} color="#06b6d4" scale={0.6} />
        <FloatingShape position={[-6, -4, -6]} color="#10b981" scale={1.0} />
        <FloatingShape position={[6, 3, -4]} color="#f59e0b" scale={0.9} />
        
        {/* Particle field */}
        <ParticleField />
        
        {/* Subtle fog effect */}
        <fog attach="fog" args={['#0a0a0a', 5, 20]} />
        
        {/* Optional orbit controls for development */}
        {/* <OrbitControls enableZoom={false} enablePan={false} autoRotate autoRotateSpeed={0.5} /> */}
      </Canvas>
    </div>
  );
}