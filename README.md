# **MetalWolf Backend y Frontend**

**MetalWolf** es una aplicación web que combina un backend desarrollado en Flask con un frontend estático en React. Su propósito es gestionar contenido dinámico y proporcionar una experiencia optimizada al usuario.

## **Características**
- Backend en Flask con integración a una base de datos PostgreSQL.
- Frontend en React para una interfaz interactiva y atractiva.
- Configuración de dominio principal y subdominio para la API.
- Compatibilidad con SEO y generación de contenido dinámico.

---

## **Tecnologías Utilizadas**

### **Backend**
- Python 3.11
- Flask (API RESTful)
- SQLAlchemy (ORM)
- Flask-Admin (Panel de administración)
- PostgreSQL (base de datos)
- Render (hosting del backend)

### **Frontend**
- React (librería para UI)
- HTML5 / CSS3 / JavaScript
- Webpack y Babel para empaquetar el frontend
- Hostalia (hosting del frontend)

### **Infraestructura**
- Cloudflare (CDN y gestión de DNS)
- Certificados SSL automáticos

---

## **Estructura del Proyecto**

El proyecto está organizado de la siguiente manera:

metalwolft/ ├── src/ │ ├── api/ # Lógica de negocio y rutas del backend │ │ ├── routes.py # Endpoints principales │ │ ├── models.py # Modelos de datos │ │ ├── seo_routes.py # Rutas enfocadas en SEO │ │ ├── admin.py # Configuración del panel de administración │ ├── templates/ # Plantillas HTML renderizadas por Flask │ ├── front/ # Recursos del frontend (React) │ │ ├── img/ # Imágenes estáticas │ │ ├── js/ # Código JS │ │ ├── styles/ # Hojas de estilo CSS │ ├── app.py # Archivo principal de la aplicación Flask │ ├── requirements.txt # Dependencias de Python │ └── wsgi.py # Configuración para servidores WSGI


---

## **Instalación y Configuración**

### **Requisitos previos**
- Python 3.11
- Node.js (para compilar y ejecutar React)
- PostgreSQL (si ejecutas localmente)

### **Clonar el repositorio**
```bash
git clone https://github.com/mwolft/metalwolft.git
cd metalwolft/src

