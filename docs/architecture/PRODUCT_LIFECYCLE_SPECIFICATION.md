# Product Lifecycle Specification

## 1. Proposito

Este documento define el contrato de dominio para el ciclo de vida publico y comercial de los productos de MetalWolft.

El objetivo es separar dos decisiones que hoy estan mezcladas por ausencia de estado explicito:

- si un producto esta publicado;
- si un producto esta disponible para venta.

La especificacion prepara cambios futuros en:

- migracion Alembic;
- modelo `Products`;
- APIs publicas y administrativas;
- Flask-Admin;
- React legacy;
- Next.js;
- carrito;
- quote;
- Stripe;
- PayPal;
- sitemap;
- retirada de productos.

Queda fuera de esta especificacion:

- implementar campos;
- crear migraciones;
- modificar endpoints;
- cambiar frontends;
- introducir stock clasico;
- disenar UI visual;
- definir tablas de redirects;
- definir sustitutos como entidad propia;
- eliminar productos existentes.

El comportamiento inicial debe conservar la semantica actual: todos los productos existentes migraran como `published=true` y `available_for_sale=true`.

## 2. Definiciones

### Existencia tecnica

Un producto existe tecnicamente cuando hay una fila en `Products`.

La existencia tecnica no implica:

- publicacion;
- aparicion en categoria;
- indexabilidad;
- disponibilidad de compra;
- aparicion en sitemap.

### Publicado

Un producto esta publicado cuando Flask considera que puede exponerse publicamente.

Campo conceptual:

```text
published
```

`published=true` permite que una ficha publica exista, pero no garantiza que el producto pueda comprarse.

### Disponible para venta

Un producto esta disponible para venta cuando Flask permite que entre en nuevas operaciones comerciales online.

Campo conceptual:

```text
available_for_sale
```

`available_for_sale=true` solo es valido si `published=true`.

### Visible

Un producto es visible cuando puede aparecer en superficies publicas como Home, categorias, listados o fichas.

`published` habilita la visibilidad publica. Cada superficie puede aplicar ademas
su politica comercial; inicialmente Home y categoria exigen tambien
`available_for_sale=true`. La visibilidad no deriva de:

- `es_mas_vendido`;
- `es_nuevo_diseno`;
- `sort_order`;
- precio;
- imagen;
- categoria.

### Indexable

Un producto es indexable cuando puede entrar en el sitemap publico y recibir metadata/canonical orientada a indexacion.

La indexabilidad deriva de la politica SEO de Flask y de `published`.

### Comprable

Un producto es comprable cuando puede:

- configurarse para una nueva compra;
- entrar en carrito nuevo;
- entrar en quote;
- iniciar Stripe;
- iniciar PayPal;
- terminar checkout.

La comprabilidad deriva de `available_for_sale=true` y de las validaciones de negocio del backend.

### Descatalogado

Un producto descatalogado ya no se vende.

Puede seguir `published=true` si MetalWolft decide mantener la ficha por SEO, soporte, explicacion comercial o alternativas.

Un producto descatalogado no debe estar `available_for_sale=true`.

### Archivado

Un producto archivado se conserva por integridad historica o administrativa, pero no se expone publicamente ni se vende.

Estado conceptual:

```text
published=false
available_for_sale=false
```

### Eliminado

Un producto eliminado ha sido borrado fisicamente.

La eliminacion fisica no debe permitirse si existen referencias historicas u operativas relevantes.

### Producto historico

Un producto historico es cualquier producto referenciado por datos ya persistidos.

Referencias historicas:

- pedidos;
- facturas;
- albaranes;
- snapshots fiscales, comerciales o documentales.

Referencias operativas:

- carritos;
- favoritos.

Las referencias historicas deben seguir siendo legibles aunque cambie el estado comercial actual del producto.

Las referencias operativas pueden requerir avisos, limpieza o bloqueo de compra, pero no deben romper la experiencia ni producir errores tecnicos.

## 3. Invariantes

