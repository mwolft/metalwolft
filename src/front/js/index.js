import React from "react";  // Import react into the bundle
import { createRoot } from "react-dom/client";  // Import createRoot from React 18
import "../styles/index.css";  // Include your index.scss file into the bundle
import Layout from "./Layout.jsx";  // Import your own components

// Obtener el elemento contenedor donde se montará la aplicación
const container = document.querySelector("#app");

// Crear una raíz utilizando createRoot
const root = createRoot(container);

// Renderizar la aplicación Layout en la raíz creada
root.render(<Layout />);
