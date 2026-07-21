# MetalWolft Business Domain Architecture

## 1. Naturaleza normativa

> Este documento es la autoridad principal del dominio comercial y documental de MetalWolft. Antes de modificar productos, ventas, pedidos, pagos, fabricación, albaranes, facturas o procesos posteriores, debe comprobarse la coherencia del cambio con esta arquitectura.

> Si la implementación existente contradice este documento, no debe asumirse automáticamente que el código representa la decisión correcta. La contradicción debe documentarse y resolverse expresamente.

> Cuando aparezca un caso de negocio no contemplado, no debe improvisarse una solución en código. Primero debe proponerse y aprobarse la actualización arquitectónica correspondiente.

Este documento no sustituye al codigo ni a las pruebas. Define el lenguaje, los limites del dominio y las invariantes que deben guiar la implementacion incremental.

## 2. Jerarquia documental

Documentos normativos actuales:

- `docs/architecture/BUSINESS_DOMAIN_ARCHITECTURE.md`: autoridad general del dominio comercial y documental.
- `docs/architecture/INVOICE_DOMAIN_SPECIFICATION.md`: autoridad especializada del dominio de facturacion, snapshot fiscal, numeracion, PDF de factura, email de factura, contabilidad y VeriFactu.
- `docs/architecture/PRODUCT_LIFECYCLE_SPECIFICATION.md`: autoridad especializada del ciclo de vida publico y comercial de productos, incluyendo publicacion, disponibilidad de venta, retirada, sitemap y compatibilidad con carrito/checkout.

Documentos especializados futuros:

- Especificacion de checkout y pagos.
- Especificacion de pedidos y lineas comerciales.
- Especificacion de albaranes y preparacion logistica.
- Especificacion de catalogo, configurador y tipos de linea no cubiertos por el ciclo de vida de producto.
- ADRs puntuales para decisiones irreversibles o de alto riesgo.

Regla de conflicto:

- El documento maestro gobierna las relaciones generales entre dominios.
- La especificacion especializada gobierna los detalles internos de su subdominio.
- Si ambos documentos contradicen una decision, la contradiccion debe resolverse en un cambio documental explicito antes de tocar codigo productivo.

## 3. Protocolo obligatorio de consulta

Antes de cambiar cualquier archivo relacionado con los dominios de este documento, la tarea debe:

1. Leer este documento.
2. Leer `INVOICE_DOMAIN_SPECIFICATION.md` si el cambio afecta facturas, PDF de factura, contabilidad, VeriFactu, email de factura o numeracion fiscal.
3. Identificar si el cambio afecta a checkout, pedidos, productos, pagos, albaranes, ventas manuales o procesos documentales.
4. Declarar si el cambio es compatible con esta arquitectura.
5. Si no es compatible, detener la implementacion y proponer primero una actualizacion arquitectonica.

Checklist minimo para PRs o tareas Codex:

- El checkout sigue limitado a pago -> pedido -> confirmacion, salvo feature flag documentado.
- Ningun numero fiscal se asigna antes de emitir factura.
- Ningun PDF, email, contabilidad o envio fiscal crea una factura por su cuenta.
- Las lineas economicas conservan snapshot descriptivo y economico suficiente.
- Las ventas manuales no deben saltarse el concepto de pedido comercial en nuevas implementaciones.
- Los albaranes no deben mezclarse con facturas.
- Las automatizaciones deben ser configurables y reversibles operativamente.

## 4. Principios generales

- MetalWolft comercializa articulos.
- Un articulo puede ser configurable, de catalogo, personalizado, servicio o suplemento.
- `Orders` representa una operacion comercial general, no exclusivamente un checkout online.
- El checkout es solo un canal de creacion de pedidos.
- Un pedido puede tener origen online, admin, telefono, email, mostrador u otro canal futuro.
- Las lineas deben conservar snapshots descriptivos y economicos.
- Los pagos son independientes del pedido y de la factura.
- El albaran es independiente del pedido y de la factura.
- La factura solo nace al emitirse.
- No existe una factura fiscal pendiente antes de la emision.
- El numero fiscal solo se asigna al emitir.
- La factura emitida es inmutable.
- El PDF es una representacion.
- El email es un proceso de entrega.
- Contabilidad y VeriFactu son procesos independientes, idempotentes y reintentables.
- Las automatizaciones son politicas configurables, no reglas acopladas al checkout.
- El codigo legacy debe conservarse cuando sea necesario para leer historicos, pero no debe usarse como autoridad para disenar nuevos flujos.

## 5. Entidades conceptuales

### Customer

Representa la persona o entidad cliente.

No representa una sesion, un pago ni una factura.

Nace cuando el sistema necesita identificar a quien compra, solicita, recibe o debe figurar en un documento. Puede existir antes de cualquier pedido.

Relaciones principales:

- Puede tener cero o muchos pedidos.
- Puede tener cero o muchos pagos vinculados indirectamente a pedidos.
- Sus datos pueden congelarse en snapshots de pedido, checkout o factura.

Reglas:

- Los datos vivos del cliente no deben modificar una factura emitida.
- Los documentos deben usar snapshots cuando la trazabilidad lo exija.

### CommercialArticle