1. `published=false` implica `available_for_sale=false`.
2. `published=false` y `available_for_sale=true` es una combinacion invalida.
3. Flask es la unica autoridad de `published` y `available_for_sale`.
4. Un frontend nunca puede autorizar la compra por si mismo.
5. Un producto no disponible no puede entrar en carrito nuevo, quote, Stripe ni PayPal.
6. Un producto no publicado no aparece en Home, categorias publicas ni sitemap.
7. Los pedidos historicos no dependen del estado comercial actual del producto.
8. Las facturas, albaranes y snapshots no deben reconstruirse desde estados vivos del producto.
9. No se elimina fisicamente un producto con referencias historicas.
10. El slug de un producto publicado se considera estable.
11. Cualquier cambio de slug publicado requiere redirect.
12. Los productos a medida no usan stock clasico como autoridad de disponibilidad.
13. `es_mas_vendido`, `es_nuevo_diseno` y `sort_order` no controlan publicacion ni venta.
14. Si un pago ya ha sido confirmado, una retirada posterior del producto no puede impedir la creacion idempotente del pedido. El finalizador debe usar el snapshot validado de la sesion.
15. La retirada comercial de un producto no debe invalidar pedidos, facturas, albaranes ni snapshots existentes.

## 4. Matriz de estados

| published | available_for_sale | Estado | Home | Categoria | Ficha | Sitemap | Configurador | Carrito | Checkout |
|---|---|---|---|---|---|---|---|---|---|
| true | true | Publicado y disponible | Si | Si | Si | Si | Si | Nuevas altas y modificaciones permitidas | Permitido |
| true | false | Publicado no disponible | No inicialmente | No inicialmente | Si, sin compra | Si | No | Lineas existentes visibles con aviso; nuevas altas bloqueadas | Bloqueado |
| false | false | No publicado / archivado | No | No | 404 inicial | No | No | Lineas existentes visibles como retiradas si procede; nuevas altas bloqueadas | Bloqueado |
| false | true | Invalido | No | No | No | No | No | No | No |

Comportamiento inicial obligatorio:

- producto no publicado: 404;
- producto publicado y no disponible: ficha accesible, pero sin compra;
- categoria: inicialmente solo productos publicados y disponibles;
- sitemap: productos publicados;
- Flask-Admin no debe permitir editar estos estados hasta que backend y frontends esten preparados.

## 5. Comportamiento por capa

### Modelo

El modelo futuro debe representar:

```text
published
available_for_sale
```

Los productos existentes deben migrarse inicialmente como:

```text
published=true
available_for_sale=true
```

El modelo debe impedir la combinacion:

```text
published=false
available_for_sale=true
```

### Serializacion

Los serializadores publicos deben exponer solo la informacion necesaria para que el frontend represente correctamente la compra.

Regla inicial:

- `available_for_sale` puede exponerse a fichas publicas para bloquear configurador y CTA;
- `published` no necesita exponerse a clientes si las APIs publicas ya filtran correctamente;
- las APIs administrativas si pueden exponer ambos campos cuando la administracion este preparada.

### API publica

Las APIs publicas deben aplicar filtros en Flask.

Reglas:

- listados publicos: solo `published=true` y, inicialmente, `available_for_sale=true`;
- detalle publico: `published=true`;
- detalle no publicado: 404 inicial;
- detalle publicado no disponible: 200 con compra bloqueada;
- ningun endpoint publico debe permitir comprar por recibir un campo enviado por el cliente.

### API admin

Las APIs administrativas podran gestionar estados cuando todo el stack este preparado.

Hasta entonces:

- no deben aceptar cambios de `published`;
- no deben aceptar cambios de `available_for_sale`;
- no deben permitir combinaciones invalidas;
- no deben permitir delete fisico peligroso.

### Home

Home solo debe recibir productos que Flask considere publicos para esa superficie.

Regla inicial:

- Home muestra solo productos `published=true` y `available_for_sale=true`;
- `es_mas_vendido` y `es_nuevo_diseno` pueden ordenar o destacar;
- esos flags no publican ni habilitan venta.

### Categoria

Las categorias publicas deben listar inicialmente solo productos:

```text
published=true
available_for_sale=true
```

Un producto publicado pero no disponible no aparece inicialmente en categoria, aunque su ficha pueda seguir accesible.

### Ficha

La ficha debe comportarse asi:

