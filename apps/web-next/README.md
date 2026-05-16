# `apps/web-next`

Frontend público SEO paralelo para MetalWolft.

## Qué es

`apps/web-next` es el nuevo shell público en Next.js pensado para mejorar SEO, renderizado inicial e indexabilidad.

## Objetivo

Crear un frontend público SEO en paralelo, sin romper el stack actual.

- No sustituye todavía a la SPA React actual.
- Flask sigue siendo la API y backend de negocio.

## Estado actual

Esta fase solo cubre páginas públicas SEO base.

Quedan fuera por ahora:

- checkout
- carrito
- admin
- auth
- pagos

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

Mientras dure esta etapa, la SPA React actual sigue siendo la aplicación principal para flujos privados y transaccionales.
