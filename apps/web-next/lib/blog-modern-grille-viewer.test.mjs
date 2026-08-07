import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const article = readFileSync(
  new URL("../app/rejas-para-ventanas-modernas/page.tsx", import.meta.url),
  "utf8"
);
const loader = readFileSync(
  new URL(
    "../components/visualization/ModernGrilleViewerLoader.tsx",
    import.meta.url
  ),
  "utf8"
);
const viewer = readFileSync(
  new URL("../components/visualization/ModernGrilleViewer.tsx", import.meta.url),
  "utf8"
);
const styles = readFileSync(new URL("../app/globals.css", import.meta.url), "utf8");
const packageJson = JSON.parse(
  readFileSync(new URL("../package.json", import.meta.url), "utf8")
);

const designsIndex = article.indexOf("Diseños que suelen funcionar mejor");
const viewerIndex = article.indexOf("Vista 3D de una reja Albany");
const materialsIndex = article.indexOf("Materiales, color y acabado");

assert.doesNotMatch(article, /^"use client";/);
assert.ok(designsIndex >= 0 && viewerIndex > designsIndex);
assert.ok(materialsIndex > viewerIndex);
assert.match(article, /<ModernGrilleViewerLoader \/>/);
assert.match(article, /Gira el modelo para ver su estructura desde distintos ángulos\./);

assert.match(loader, /^"use client";/);
assert.match(loader, /dynamic\(/);
assert.match(loader, /ssr: false/);
assert.match(loader, /IntersectionObserver/);
assert.match(loader, /rootMargin: "240px 0px"/);
assert.match(loader, /<ModernGrilleViewer isActive=\{isNearViewport\} \/>/);
assert.match(loader, /La vista 3D no está disponible en este dispositivo\./);

assert.match(
  viewer,
  /https:\/\/res\.cloudinary\.com\/dewanllxn\/image\/upload\/v1735066362\/tj5xfmx7b0dqpvqdsxaf\.glb/
);
assert.match(viewer, /scene\.clone\(true\)/);
assert.match(viewer, /new Box3\(\)\.setFromObject\(clonedScene\)/);
assert.doesNotMatch(viewer, /scene\.position/);
assert.match(viewer, /useFrame\(\(_, delta\)/);
assert.match(viewer, /rotation\.y \+= delta \* 0\.12/);
assert.doesNotMatch(viewer, /rotation\.y \+= 0\.005/);
assert.match(viewer, /prefers-reduced-motion: reduce/);
assert.match(viewer, /frameloop=\{autoRotate \? "always" : "demand"\}/);
assert.match(viewer, /dpr=\{\[1, 1\.5\]\}/);
assert.match(viewer, /enablePan=\{false\}/);
assert.match(viewer, /minDistance=\{5\.2\}/);
assert.match(viewer, /maxDistance=\{9\}/);
assert.doesNotMatch(viewer, /1758455|360-degree|360°/i);

assert.match(styles, /\.mw-modern-grille-viewer\s*\{[^}]*height: clamp\(22\.5rem, 32vw, 26\.25rem\)/s);
assert.match(styles, /height: clamp\(20rem, 44vw, 22\.5rem\)/);
assert.match(styles, /height: clamp\(16\.25rem, 72vw, 18\.75rem\)/);
assert.match(
  styles,
  /\.mw-modern-grille-viewer > \[role="img"\],[\s\S]*?touch-action: pan-y !important/,
);
assert.doesNotMatch(styles, /\.mw-modern-grille-viewer\s*\{[^}]*height:\s*400px/s);

assert.equal(packageJson.dependencies.three, "0.182.0");
assert.equal(packageJson.dependencies["@react-three/fiber"], "9.7.0");
assert.equal(packageJson.dependencies["@react-three/drei"], "10.4.4");

console.log("Modern grille viewer contract assertions passed");