- `published=true`, `available_for_sale=true`: ficha completa con compra;
- `published=true`, `available_for_sale=false`: ficha accesible sin configurador ni compra;
- `published=false`, `available_for_sale=false`: 404 inicial.

### Sitemap

El sitemap debe incluir productos `published=true`.

El sitemap no debe incluir productos no publicados.

### Configurador

El configurador solo puede operar si:

```text
available_for_sale=true
```

Si el producto esta publicado pero no disponible, el configurador no debe permitir calcular una compra nueva ni anadir al carrito.

### Carrito

Reglas para carrito:

- anadir una nueva linea requiere `available_for_sale=true`;
- aumentar cantidad o modificar una linea requiere revalidar `available_for_sale=true`;
- eliminar una linea siempre debe permitirse;
- las lineas existentes de productos retirados deben mostrarse con aviso controlado;
- un carrito guardado no puede saltarse la validacion backend.

### Quote

Quote es una defensa autoritativa.

Debe rechazar lineas cuando:

- el producto no existe;
- el producto no esta disponible para venta;
- la configuracion ya no es valida.

Quote no debe aceptar disponibilidad enviada por frontend.

### Stripe

Stripe solo puede iniciarse despues de una quote valida.

No se debe crear ni modificar PaymentIntent si alguna linea de la quote contiene producto no disponible.

Si el pago ya fue confirmado antes de una retirada posterior, el finalizador debe crear o recuperar idempotentemente el pedido usando el snapshot validado.

### PayPal

PayPal solo puede iniciarse despues de una quote valida.

No se debe crear orden PayPal si alguna linea contiene producto no disponible.

Si el pago ya fue confirmado antes de una retirada posterior, el finalizador debe crear o recuperar idempotentemente el pedido usando el snapshot validado.

### Pedidos historicos

Los pedidos historicos deben seguir siendo legibles.

No deben ocultarse ni recalcularse por:

- `published=false`;
- `available_for_sale=false`;
- cambios de precio;
- cambios de descripcion;
- cambio de categoria;
- cambio de slug.

### Facturas, albaranes y snapshots

Las referencias historicas no deben depender del estado vivo del producto.

Una factura emitida, un albaran o un snapshot deben conservar su propia informacion historica.

### Favoritos

Favoritos son referencias operativas.

Reglas:

- si el producto sigue publicado y disponible, se muestra normal;
- si sigue publicado pero no disponible, se muestra como no comprable si la UX lo soporta;
- si no esta publicado, no debe enlazar a una ficha publica normal;
- la ausencia de producto no debe producir error tecnico.

### Flask-Admin

Flask-Admin sera la primera superficie de administracion de estados, pero solo cuando backend y frontends esten preparados.

Hasta entonces, los campos no deben ser editables.

### React legacy

React legacy debe seguir siendo compatible durante la migracion.

Regla:

- no debe decidir publicacion ni compra;
- debe consumir el filtrado y los errores del backend;
- si ignora campos nuevos, Flask debe seguir protegiendo compra y sitemap.

### Next

Next debe:

- consumir estados desde Flask;
- no convertirse en autoridad;
- ocultar configurador si `available_for_sale=false`;
- construir sitemap desde endpoints filtrados por Flask;
- no decidir indexabilidad sin contrato backend.

## 6. Errores de dominio

Errores conceptuales:

| Error | Situacion |
|---|---|
| `ProductNotFound` | No existe producto tecnico |
| `ProductNotPublished` | Producto existe, pero no debe exponerse publicamente |
| `ProductNotAvailableForSale` | Producto publicado, pero no puede comprarse |
| `CartProductRetired` | Carrito contiene producto que ya no puede comprarse |
| `CheckoutProductUnavailable` | Checkout intenta pagar una linea ya no disponible |
| `InvalidProductLifecycleState` | Se intenta guardar `published=false` y `available_for_sale=true` |
| `ReferencedProductDeletionBlocked` | Se intenta eliminar fisicamente un producto con referencias |
| `PublishedSlugChangeRequiresRedirect` | Se intenta cambiar slug publicado sin redirect |

Codigos y textos HTTP definitivos quedan para la implementacion.

Regla inicial de comportamiento:

- producto no publicado en ficha publica: 404;
- producto publicado no disponible: 200 con compra bloqueada;
- producto no disponible en carrito/quote/checkout: error de negocio controlado.

