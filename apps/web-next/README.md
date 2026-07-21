# `apps/web-next`

Frontend público SEO paralelo para MetalWolft.

## Qué es

`apps/web-next` es el nuevo shell público en Next.js pensado para mejorar SEO, renderizado inicial e indexabilidad.

## Objetivo

Crear un frontend público SEO en paralelo, sin romper el stack actual.

- No sustituye todavía a la SPA React actual.
- Flask sigue siendo la API y backend de negocio.

## Home pública

La Home se compone en `app/page.tsx` como Server Component. El contenido principal no depende
de JavaScript en el navegador y el bloque de modelos se obtiene desde Flask mediante el endpoint
de productos de la categoría `rejas-para-ventanas`.

- Flask decide qué productos son públicos y están disponibles para venta.
- Next no replica las reglas de `published` ni autoriza compras.
- Se muestran como máximo seis modelos, priorizando de forma estable `es_mas_vendido` y después
  `es_nuevo_diseno`; esos campos solo ordenan productos que Flask ya considera descubribles.
- Si la API del catálogo no responde, el resto de la Home y sus guías siguen renderizándose.
- La página usa Server Components; no añade componentes cliente para cargar el catálogo.
- La información comercial indica envío a España peninsular y que el servicio no incluye
  instalación.

Límites actuales: la Home no administra destacados propios, no calcula precios y no presenta
productos retirados. Cualquier cambio de esos criterios debe comenzar en el contrato de Flask.

## Estado actual

Next cubre páginas públicas, autenticación de cliente, área privada, carrito y checkout. La
administración continúa fuera de esta aplicación y el backend Flask conserva toda la autoridad
comercial y transaccional.

## Puertos

- `3000`: React legacy
- `3001`: Flask API
- `3002`: Next public shell

## Arranque local

```bash
cp .env.example .env.local
npm install
npm run dev
```

## Otros comandos

```bash
npm run build
npm start
```

## Nota importante

La migración desde React sigue siendo incremental. No deben retirarse rutas legacy hasta que su
equivalente en Next esté validado y el despliegue haya cambiado de autoridad de forma explícita.