Representa cualquier cosa vendible o cobrable por MetalWolft.

No representa necesariamente una fila actual de `Products`.

Nace como concepto cuando una oferta puede formar parte de una linea comercial.

Especializaciones:

- `CatalogProduct`.
- `ConfiguredProduct`.
- `CustomLine`.
- `Service`.
- `Supplement`.

Reglas:

- Debe permitir descripcion comercial, precio o regla de precio, fiscalidad y trazabilidad.
- La implementacion actual esta acoplada a `Products`, pero el dominio objetivo es mas amplio.

### CatalogProduct

Representa un articulo de catalogo con precio fijo o precio definido de forma directa.

No requiere medidas ni configuracion para poder venderse, aunque podria admitir variantes simples en el futuro.

Nace cuando un articulo se publica o se habilita para venta de catalogo.

Relaciones principales:

- Puede aparecer en una o muchas lineas de pedido.
- Puede tener SKU, precio, estado activo/inactivo y descripcion.

Reglas:

- Un cambio posterior de precio o descripcion no debe alterar pedidos o facturas ya emitidas.

### ConfiguredProduct

Representa un articulo cuyo precio o descripcion dependen de una configuracion.

No representa todos los articulos de MetalWolft.

Nace cuando el cliente o administrador define una configuracion concreta para una venta.

Ejemplo actual:

- Reja con alto, ancho, instalacion/anclaje y color.

Reglas:

- La configuracion debe congelarse en la linea.
- Flask debe ser la autoridad de precio y validaciones.
- El frontend solo puede replicar calculos para mostrar una previsualizacion.

### CustomLine

Representa una linea ad hoc no necesariamente asociada a un producto de catalogo.

No debe usarse para saltarse validaciones fiscales o comerciales.

Nace en ventas manuales, presupuestos o pedidos administrativos cuando el trabajo vendido no encaja todavia en catalogo.

Reglas:

- Debe conservar descripcion, cantidad, precio unitario, IVA y origen del calculo.
- Debe quedar trazada la persona o canal que la creo.

### Service

Representa un trabajo, servicio o concepto cobrable que no es una pieza fisica principal.

No representa por si mismo un envio ni una factura.

Puede formar parte de un pedido junto a productos configurables o de catalogo.

Ejemplos futuros:

- Servicio de instalacion.
- Ajuste especial.
- Medicion o desplazamiento si se decide cobrarlo.

### Supplement

Representa un incremento economico vinculado a una linea o configuracion.

No debe quedar oculto como texto libre si afecta al precio.

Ejemplo actual:

- Suplemento de pletinas.

Reglas:

- Debe conservarse en el snapshot economico de la linea.
- Flask debe aplicarlo como autoridad.

### SalesOrder

Representa la operacion comercial aceptada por MetalWolft.

En la implementacion actual esta representado por `Orders`.

No representa exclusivamente un checkout online, una factura ni un albaran.

Nace cuando la empresa acepta una venta o encargo que debe prepararse, cobrarse, entregarse o facturarse.

Canales posibles:

- Checkout online.
- Admin.
- Telefono.
- Email.
- Mostrador.
- Otro canal futuro.

Relaciones principales:

- Tiene una o muchas lineas.
- Puede tener cero o muchos pagos.
- Puede tener cero o varios albaranes.
- Puede tener cero o una factura ordinaria inicial.
- Puede tener futuras rectificativas relacionadas de forma fiscal, no como sustitucion del pedido.

Reglas:

- Debe poder existir sin factura.
- Debe poder existir sin albaran.
- Debe conservar origen/canal en futuras iteraciones.
- `Orders.invoice_number` es compatibilidad legacy, no fuente fiscal.

### OrderLine

Representa una linea economica y descriptiva dentro de un pedido.

En la implementacion actual esta representada parcialmente por `OrderDetails`.

No debe asumir que toda linea tiene alto, ancho, anclaje y color.

Tipos conceptuales:

- Producto configurable.
- Producto de catalogo.
- Linea personalizada.
- Servicio.
- Suplemento explicito.

Reglas:

- Debe conservar descripcion congelada.
- Debe conservar precio unitario, cantidad, descuentos, IVA y total.
- Debe conservar la configuracion si existe.
- Debe ser suficiente para reconstruir documentos sin consultar datos vivos.

### Payment

Representa un cobro, intento de cobro, autorizacion o referencia de proveedor.

No es pedido ni factura.

Nace cuando se inicia o registra un movimiento de pago.

Implementaciones actuales:

- Stripe mediante PaymentIntent.
- PayPal mediante orden/captura.

Reglas:

- Un pago confirmado puede habilitar la creacion del pedido.
- Un pedido podria tener pagos manuales o multiples pagos en el futuro.
- La factura no debe depender de llamar de nuevo al proveedor.

### DeliveryNote

Representa albaran, expedicion fisica o parte de entrega.

No es factura.

No crea factura.

No modifica factura.

Nace cuando se prepara, entrega o expide total o parcialmente un pedido.

Relaciones principales:

- Pertenece a un pedido.
- Puede cubrir una o varias lineas o cantidades parciales.
- Un pedido puede tener cero o muchos albaranes.

Reglas:

- Puede tener PDF propio futuro.
- Puede carecer de precios fiscales si asi se decide.
- No debe confundirse con parte de trabajo interno.

### Invoice

Representa el documento fiscal emitido.

No representa un pedido pendiente, un PDF ni un email.

Nace solo cuando se emite y se asigna numero fiscal.

Relaciones principales:

- Puede estar asociada a un pedido.
- Las facturas manuales legacy pueden no tener `order_id`.
- Una factura ordinaria nueva de pedido debe ser unica para ese pedido.

Reglas:

- Debe tener numero fiscal definitivo.
- Debe tener snapshot fiscal.
- Debe ser inmutable tras emitirse.
- Sus efectos secundarios no deben crear otra factura.

### InvoiceSnapshot

Representa la congelacion fiscal de la factura emitida.

No es una cache decorativa.

Nace durante la emision de factura.

Reglas:

- Es la fuente de verdad para PDF, contabilidad, exportaciones y adaptadores fiscales.
- No debe reconstruirse desde datos vivos despues de emitir.
- Debe tener version de esquema y hash.

### AccountingProjection

Representa el reflejo contable interno de una factura emitida.

En la implementacion actual se materializa como `AccountingEntry`.

No es el origen fiscal ni un Excel maestro.

Nace despues de emitir la factura.

Reglas:

- Debe poder regenerarse desde la factura y snapshot.
- Puede fallar y reintentarse sin invalidar la factura.
- No debe modificar la factura.

### VeriFactuSubmission

Representa un intento o estado de comunicacion fiscal externa.

En la implementacion actual se materializa como `InvoiceFiscalSubmission`.

No decide si la factura existe.

Nace despues de emitir la factura.

Reglas:

- Nunca debe modificar numero, snapshot, hash o fecha de emision.
- Debe conservar intentos y respuestas.
- Debe ser reintentable e idempotente.

### DocumentDelivery

Representa la entrega de un documento a una persona o sistema.

No es el documento entregado.

Puede materializarse como email, descarga, portal de cliente u otro canal futuro.

Reglas:

- El email de pedido y el email de factura son entregas distintas.
- Un fallo de entrega no invalida el documento.
- No debe contener autoridad fiscal propia.

## 6. Flujos normativos

### Compra online

```text
pago confirmado
    ->
pedido
    ->
email de confirmacion de pedido
```

Reglas:

- El checkout no emite factura por defecto.
- El checkout no genera PDF de factura por defecto.
- El checkout no registra contabilidad ni VeriFactu por defecto.
- Cualquier automatizacion posterior debe estar protegida por configuracion explicita.

### Venta manual

```text
crear pedido administrativo
    ->
anadir cliente y lineas
    ->
revisar
    ->
registrar o cobrar pago
```

Reglas:

- La venta manual nueva debe crear una operacion comercial antes de emitir factura.
- La ruta legacy de factura manual directa se conserva solo como compatibilidad mientras exista.
- El administrador no debe enviar numero fiscal, snapshot, importes finales de factura ni PDF como autoridad del dominio fiscal.

### Logistica

```text
pedido
    ->
fabricacion o preparacion
    ->
albaran
```

Reglas:

- El albaran documenta preparacion, expedicion o entrega.
- Puede haber cero o varios albaranes por pedido.
- El albaran no crea ni modifica factura.
- El albaran no sustituye el pedido.

### Fiscal

```text
Factura emitida
    |-- generar PDF
    |-- registrar contabilidad
    |-- procesar VeriFactu
    `-- entregar factura por email