## 7. Productos retirados

| Escenario | Estados | Ficha | Sitemap | Redirect | Compra | Historico |
|---|---|---|---|---|---|---|
| Borrador o creado por error sin referencias | `false / false` | 404 | No | No necesario | No | Sin impacto |
| Retirada temporal | `true / false` | Accesible sin compra | Si | No necesario | No | Legible |
| Descatalogado con sustituto | `true / false` o `false / false` | Accesible con alternativa o 404 | Segun `published` | Requerido si se cambia URL o se oculta | No | Legible |
| Descatalogado sin sustituto | `true / false` o `false / false` | Accesible informativa o 404 | Segun `published` | Opcional segun SEO | No | Legible |
| Producto con pedidos historicos | No borrar fisicamente | Segun estado | Segun estado | Requerido si cambia slug | Segun disponibilidad | Siempre legible |
| Producto con facturas, albaranes o snapshots | No borrar fisicamente | Segun estado | Segun estado | Requerido si cambia slug | Segun disponibilidad | Siempre legible |
| Producto en carritos o favoritos | No borrar sin tratamiento operativo | Segun estado | Segun estado | Segun SEO | Nuevas compras bloqueadas si no disponible | No historico, pero no debe romper UX |
| Cambio de slug publicado | Estados no cambian | Nueva URL | Nueva URL si publicado | Obligatorio | Segun disponibilidad | Historico independiente del slug |
| Eliminacion fisica | Solo sin referencias | No | No | Opcional | No | No aplicable |

## 8. Compatibilidad y migracion

### Defaults

La migracion debe crear los campos de forma compatible:

```text
published=true
available_for_sale=true
```

para todos los productos existentes.

### Backfill

El backfill inicial no debe retirar ningun producto.

Todos los productos existentes conservaran:

- visibilidad publica actual;
- aparicion en categoria;
- aparicion potencial en Home;
- aparicion en sitemap;
- compra;
- compatibilidad con React legacy;
- compatibilidad con Next.

### Orden de despliegue

Orden recomendado:

1. Crear columnas y constraint sin cambiar comportamiento.
2. Actualizar serializacion interna/admin.
3. Actualizar tests de modelo.
4. Preparar Flask-Admin en modo solo lectura para estados.
5. Actualizar APIs publicas con filtros.
6. Actualizar carrito y quote.
7. Actualizar Stripe y PayPal.
8. Actualizar Next.
9. Actualizar React legacy si sigue activo.
10. Activar edicion administrativa.
11. Retirar o alinear sitemap legacy.

### Despliegues mixtos

Durante un despliegue mixto:

- clientes antiguos pueden no enviar ni interpretar estados;
- Flask debe seguir validando compra;
- defaults `true / true` deben evitar cambios publicos no intencionados;
- no se deben marcar productos como retirados hasta completar backend y frontends.

### Rollback conceptual

Si se revierte codigo despues de crear columnas:

- las columnas pueden quedar sin uso;
- no hay perdida funcional si todos los productos siguen `true / true`;
- si ya existen productos retirados, revertir codigo antiguo podria volver a exponerlos.

Por tanto, no debe usarse `published=false` ni `available_for_sale=false` en produccion hasta que la defensa backend este completa.

## 9. Seguridad y pagos concurrentes

### Validacion backend

Flask debe validar disponibilidad en:

- anadir al carrito;
- modificar cantidad;
- construir quote;
- crear PaymentIntent;
- modificar PaymentIntent;
- crear orden PayPal;
- capturar o finalizar checkout cuando aplique.

### Clientes antiguos

React legacy, Next antiguo o llamadas manuales no pueden saltarse la disponibilidad.

La validacion en backend debe ser suficiente aunque el frontend no conozca los campos nuevos.

### Carritos guardados

Un carrito puede contener una linea de producto que luego queda no disponible.

Reglas:

- GET carrito no debe romper;
- debe poder eliminarse la linea;
- no debe poder aumentarse o pagarse;
- quote debe bloquear el checkout.

### Concurrencia entre quote y pago

Si un producto se retira despues de una quote pero antes de crear pago:

- Stripe/PayPal deben bloquearse al revalidar.

