# CSP Report-Only

`www.metalwolft.com` mantiene su CSP aplicada sin cambios y emite una segunda
cabecera `Content-Security-Policy-Report-Only`. Esta política elimina solo
`'unsafe-inline'` de `script-src` para observar incompatibilidades sin bloquear
al navegador.

Los informes se envían a `POST https://api.metalwolft.com/api/security/csp-report`.
El endpoint no guarda datos en la base de datos ni envía correos. Limita el cuerpo,
aplica rate limit y registra únicamente campos normalizados sin query strings.

## Inspección en producción

1. Abre DevTools y revisa **Console** para las violaciones CSP de tipo
   `report-only`.
2. En **Network**, filtra por `csp-report` y confirma respuestas `204` desde
   `api.metalwolft.com`.
3. Revisa los logs estructurados del backend por `event=csp_violation_report`.

Clasificación inicial esperada:

- `blocked-uri: inline` y `source-file` vacío o de la propia web: scripts Flight
  de Next/App Router o el bootstrap de GTM.
- `source-file` bajo `www.googletagmanager.com`: GTM tras aceptar cookies.
- hosts `js.stripe.com` o `hooks.stripe.com`: flujo de tarjeta/3DS de Stripe.
- hosts `paypal.com`, `paypalobjects.com` o `venmo.com`: SDK o popup de PayPal.

No se debe retirar `'unsafe-inline'` de la CSP aplicada mientras los informes y
las pruebas manuales no demuestren una alternativa compatible con Next, GTM y los
pagos.