```

Reglas:

- La factura nace en la emision, no antes.
- El PDF, contabilidad, VeriFactu y email son procesos posteriores independientes.
- Cada proceso posterior debe ser idempotente, trazable y reintentable.
- No existe un orden rigido entre contabilidad, VeriFactu y email salvo que una futura regla legal o tecnica lo exija.
- El PDF puede ser requisito tecnico para entregar la factura adjunta por email, pero no para la existencia fiscal de la factura.

## 7. Estado actual reconocido

La implementacion actual debe entenderse como una migracion en curso:

- `Products` existe y tiene precio, pero no distingue explicitamente producto configurable, catalogo, servicio o linea personalizada.
- `Orders` existe y debe evolucionar conceptualmente hacia `SalesOrder`, manteniendo compatibilidad con la tabla actual.
- `OrderDetails` esta acoplado a rejas configurables mediante `alto`, `ancho`, `anclaje` y `color`.
- `CheckoutSessions` representa bien el intento tecnico de checkout y conserva snapshots de quote y cliente.
- `Invoices` ya soporta numero fiscal, `invoice_type`, snapshot, hash, PDF nullable y estado de email.
- `AccountingEntry` ya representa proyeccion contable interna.
- `InvoiceFiscalSubmission` ya representa intentos fiscales externos futuros.
- El hook post-pedido permite automatizacion opcional, pero debe permanecer configurable.
- La venta manual legacy todavia puede crear factura directamente.
- El albaran sigue sin modelo propio.

Estas limitaciones no autorizan nuevas implementaciones acopladas al legacy. Deben guiar una migracion incremental.

## 8. Invariantes de compatibilidad

- No se deben romper pedidos, facturas ni PDFs historicos.
- Las facturas manuales legacy sin pedido deben seguir siendo legibles.
- `Orders.invoice_number` puede mantenerse durante la migracion, pero no debe tratarse como fuente fiscal.
- Los generadores legacy de numero no deben usarse en nuevos caminos de emision.
- Los endpoints legacy pueden coexistir temporalmente, pero cualquier nuevo flujo debe declarar si pertenece al dominio objetivo o al legado.
- Las tablas existentes pueden evolucionar antes de crear entidades paralelas, siempre que se preserve la compatibilidad.

## 9. Decisiones prohibidas sin actualizacion arquitectonica

No debe implementarse sin revisar este documento y, cuando cambie una decision aprobada o resuelva una decision pendiente, sin actualizar la arquitectura correspondiente:

- Hacer que el checkout emita factura automaticamente sin flag y sin criterio documentado.
- Crear facturas pendientes sin numero fiscal definitivo.
- Crear PDF de factura como sustituto de factura emitida.
- Mezclar albaran con factura.
- Crear ventas manuales nuevas saltandose el pedido comercial.
- Introducir productos de precio fijo forzandolos a campos de configurador que no aplican.
- Permitir que Next.js, React legacy o React Admin sean autoridad de precios fiscales.
- Enviar o registrar en VeriFactu antes de persistir una factura estable.
- Crear una segunda factura ordinaria para el mismo pedido.
- Editar numero, snapshot, importes o hash de una factura emitida.

## 10. Roadmap minimo recomendado

1. Mantener este documento como referencia normativa y enlazarlo desde instrucciones de desarrollo.
2. Definir especificacion especializada de pedidos y lineas antes de soportar catalogo mixto.
3. Evolucionar `Orders` con origen/canal sin romper el checkout actual.
4. Introducir un modelo o contrato de linea general compatible con `OrderDetails`.
5. Migrar venta manual hacia pedido administrativo facturable.
6. Soportar productos de catalogo y precio fijo en quote, carrito y pedido.
7. Crear dominio de albaranes independiente.
8. Mantener facturacion, PDF, contabilidad, VeriFactu y email como procesos posteriores.
9. Activar automatizaciones solo mediante configuracion explicita y observabilidad suficiente.

## 11. Relacion con la especificacion de facturacion

Todo lo relativo a estas areas debe consultar `INVOICE_DOMAIN_SPECIFICATION.md`:

- Numeracion fiscal.
- `Invoice`.
- `InvoiceSnapshot`.
- Facturas ordinarias y rectificativas.
- PDF de factura.
- Email de factura.
- Contabilidad basada en factura.
- VeriFactu.
- Compatibilidad de facturas historicas.

Este documento maestro no redefine esos detalles. Solo fija que la factura es independiente de pedido, pago, albaran y procesos posteriores.

## 12. Glosario de compatibilidad actual

- `Orders`: tabla actual que debe representar el pedido comercial general durante la migracion.
- `OrderDetails`: tabla actual de lineas, hoy orientada a producto configurable.
- `CheckoutSessions`: proceso tecnico de checkout/pago.
- `Invoices`: facturas emitidas e historicas.
- `AccountingEntry`: proyeccion contable interna.
- `InvoiceFiscalSubmission`: intento de comunicacion fiscal externa.
- `work_order_service`: parte de trabajo interno; no debe considerarse albaran definitivo.
- `/api/manual-invoice`: ruta legacy de factura manual directa; no debe ser el patron para ventas manuales nuevas.

# Architectural Decision Log

## BA-001 — Autoridad del documento maestro

Estado: Aprobada.

Contexto:

- La auditoria del dominio mostro que `INVOICE_DOMAIN_SPECIFICATION.md` es valida para facturacion, pero no cubre todo el dominio comercial.
- El sistema mezcla checkout, pedidos, productos configurables, facturas legacy, PDF, contabilidad, VeriFactu y administracion.
- Sin una referencia maestra, cada cambio puede reinterpretar el dominio desde el codigo existente, aunque ese codigo sea transitorio o legacy.

Decision:

- `BUSINESS_DOMAIN_ARCHITECTURE.md` gobierna el dominio comercial y documental general.
- Las especificaciones especializadas gobiernan los detalles internos de sus subdominios.
- En caso de conflicto, el documento maestro gobierna relaciones entre dominios y la especificacion especializada gobierna reglas internas, pero la contradiccion debe resolverse explicitamente.

Consecuencias:

- Antes de modificar productos, ventas, pedidos, pagos, albaranes, facturas o procesos posteriores, debe consultarse este documento.
- El codigo existente no se considera automaticamente la decision correcta cuando contradice el documento.
- Las nuevas implementaciones deben declarar si siguen el dominio objetivo o conservan compatibilidad legacy.

Elementos todavia pendientes:

- Crear plantillas de PR o checks de proceso que recuerden esta consulta.
- Crear especificaciones especializadas de pedidos, lineas, albaranes, catalogo y pagos.
- Definir un mecanismo formal para registrar cambios futuros de arquitectura.

## BA-002 — Orders como operacion comercial general

Estado: Aprobada.

Contexto:

- La tabla actual `Orders` nacio muy conectada al checkout online.
- La arquitectura objetivo necesita representar ventas por checkout, admin, telefono, email, mostrador u otros canales futuros.
- Sustituir inmediatamente `Orders` por otra tabla romperia flujos productivos, historicos, administracion y facturacion.

Decision:

- `Orders` representa conceptualmente una operacion comercial o encargo, independientemente de su canal de origen.
- `Orders` no representa exclusivamente compras realizadas mediante checkout.
- La tabla no se renombrara ni sustituira ahora por compatibilidad.

Consecuencias:

- Las nuevas ventas manuales deben tender a crear un pedido administrativo antes de emitir factura.
- Los cambios futuros deben evolucionar `Orders` con origen, canal y trazabilidad en lugar de crear un flujo paralelo sin justificarlo.
- `Orders.invoice_number` se conserva como compatibilidad legacy, pero no debe entenderse como la fuente fiscal principal.

Elementos todavia pendientes:

- Definir campos o contrato para `source`, `channel` y actor comercial.
- Definir estados comerciales independientes de estados de pago, factura y albaran.
- Evaluar si en una fase posterior conviene una abstraccion `SalesOrder` de aplicacion sin renombrar la tabla fisica.

## BA-003 — Articulos comerciales heterogeneos

Estado: Aprobada.

Contexto:

- MetalWolft vende principalmente rejas configurables, pero el dominio no debe limitarse a ese caso.
- Ya existe necesidad de piezas con precio fijo, trabajos personalizados, servicios y suplementos.
- El modelo actual `Products` no distingue suficientemente entre catalogo, configurador, servicio o linea personalizada.

Decision:

- MetalWolft puede vender productos configurables, productos de catalogo, piezas personalizadas, servicios y suplementos.
- El concepto de articulo comercial es mas amplio que una fila actual de `Products`.
- Cada tipo de articulo debe poder aportar descripcion, precio o regla de precio, fiscalidad y trazabilidad.

Consecuencias:

- No se debe forzar un producto de precio fijo a tener alto, ancho, anclaje o color si no aplica.
- El catalogo futuro debe poder convivir con el configurador actual.
- Los servicios y suplementos deben aparecer como conceptos economicos trazables, no como texto oculto sin significado fiscal.

Elementos todavia pendientes:

- Definir tipos concretos de articulo y su representacion tecnica.
- Definir SKU, estado activo/inactivo, disponibilidad y stock si aplica.
- Definir como se publica un articulo en Next, React Admin y futuros canales.

## BA-004 — Lineas economicas generalizadas

Estado: Aprobada.

Contexto:

- `OrderDetails` esta orientado a rejas configurables mediante `alto`, `ancho`, `anclaje` y `color`.
- El checkout, carrito y quote actuales asumen una configuracion de reja para calcular precio.
- Para vender catalogo, servicios o lineas manuales hace falta un contrato comun de linea.

Decision:

- Todas las lineas comerciales deben converger en un contrato comun con snapshot descriptivo y economico.
- La configuracion especifica es opcional y no puede ser requisito para todos los tipos de linea.
- Cada linea debe conservar descripcion, cantidad, precio unitario, descuentos, IVA, total y origen del calculo.

Consecuencias:

- Los nuevos flujos no deben depender de que toda linea tenga medidas o anclaje.
- La factura y los documentos posteriores deben poder reconstruirse desde snapshots, no desde productos vivos.
- El frontend puede mostrar configuracion, pero Flask debe seguir siendo autoridad economica.

Elementos todavia pendientes:

- Diseñar el contrato `OrderLine` compatible con `OrderDetails`.
- Decidir si se evoluciona la tabla actual o se introduce una tabla nueva en fase posterior.
- Definir snapshots para catalogo fijo, configurador, servicio, suplemento y linea personalizada.

## BA-005 — Checkout desacoplado de facturacion

Estado: Aprobada.

Contexto:

- El flujo actual validado separa checkout, pedido y email de confirmacion de la emision fiscal.
- La facturacion automatica puede ser util en el futuro, pero tiene riesgos comerciales y fiscales si se acopla al pago.
- Hay excepciones abiertas: particulares, anticipos, pagos parciales, devoluciones, total cero y facturas simplificadas.

Decision:

- El flujo obligatorio del checkout termina en pago confirmado, pedido creado y email de confirmacion.
- La emision fiscal no forma parte obligatoria del checkout.
- Cualquier ejecucion automatica del workflow de factura debe estar detras de configuracion explicita, observabilidad y criterios documentados.

Consecuencias:

- `/thank-you` y el cliente final no deben depender de que exista factura, PDF, contabilidad, VeriFactu o email de factura.
- Un fallo del workflow documental no debe revertir el pedido ni cambiar el estado del pago.
- El pedido pagado puede quedar pendiente de facturar.

Elementos todavia pendientes:

- Definir politica de automatizacion por canal, cliente, importe y tipo de operacion.
- Definir si algunos pedidos requieren revision manual antes de emitir factura.
- Definir indicadores administrativos para pedidos pagados pendientes de factura.

## BA-006 — Albaran independiente

Estado: Aprobada.

Contexto:

- El albaran fue identificado en la especificacion fiscal, pero no existe modelo propio.
- Existen conceptos cercanos como parte de trabajo o nota de entrega, pero no equivalen al albaran objetivo.
- Mezclar albaran con factura puede romper trazabilidad logistica y fiscal.

Decision:

- El albaran es un documento logistico independiente.
- No es una factura, no sustituye a la factura y no equivale al parte de trabajo.
- Puede haber cero, uno o varios albaranes para un pedido.

Consecuencias:

- La creacion de albaranes no debe emitir factura ni modificar una factura emitida.
- Un albaran puede documentar expedicion parcial o total.
- El futuro PDF de albaran, si existe, debe tener contrato propio y no usar el PDF fiscal de factura.

Elementos todavia pendientes:

- Definir modelo, numeracion si aplica y estados de albaran.
- Definir relacion entre lineas de pedido y cantidades expedidas.
- Definir si los albaranes muestran precios, solo descripcion o ambos segun caso.

## BA-007 — Venta manual mediante pedido

Estado: Aprobada.

Contexto:

- La ruta legacy `/api/manual-invoice` crea factura directa.
- Ese camino puede conservar historicos y excepciones, pero no representa bien una operacion comercial revisable.
- Las ventas manuales necesitan cliente, lineas, posible pago, preparacion, albaran y factura posterior.

Decision:

- El camino ordinario para nuevas ventas manuales sera crear una operacion comercial o pedido administrativo y emitir posteriormente la factura.
- La creacion directa de factura se conserva unicamente como compatibilidad legacy o para excepciones futuras expresamente definidas.

Consecuencias:

- Nuevas pantallas administrativas de venta manual no deben usar la factura como primer objeto del flujo.
- La factura manual directa no debe ser el patron para catalogo, servicios o lineas personalizadas.
- El pedido administrativo debe capturar snapshots comerciales suficientes antes de la emision fiscal.

Elementos todavia pendientes:

- Definir UI y API de pedido administrativo.
- Definir excepciones futuras donde se permita factura sin pedido.
- Definir como migrar o limitar `/api/manual-invoice` sin romper historicos.

## BA-008 — La factura nace al emitirse

Estado: Aprobada.

Contexto:

- La arquitectura fiscal exige no reservar numeros y no crear facturas fiscales provisionales.
- Antes de emitir puede existir un pedido pagado, revisado o pendiente de facturar.
- Crear filas de factura sin numero definitivo podria confundirse con documento fiscal existente.

Decision:

- Antes de la emision puede existir un pedido pendiente de facturar, pero no una factura fiscal provisional o pendiente de numero.
- La factura nace cuando se asignan numero fiscal, fecha de emision y snapshot fiscal inmutable.
- La factura emitida es inmutable y sus cambios posteriores deben resolverse con documentos fiscales adicionales.

Consecuencias:

- No se debe crear `Invoice` como borrador fiscal sin numero.
- Los estados previos pertenecen al pedido o a una cola/vista de pendientes, no a una factura fiscal.
- La numeracion debe ocurrir dentro de la transaccion de emision.

Elementos todavia pendientes:

- Definir vistas de pedidos pendientes de facturar.
- Definir tratamiento de pedidos no facturables, anticipos y operaciones de total cero.
- Definir rectificativas y documentos fiscales posteriores.

## BA-009 — Procesos fiscales posteriores independientes

Estado: Aprobada.

Contexto:

- PDF, contabilidad, VeriFactu y email tienen fallos y reintentos propios.
- El sistema ya separa varios de estos pasos, pero los flujos pueden inducir a pensar en un orden lineal obligatorio.
- Algunas dependencias tecnicas existen, por ejemplo enviar una factura adjunta requiere PDF disponible.

Decision:

- PDF, contabilidad, VeriFactu y entrega por email son procesos independientes, idempotentes y reintentables.
- No se define un orden rigido entre contabilidad, VeriFactu y email salvo que una futura regla legal o tecnica lo exija.
- La unica dependencia general es `factura emitida -> procesos posteriores`.
- El PDF puede ser requisito tecnico para enviar la factura adjunta, pero no para la existencia fiscal de la factura.

Consecuencias:

- Un fallo de contabilidad no debe impedir VeriFactu si el flujo futuro decide ejecutarlo.
- Un fallo de email no invalida factura, PDF, contabilidad ni VeriFactu.
- Los reintentos de procesos posteriores nunca deben crear una nueva factura.

Elementos todavia pendientes:

- Definir orden operativo real cuando VeriFactu tenga requisitos definitivos.
- Definir politicas de reintento, observabilidad y alertas.
- Definir si algun canal requiere enviar email despues de VeriFactu por razones legales o comerciales.

## BA-010 — Evolucion incremental compatible

Estado: Aprobada.

Contexto:

- El sistema esta en produccion y conserva datos, rutas y formatos legacy.
- Hay piezas modernas del dominio fiscal ya implementadas, pero tambien quedan generadores y endpoints legacy.
- Una sustitucion completa inmediata aumentaria el riesgo de romper checkout, admin, facturas historicas o PDFs existentes.

Decision:

- La arquitectura se implantara mediante cambios pequeños, compatibles, reversibles y auditables.
- No habra sustitucion completa inmediata de `Orders`, `OrderDetails` ni otros modelos productivos.
- Cada cambio debe conservar lectura de historicos y separar claramente dominio objetivo de compatibilidad legacy.

Consecuencias:

- Las migraciones deben ser incrementales y con criterios de aceptacion claros.
- Los endpoints legacy pueden coexistir temporalmente, pero no deben inspirar nuevos flujos sin decision explicita.
- La limpieza de deuda se hara por fases, despues de asegurar rutas nuevas y compatibilidad.

Elementos todavia pendientes:

- Definir secuencia de migracion para venta manual, catalogo fijo y albaranes.
- Definir retirada o encapsulado de generadores legacy.
- Definir observabilidad minima para automatizaciones documentales.

# Decisiones pendientes

## Momento fiscal de emision cuando existe pago anticipado

Estado: pendiente.

Por que todavia no se decide:

- Requiere confirmar criterio fiscal y operativo para anticipos, reservas y pagos antes de fabricar o entregar.

Dominios afectados:

- Pagos, pedidos, facturacion, contabilidad, VeriFactu y email.

No debe asumirse mientras siga abierta:

- No debe asumirse que todo pago anticipado obliga a emitir factura inmediatamente.
- No debe asumirse que el checkout puede decidir esta politica por si solo.

## Politica de factura para particulares

Estado: pendiente.

Por que todavia no se decide:

- Falta cerrar cuando se emite factura completa, simplificada o bajo peticion del cliente particular.

Dominios afectados:

- Checkout, pedidos, facturacion, datos de cliente, PDF y email.

No debe asumirse mientras siga abierta:

- No debe asumirse que todos los particulares reciben automaticamente la misma factura que una empresa.
- No debe asumirse que el formulario actual de checkout contiene todos los datos fiscales necesarios.

## Factura ordinaria y factura simplificada

Estado: pendiente.

Por que todavia no se decide:

- La implementacion actual solo consolida la factura ordinaria inicial y deja simplificadas fuera de alcance.

Dominios afectados:

- Facturacion, numeracion, PDF, VeriFactu, contabilidad y administracion.

No debe asumirse mientras siga abierta:

- No debe crearse una factura simplificada reutilizando sin mas la estructura de factura ordinaria.
- No debe mezclarse `invoice_type` fiscal con origen operativo o canal.

## Fecha de operacion frente a fecha de emision

Estado: pendiente.

Por que todavia no se decide:

- Hay que definir si la fecha de operacion procede del pago, pedido, entrega, fabricacion o decision administrativa.

Dominios afectados:

- Pedidos, pagos, albaranes, facturacion, contabilidad y VeriFactu.

No debe asumirse mientras siga abierta:

- No debe asumirse que la fecha de pago y la fecha de emision son siempre iguales.
- No debe recalcularse la fecha de una factura emitida desde datos vivos.

## Facturas rectificativas

Estado: pendiente.

Por que todavia no se decide:

- Requiere definir relacion con factura original, numeracion, importes, causas, PDF y tratamiento fiscal.

Dominios afectados:

- Facturacion, pedidos, devoluciones, pagos, contabilidad, VeriFactu y admin.

No debe asumirse mientras siga abierta:

- No debe corregirse una factura emitida editandola.
- No debe crearse una segunda factura ordinaria para corregir la primera.

## Devoluciones y reembolsos

Estado: pendiente.

Por que todavia no se decide:

- Falta definir relacion entre reembolso, devolucion fisica, rectificativa, estado de pedido y comunicacion al cliente.

Dominios afectados:

- Pedidos, pagos, albaranes, facturacion, contabilidad, VeriFactu y email.

No debe asumirse mientras siga abierta:

- No debe asumirse que devolver dinero elimina o modifica la factura emitida.
- No debe asumirse que una devolucion logistica implica automaticamente rectificativa sin decision fiscal.

## Pedidos con total cero

Estado: pendiente.

Por que todavia no se decide:

- El checkout de pago y los proveedores tienen limites tecnicos, y el tratamiento fiscal de pedidos gratuitos necesita regla propia.

Dominios afectados:

- Checkout, pagos, descuentos, pedidos, facturacion y contabilidad.

No debe asumirse mientras siga abierta:

- No debe forzarse un pago de importe minimo para simular un pedido gratuito.
- No debe emitirse factura de total cero sin politica fiscal aprobada.

## Excepciones que permitan factura manual sin pedido

Estado: pendiente.

Por que todavia no se decide:

- La compatibilidad legacy existe, pero el patron objetivo es pedido administrativo antes de factura.

Dominios afectados:

- Ventas manuales, facturacion, admin, PDFs historicos y contabilidad.

No debe asumirse mientras siga abierta:

- No debe ampliarse la factura manual directa a nuevos casos sin decision explicita.
- No debe eliminarse la lectura de facturas manuales historicas.

## Varios pagos para un pedido

Estado: pendiente.

Por que todavia no se decide:

- El modelo actual se apoya principalmente en `CheckoutSessions` y referencias de proveedor, no en una entidad general de pagos multiples.

Dominios afectados:

- Pagos, pedidos, checkout, venta manual, facturacion y contabilidad.

No debe asumirse mientras siga abierta:

- No debe asumirse que un pedido tiene siempre un solo pago.
- No debe emitirse factura basandose en un pago parcial sin politica aprobada.

## Anticipos y pagos parciales

Estado: pendiente.

Por que todavia no se decide:

- Necesita distinguir anticipo, reserva, pago parcial, pago final y su reflejo fiscal.

Dominios afectados:

- Pagos, pedidos, facturacion, contabilidad, VeriFactu y email.

No debe asumirse mientras siga abierta:

- No debe tratarse todo pago parcial como pedido completamente pagado.
- No debe asumirse que el mismo flujo de checkout cubre anticipos sin cambios de dominio.

## Varias expediciones y albaranes parciales

Estado: pendiente.

Por que todavia no se decide:

- Todavia no existe modelo propio de albaran ni relacion de cantidades expedidas por linea.

Dominios afectados:

- Pedidos, lineas, fabricacion, logistica, albaranes, facturacion y admin.

No debe asumirse mientras siga abierta:

- No debe asumirse un unico albaran por pedido.
- No debe confundirse parte de trabajo con albaran parcial.

## Relacion entre albaranes y facturas

Estado: pendiente.

Por que todavia no se decide:

- La arquitectura ya separa ambos documentos, pero no define si futuras facturas pueden referenciar albaranes o agrupar expediciones.

Dominios afectados:

- Pedidos, albaranes, facturacion, PDF, contabilidad y admin.

No debe asumirse mientras siga abierta:

- No debe asumirse que un albaran crea factura.
- No debe asumirse que toda factura debe nacer desde un albaran.

## Presupuestos

Estado: pendiente.

Por que todavia no se decide:

- El presupuesto puede compartir cliente, articulos y lineas, pero no equivale a pedido aceptado ni factura.

Dominios afectados:

- Ventas, catalogo, configurador, pedidos, pagos y admin.

No debe asumirse mientras siga abierta:

- No debe reutilizarse `Orders` como presupuesto sin definir estados y conversion.
- No debe asignarse numero fiscal ni crear factura desde un presupuesto no aceptado.

## SKU, stock y disponibilidad de catalogo

Estado: pendiente.

Por que todavia no se decide:

- `Products` existe, pero no define todavia el contrato completo de catalogo, stock, SKU o disponibilidad.

Dominios afectados:

- Productos, catalogo, Next, React Admin, carrito, pedidos y lineas.

No debe asumirse mientras siga abierta:

- No debe asumirse que `slug` equivale a SKU fiscal o logistico.
- No debe bloquearse la venta de productos configurables por no tener stock clasico.

## Formato definitivo de exportacion contable

Estado: pendiente.

Por que todavia no se decide:

- Ya existe proyeccion contable interna, pero el formato externo puede depender de asesoria, obligaciones fiscales o software contable.

Dominios afectados:

- Contabilidad, Excel, facturacion, impuestos y admin.

No debe asumirse mientras siga abierta:

- No debe tratarse el Excel como origen maestro.
- No debe codificarse un formato final irreversible sin validacion externa.

## Integracion concreta con VeriFactu

Estado: pendiente.

Por que todavia no se decide:

- Falta cerrar requisitos tecnicos definitivos, firma, XML, certificados, QR, respuestas y reintentos reales.

Dominios afectados:

- Facturacion, VeriFactu, PDF, contabilidad, admin y observabilidad.

No debe asumirse mientras siga abierta:

- No debe considerarse que `InvoiceFiscalSubmission` actual ya envia a AEAT.
- No debe modificar una factura emitida para adaptarse tarde a un envio fiscal.

## Politica de automatizacion

Estado: pendiente.

Por que todavia no se decide:

- Automatizar emision, PDF, contabilidad, VeriFactu o email puede ser correcto para algunos casos y riesgoso para otros.

Dominios afectados:

- Checkout, pedidos, facturacion, PDF, contabilidad, VeriFactu, email y admin.

No debe asumirse mientras siga abierta:

- No debe activarse automatizacion global sin flag, observabilidad y criterios.
- No debe bloquearse el pedido ni el pago por fallo documental posterior.

## Tratamiento final de `Orders.invoice_number`

Estado: pendiente.

Por que todavia no se decide:

- El campo existe por compatibilidad y todavia puede ser leido por pantallas o historicos.

Dominios afectados:

- Pedidos, facturacion, admin, Mi Cuenta, PDFs legacy y migraciones.

No debe asumirse mientras siga abierta:

- No debe tratarse como fuente fiscal principal.
- No debe eliminarse sin auditoria de lecturas y migracion compatible.

## Conservacion y migracion de PDFs legacy

Estado: pendiente.

Por que todavia no se decide:

- Existen PDFs y rutas legacy que deben seguir siendo accesibles, pero los PDFs nuevos deben generarse desde snapshot.

Dominios afectados:

- Facturacion, PDF, descargas, admin, Mi Cuenta, almacenamiento y migracion.

No debe asumirse mientras siga abierta:

- No debe regenerarse un PDF historico como si garantizara inmutabilidad fiscal.
- No debe borrarse o mover PDFs legacy sin plan de conservacion.