Si un producto se retira despues de crear el intento de pago pero antes de confirmarlo:

- la confirmacion debe resolverse con una politica segura;
- no debe iniciarse un pedido nuevo si el pago no esta confirmado;
- si el pago ya esta confirmado, aplica la invariante de snapshot validado.

### Pago confirmado

Si un pago ya ha sido confirmado, una retirada posterior del producto no puede impedir la creacion idempotente del pedido.

El finalizador debe usar:

- `CheckoutSessions`;
- `quote_snapshot`;
- `customer_snapshot`;
- idempotencia existente.

No debe volver a decidir la compra desde el estado vivo del producto si el pago ya esta confirmado y la quote previa fue valida.

### Referencias historicas

Pedidos, facturas, albaranes y snapshots son historicos.

No se deben invalidar por cambios comerciales posteriores.

### Delete fisico

Delete fisico debe bloquearse si existen:

- `OrderDetails`;
- facturas o snapshots relacionados;
- albaranes;
- carritos;
- favoritos;
- imagenes u otras relaciones dependientes.

Carritos y favoritos son operativos, no historicos, pero deben tratarse antes de borrar.

## 10. Sitemap y SEO

### Fuente de verdad

Next sera la autoridad futura del sitemap publico.

Next debe consumir datos de Flask.

Flask sigue siendo la autoridad de:

- publicacion;
- disponibilidad;
- categoria;
- slug;
- compra.

### Productos publicados

Productos `published=true` deben entrar en sitemap.

### Productos no publicados

Productos `published=false`:

- no entran en sitemap;
- no aparecen en Home;
- no aparecen en categoria;
- devuelven 404 inicialmente en ficha.

### Productos publicados no disponibles

Productos `published=true` y `available_for_sale=false`:

- mantienen ficha accesible;
- entran en sitemap;
- no permiten compra;
- pueden mostrar alternativas en una fase posterior.

### Canonical

El canonical debe basarse en el slug publico estable.

Si cambia el slug de un producto publicado, debe existir redirect desde la URL anterior.

### Sitemap legacy

El sitemap legacy debe:

- alinearse con la misma politica;
- o dejar de ser la fuente servida en produccion cuando Next controle sitemap.

No deben coexistir dos sitemaps con criterios distintos.

## 11. Administracion

### Controles

Flask-Admin sera la superficie inicial para gestionar:

- `published`;
- `available_for_sale`.

Pero no debe permitir editarlos hasta que backend y frontends esten preparados.

### Etiquetas

Etiquetas recomendadas:

- `published`: "Publicado en web";
- `available_for_sale`: "Disponible para venta".

### Validaciones

Flask-Admin debe impedir:

- marcar disponible para venta si no esta publicado;
- cambiar slug publicado sin redirect;
- eliminar fisicamente productos con referencias;
- confundir flags comerciales con publicacion.

### Advertencias

Al despublicar:

- desaparece de Home;
- desaparece de categorias;
- desaparece de sitemap;
- ficha devuelve 404 inicial.

Al marcar como no disponible:

- ficha sigue accesible;
- compra se bloquea;
- carrito y checkout pueden requerir avisos.

### Acciones peligrosas

Acciones peligrosas:

- delete fisico;
- cambio de slug publicado;
- cambio de categoria de producto indexado;
- retirada de producto con carritos activos;
- retirada de producto con pagos iniciados.

Estas acciones deben mostrar advertencia o requerir flujo especifico cuando se implementen.

## 12. Tests de aceptacion

### Modelo

- defaults `published=true` y `available_for_sale=true`;
- `published=false`, `available_for_sale=false` valido;
- `published=true`, `available_for_sale=false` valido;
- `published=false`, `available_for_sale=true` invalido;
- flags comerciales no cambian estados.

### API publica

- categoria excluye no publicados;
- categoria excluye inicialmente publicados no disponibles;
- ficha publicada disponible devuelve 200;
- ficha publicada no disponible devuelve 200 sin compra;
- ficha no publicada devuelve 404.

### Home

- Home no muestra no publicados;
- Home no muestra inicialmente no disponibles;
- `es_mas_vendido` solo ordena o destaca productos ya elegibles.

### Sitemap

- sitemap incluye publicados;
- sitemap excluye no publicados;
- sitemap incluye publicados no disponibles;
- sitemap legacy queda alineado o fuera de servicio.

### Carrito

- POST carrito rechaza producto no disponible;
- PUT carrito rechaza aumentar producto no disponible;
- DELETE carrito permite retirar producto no disponible;
- GET carrito no rompe si una linea queda retirada.

### Quote

- quote rechaza producto inexistente;
- quote rechaza producto no disponible;
- quote no acepta disponibilidad enviada por frontend.

### Stripe

- no crea PaymentIntent con producto no disponible;
- no modifica PaymentIntent con producto no disponible;
- pago ya confirmado puede finalizar pedido desde snapshot validado.

### PayPal

- no crea orden PayPal con producto no disponible;
- no captura/continua checkout con quote invalida;
- pago ya confirmado puede finalizar pedido desde snapshot validado.

### Pedidos historicos

- pedido con producto no publicado sigue legible;
- pedido con producto no disponible sigue legible;
- factura/albaran/snapshot no se recalcula desde estado vivo.

### Favoritos

- favoritos no rompen con producto retirado;
- favoritos no permiten comprar producto no disponible.

### Flask-Admin

- estados no editables hasta que backend/frontends esten preparados;
- combinacion invalida bloqueada;
- delete fisico referenciado bloqueado;
- cambio de slug publicado requiere redirect.

### React legacy

- listados respetan filtros backend;
- compra queda bloqueada por backend aunque React ignore campos nuevos.

### Next

- tipos aceptan `available_for_sale`;
- ficha bloquea configurador si no disponible;
- sitemap consume filtros de Flask;
- Next no decide disponibilidad por si mismo.

## 13. Plan de implementacion por commits pequenos

| Commit | Alcance | Riesgo | Validaciones | Rollback |
|---|---|---|---|---|
| 1 | Crear esta especificacion y enlazarla desde arquitectura maestra | Bajo | Revision documental | Revertir documento |
| 2 | Anadir columnas y constraint con defaults `true / true` | Medio | Tests modelo y migracion | Dejar columnas sin uso |
| 3 | Anadir helpers backend de elegibilidad sin cambiar endpoints | Bajo | Tests unitarios | Revertir helpers |
| 4 | Ampliar serializadores internos/admin | Bajo | Tests DTO | Revertir serializacion |
| 5 | Preparar Flask-Admin en solo lectura para estados | Bajo | Tests Admin | Revertir columnas Admin |
| 6 | Filtrar APIs publicas por `published` y disponibilidad inicial de categoria | Medio | Tests API categoria/ficha | Revertir filtros si no hay estados false |
| 7 | Bloquear carrito y quote para productos no disponibles | Alto | Tests carrito/quote | Revertir validacion solo si no hay productos retirados |
| 8 | Proteger Stripe y PayPal con quote validada | Medio | Tests Stripe/PayPal sin proveedores reales | Revertir integracion de validacion |
| 9 | Adaptar Next ficha, Home, categoria y sitemap | Medio | Typecheck/build/tests | Revertir frontend; backend protege compra |
| 10 | Adaptar React legacy si sigue operativo | Medio | Build/tests legacy disponibles | Revertir legacy |
| 11 | Habilitar edicion en Flask-Admin | Medio | Tests Admin + pruebas manuales | Volver a solo lectura |
| 12 | Alinear o retirar sitemap legacy | Medio | Tests sitemap/headers | Restaurar sitemap previo |
| 13 | Introducir politica de redirects para slug publicado | Medio | Tests redirects | Revertir politica si no se han cambiado slugs |

## 14. Preguntas realmente abiertas

1. Si un producto no publicado tenia trafico organico, debe devolver 404, 410 o redirect?
2. Como se define y mantiene un producto sustituto?
3. Que mensaje debe ver el cliente cuando un carrito contiene producto retirado?
4. Que politica aplicar a pagos iniciados pero no confirmados cuando un producto se retira?
5. Quien puede aprobar cambios de slug publicado?
6. Cuando se desactiva definitivamente el sitemap legacy?
7. Deben mostrarse favoritos de productos no publicados o retirarse silenciosamente?
