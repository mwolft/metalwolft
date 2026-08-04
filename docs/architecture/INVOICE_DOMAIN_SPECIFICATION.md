# MetalWolft Invoice Domain Specification

## 1. Propósito y alcance

Este documento define el comportamiento estable del dominio documental, fiscal y contable de MetalWolft. Debe servir como referencia para futuras implementaciones de facturas, facturas manuales, rectificativas, albaranes, PDF, email, registro contable, exportación Excel y adaptación VeriFactu.

El dominio existe para separar correctamente la operación comercial, el cobro, la documentación fiscal, la expedición física y la contabilidad interna.

Flujo activo de checkout:

```text
Pago confirmado
    ↓
CheckoutSession
    ↓
Pedido
    ↓
Email de confirmación
```

Flujo documental objetivo:

```text
Pedido pagado
    ↓
Emisión de factura
    ↓
Snapshot fiscal inmutable
    ↓
Número fiscal
    ↓
PDF
    ↓
VeriFactu
    ↓
Registro contable
    ↓
Excel de ingresos
```

Flujo operativo paralelo:

```text
Pedido
    ↓
Preparación o expedición
    ↓
Albarán
```

El albarán no condiciona el nacimiento de la factura.

Queda fuera de la primera implementación:

- Facturas rectificativas completas.
- Facturas simplificadas.
- Múltiples series complejas.
- Pedidos gratuitos.
- OCR de gastos.
- Automatización total.
- Integración real con VeriFactu.

El diseño no debe impedir incorporar estos elementos en fases posteriores.

## 2. Principios obligatorios

1. Flask es la autoridad del dominio.
2. Next.js no calcula datos fiscales ni decide importes finales.
3. Pedido, pago, factura, albarán y registro contable son entidades diferentes.
4. Una factura emitida es inmutable.
5. El PDF es una representación de la factura, no la factura misma.
6. Excel es una exportación regenerable, no el origen de verdad.
7. VeriFactu es un adaptador fiscal externo, no el núcleo del dominio.
8. El número de factura se asigna únicamente al emitir.
9. No se reservan números fiscales.
10. La emisión debe ser idempotente.
11. Un fallo de PDF, email, Excel o VeriFactu no debe provocar una segunda factura.
12. Los datos históricos deben seguir siendo accesibles.

## 3. Glosario de entidades

### CheckoutSession

Representa el proceso técnico de checkout y pago. Guarda el estado del intento de pago, referencias del proveedor, `quote_snapshot` y `customer_snapshot`.

No es documento fiscal. No debe contener número de factura. Puede existir sin pedido si el pago no se completa.

### Payment

Representa el cobro o intento de cobro. Puede materializarse hoy mediante Stripe o PayPal y se identifica por referencias externas como `payment_intent_id`, `provider_order_id` o `provider_capture_id`.

No es pedido ni factura. Un pago confirmado habilita la creación del pedido y, posteriormente, la emisión fiscal.

### Order

Representa la operación comercial. Puede existir sin factura y sin albarán.

En el sistema actual, `Orders` conserva `invoice_number` como campo legacy duplicado. Durante la migración debe mantenerse sincronizado con la factura ordinaria emitida hasta poder retirarlo de forma segura.

### Invoice

Representa el documento fiscal emitido. Debe tener identidad propia, número fiscal, fecha de emisión, fecha de operación cuando proceda, snapshot fiscal y estado fiscal.

Una factura emitida no se edita. Los cambios posteriores se resolverán mediante documentos adicionales, como rectificativas futuras.

### InvoiceSnapshot

Representa todos los datos fiscales congelados en el momento de emisión. Es la fuente de verdad para PDF, registro contable, exportaciones y adaptadores fiscales.

No debe depender de consultas dinámicas posteriores a `Order`, `OrderDetails`, `Products` o `Users`.

### DeliveryNote

Representa la expedición física o parte de entrega. Puede haber varios albaranes por pedido en el futuro.

No es factura. No modifica la factura.

### AccountingEntry

Representa el reflejo contable interno de una factura emitida. Debe poder reconstruirse desde la factura y su snapshot.

No es el origen fiscal, sino una proyección interna para gestión contable y exportación.

### VeriFactuRecord

Representa el estado y resultado de comunicación con VeriFactu. Debe estar vinculado a una factura emitida y debe ser reintentable.

VeriFactu no debe ser el núcleo de la factura. Es un adaptador externo con trazabilidad propia.

## 4. Invariantes del dominio

### Invariantes obligatorios desde la primera versión

- Un pedido puede existir sin factura.
- Un pedido pagado puede estar pendiente de facturación.
- Un pedido puede tener como máximo una factura ordinaria inicial.
- Las facturas manuales legacy pueden no tener `order_id`.
- Una factura emitida nunca se edita.
- Una factura emitida siempre tiene snapshot.
- Una factura emitida siempre tiene número único.
- El número no puede cambiar.
- El snapshot no puede cambiar.
- PDF, email, Excel y VeriFactu pueden reintentarse.
- La emisión de factura no puede repetirse.
- El PDF no es condición de existencia fiscal.
- El email no es condición de existencia fiscal.
- Los datos vivos del pedido no pueden alterar una factura emitida.
- Next.js no puede enviar importes fiscales autoritativos.

### Invariantes previstas para fases futuras

- Los cambios fiscales posteriores se resuelven con documentos adicionales.
- Las rectificativas se enlazan a la factura original.
- El registro contable debe poder reconstruirse desde la factura.
- El Excel debe poder regenerarse desde datos internos.
- El albarán no modifica la factura.
- VeriFactu debe registrar huella, respuesta, estado e intentos.
- Una factura registrada fiscalmente no puede modificarse.

## 5. Relación entre entidades

```text
Order
├── Payments: 0..N
├── Invoice ordinary: 0..1
├── Corrective invoices: 0..N futuro
└── Delivery notes: 0..N

Invoice
├── InvoiceSnapshot: 1
├── PDF artifacts: 0..N
├── Email deliveries: 0..N
├── AccountingEntry: 0..1
└── VeriFactuRecord: 0..N

Manual legacy Invoice
└── Order: 0..1
```

Compatibilidad:

- Las facturas antiguas sin pedido deben seguir siendo legibles.
- Las facturas manuales sin `order_id` deben conservarse.
- Las nuevas facturas ordinarias de pedido deben imponer relación única `Order 1 -> Invoice 0..1`.
- Las futuras rectificativas deben usar una relación explícita con la factura original, no reutilizar la factura ordinaria.
- `invoice_type` representa la naturaleza fiscal de la factura, no su origen.
- Valores iniciales de `invoice_type`: `ordinary` y `corrective`.
- Las facturas históricas pueden permanecer con `invoice_type = NULL`.
- La unicidad se aplica únicamente a facturas `ordinary` con `order_id`.
- Las futuras rectificativas podrán compartir el mismo pedido.
- `issuance_source` representa el origen operativo (`manual`, `automatic`, `legacy`) y no debe mezclarse con `invoice_type`.

## 6. Invoice Snapshot

El snapshot fiscal es la pieza central del dominio. Debe construirse una sola vez durante la emisión y persistirse junto a la factura. Toda representación posterior debe partir de este snapshot.

Estructura lógica inicial:

```json
{
  "schema_version": 1,
  "issuer": {},
  "customer": {},
  "operation": {},
  "lines": [],
  "totals": {},
  "payment": {},
  "references": {}
}
```

### Emisor

Debe incluir:

- Nombre o razón social.
- NIF.
- Domicilio fiscal.
- Datos de contacto relevantes.

Fuente prevista:

- Configuración fiscal del emisor gestionada en backend.
- No debe estar hardcodeada en renderers PDF a largo plazo.

### Cliente

Debe incluir:

- Nombre o razón social.
- NIF/NIE/CIF en toda nueva factura ordinaria F1 procedente del checkout.
- Dirección fiscal.
- Email.
- Teléfono solo si se decide conservarlo como dato auxiliar.

Los snapshots históricos pueden conservar `tax_id = null` y deben seguir siendo legibles. Esta compatibilidad no permite construir una nueva factura ordinaria F1 sin identificación fiscal.

Fuentes posibles:

- `CheckoutSessions.customer_snapshot`.
- `OrderDetails` legacy para pedidos antiguos.
- `Users` solo como fallback durante migración, nunca como fuente dinámica tras emitir.

### Operación

Debe incluir:

- Fecha de operación.
- Fecha de emisión.
- Moneda.
- Tipo de factura.
- Pedido de origen.
- Referencias externas.

Fuentes posibles:

- `Order.order_date`.
- `CheckoutSessions.created_at` o estado de pago confirmado.
- Configuración fiscal y decisión administrativa en el momento de emisión.

### Líneas

Cada línea debe congelar:

- Descripción.
- Modelo.
- Cantidad.
- Medidas.
- Anclaje.
- Color.
- Precio unitario.
- Descuento de línea, si existiera.
- Base imponible.
- Tipo de IVA.
- Cuota de IVA.
- Total.

Fuentes posibles:

- `CheckoutSessions.quote_snapshot.lines`.
- `OrderDetails`.
- `Products` solo en el momento de construir el snapshot para enriquecer descripción, nunca después.

### Totales

Debe incluir:

- Subtotal.
- Descuento.
- Envío.
- Base imponible.
- Cuota de IVA.
- Total.
- Redondeos si existieran.

Fuentes posibles:

- `CheckoutSessions.quote_snapshot`.
- `Order.total_amount`, `Order.shipping_cost`, `Order.discount_code`, `Order.discount_value`.

Regla:

- La factura no debe recalcular totales desde Next.js.
- La factura no debe recalcular totales desde productos vivos después de emitir.
- Los cálculos deben ser realizados por Flask y congelados en el snapshot.

### Pago

Debe incluir:

- Proveedor.
- Estado confirmado.
- Referencia externa.
- Fecha del cobro.

Fuentes posibles:

- `CheckoutSessions.payment_provider`.
- `CheckoutSessions.payment_intent_id`.
- `CheckoutSessions.provider_order_id`.
- `CheckoutSessions.provider_capture_id`.
- `CheckoutSessions.provider_status`.

### Referencias

Debe incluir:

- `order_id`.
- `order_locator`.
- `checkout_session_id`.
- Referencia de pago externa.
- Referencias de factura original si en el futuro es rectificativa.

## 7. Numeración

Principios:

- Debe existir una única fuente de numeración.
- La serie debe ser explícita.
- El ejercicio debe ser explícito.
- El contador debe estar persistido.
- Debe existir constraint único sobre serie, ejercicio y número.
- La asignación debe ocurrir dentro de la transacción de emisión.
- No se debe buscar simplemente la última factura.
- La concurrencia debe ser segura.
- No se reserva número antes de emitir.
- Si la transacción hace rollback, el número no debe considerarse emitido.
- Los números históricos se conservan aunque usen formatos anteriores.

Formato cerrado para nuevas emisiones:

- Facturas ordinarias: `FYYYYNNNNNN`.
- Facturas rectificativas futuras: `RYYYYNNNNNN`.
- Ejemplo ordinaria: `F2026000001`.
- Ejemplo rectificativa futura: `R2026000001`.
- La secuencia reinicia por serie y ejercicio.
- Las series mensuales históricas quedan congeladas.
- El nuevo motor no volverá a crear series por mes.
- El número no se reserva fuera de la transacción de emisión.
- El formato de una serie activa no se modifica después de entrar en producción.

Problemas actuales reconocidos:

- Existen dos generadores.
- Existen dos formatos.
- `Orders.invoice_number` duplica información fiscal.
- El generador de `Invoices` solo mira la tabla `invoices`.
- El generador de `Orders` mira `orders` e `invoices` con SQL manual.

Durante la migración:

- No se elimina `Orders.invoice_number`.
- Debe mantenerse sincronizado cuando se emita una factura ordinaria.
- Debe quedar documentado como campo legacy.
- Las nuevas emisiones deben usar el nuevo mecanismo centralizado.

## 8. Ciclo de vida

No debe usarse un único estado para todo. El estado fiscal de la factura es independiente de PDF, email, VeriFactu y contabilidad.

### Estado fiscal principal

```text
pending_issue
issued
canceled futuro
corrected futuro
```

### Estado PDF

```text
pending
generated
failed
```

### Estado email

```text
pending
sent
failed
```

### Estado VeriFactu

```text
not_required
pending
registered
failed
```

### Estado contable

```text
pending
recorded
failed
```

`email_sent` o `pdf_generated` no sustituyen al estado fiscal porque una factura puede estar emitida aunque falle el PDF o el email. Del mismo modo, un PDF generado sin factura persistida no constituye una factura emitida.

## 9. Contrato de emisión

Contrato conceptual:

```python
issue_invoice_for_order(order_id)
```

Debe:

1. Comprobar que el pedido existe.
2. Comprobar que está pagado.
3. Comprobar que es facturable.
4. Devolver la factura existente si ya fue emitida.
5. Construir el snapshot fiscal.
6. Obtener un número seguro.
7. Persistir la factura y el snapshot.
8. Enlazarla con el pedido.
9. Confirmar la transacción.
10. Disparar o dejar pendientes los efectos secundarios.

No debe:

- Generar otra factura en un reintento.
- Depender del frontend.
- Confiar en importes enviados por Next.
- Enviar email antes de confirmar la factura.
- Considerar el PDF como condición de existencia fiscal.
- Escribir directamente en Excel dentro de la transacción principal.
- Llamar a VeriFactu antes de persistir una factura estable.

Concurrencia:

- Dos llamadas simultáneas para el mismo pedido deben terminar con una sola factura ordinaria.
- La segunda llamada debe devolver la factura existente o fallar de forma controlada y recuperable.
- La unicidad debe apoyarse en constraints de base de datos, no solo en comprobaciones Python.

Reintentos:

- Si la factura ya existe, no se crea otra.
- Si falló el PDF, se reintenta PDF.
- Si falló email, se reintenta email.
- Si falló VeriFactu, se reintenta el registro.
- Ningún reintento de efecto secundario crea una nueva factura.

## 10. Efectos secundarios

Después de emitir pueden ejecutarse de forma independiente:

- Generación de PDF.
- Email.
- Registro contable.
- Exportación Excel.
- Comunicación VeriFactu.

Cada efecto debe ser:

- Reintentable.
- Trazable.
- Idempotente.
- Incapaz de crear una nueva factura.

La infraestructura puede ser síncrona controlada, eventos internos o cola futura. El contrato del dominio no depende de esa decisión.

## 11. PDF

Reglas:

- Se genera desde el snapshot.
- Contiene número y fechas definitivas.
- No consulta datos vivos.
- Puede regenerarse de manera determinista.
- Regenerar no altera la factura.
- Los PDFs históricos legacy deben conservarse.
- Los PDFs nuevos deben poder reconstruirse desde el snapshot.

Problema actual reconocido:

- La regeneración actual puede reconstruir desde datos vivos de pedido/productos, por lo que no es suficiente para facturas nuevas con exigencia de inmutabilidad.

## 12. Email

Reglas:

- Se envía después de emitir.
- Puede fallar sin invalidar la factura.
- Debe poder reintentarse.
- Debe existir trazabilidad.
- No debe provocar una segunda emisión.
- No debe adjuntar un PDF generado a partir de datos vivos.

El email de confirmación de pedido y el email de factura son comunicaciones distintas.

## 13. Registro contable y Excel

Arquitectura:

```text
Invoice issued
    ↓
AccountingEntry
    ↓
Excel / CSV / futura integración
```

El registro contable interno debe guardar al menos:

- Referencia de factura.
- Fecha.
- Serie y número.
- Cliente.
- NIF.
- Base imponible.
- IVA.
- Total.
- Método de pago.
- Pedido.
- Estado de exportación.

El Excel de ingresos:

- No se edita como origen maestro.
- Debe poder regenerarse.
- No debe bloquear la emisión.
- Puede exportarse bajo demanda o sincronizarse.
- Debe permitir el formato futuro necesario para libros de ingresos e IVA.

No se define todavía el Excel físico ni sus columnas definitivas.

## 14. VeriFactu

Requisitos conocidos del dominio:

- Debe existir un adaptador separado.
- Debe existir registro de estado.
- Debe existir identificación idempotente.
- Debe almacenarse la respuesta.
- Los errores deben ser reintentables.
- Debe haber trazabilidad.
- Debe relacionarse con una factura emitida.
- No debe modificar una factura tras registrarla.
- Debe preparar el camino para rectificativas.

Hipótesis pendientes de validación normativa:

- Formato definitivo de huella o encadenamiento.
- Campos exactos exigidos por VeriFactu.
- Plazos y condiciones de comunicación.
- Requisitos concretos para rectificativas.
- Representación exacta en PDF o QR si aplica.

VeriFactu no debe decidir si una factura existe. La factura existe cuando se emite y persiste con número y snapshot.

## 15. Albaranes

El albarán representa expedición o entrega física.

Reglas:

- Un pedido puede tener cero o varios albaranes.
- El albarán puede crearse después del pedido.
- El albarán no crea factura.
- El albarán no modifica factura.
- El albarán puede reutilizar datos operativos del pedido.
- En el futuro podrá tener PDF propio sin precios fiscales si se decide.

## 16. Compatibilidad legacy

Principio obligatorio:

> La nueva arquitectura se aplicará a nuevas emisiones sin reescribir automáticamente las facturas históricas.

Estrategia:

- Facturas antiguas siguen en `Invoices`.
- Formatos antiguos de numeración se conservan.
- `Orders.invoice_number` se mantiene durante la migración.
- Facturas manuales sin pedido se conservan.
- PDFs históricos se siguen sirviendo por las rutas actuales.
- React Admin existente debe seguir pudiendo listar y descargar facturas existentes.
- La regeneración histórica solo debe usarse con cautela y no debe considerarse garantía fiscal para nuevas facturas.

Problemas actuales reconocidos:

- Dos generadores de numeración.
- Dos formatos de número.
- `Orders.invoice_number` duplicado.
- `Invoices.order_id` no único.
- Regeneración desde datos vivos.
- Varias rutas legacy.
- Posibilidad de edición desde administración.
- Facturas manuales históricas.

Estos problemas deben convivir durante la migración. No deben eliminarse de golpe.

## 17. Seguridad y permisos

Reglas:

- Solo administradores pueden emitir manualmente.
- El endpoint de emisión debe validar autorización.
- No se aceptan importes fiscales desde Next.
- No se exponen errores internos.
- Se registra quién emitió manualmente.
- Las operaciones sensibles dejan trazabilidad.
- Una factura emitida no puede editarse desde React Admin.

React Admin podrá mostrar facturas emitidas, pero no debe permitir cambiar número, snapshot, importes o datos fiscales de una factura emitida.

## 18. Observabilidad y auditoría

Hechos que deben poder investigarse:

- Fecha de emisión.
- Actor.
- Origen manual o automático.
- Intentos de emisión.
- Errores de emisión.
- PDF generado.
- Error de PDF.
- Email enviado.
- Error de email.
- VeriFactu registrado.
- Error VeriFactu.
- Registro contable creado.
- Exportación realizada.

No se requiere un sistema complejo de logs en la primera fase, pero el modelo debe reservar suficiente trazabilidad para auditar operaciones sensibles.

## 19. Migración progresiva

### 1. Documento de dominio

Objetivo: fijar invariantes y lenguaje común.

Riesgo principal: bajo.

Criterio de aceptación: documento versionado y revisado.

Queda fuera: cambios funcionales.

### 2. Snapshot fiscal y versión

Objetivo: añadir estructura de snapshot fiscal versionado para nuevas emisiones.

Riesgo principal: migración de datos incompleta.

Criterio de aceptación: facturas nuevas pueden guardar snapshot sin afectar históricas.

Queda fuera: VeriFactu y Excel.

### 3. Relación única pedido-factura

Objetivo: impedir más de una factura ordinaria inicial por pedido.

Riesgo principal: facturas legacy con `order_id` duplicado.

Criterio de aceptación: constraint o validación segura compatible con legacy.

Queda fuera: rectificativas.

### 4. Estados independientes

Objetivo: separar estado fiscal, PDF, email, VeriFactu y contabilidad.

Riesgo principal: pantallas admin aún esperan un estado simple.

Criterio de aceptación: las facturas emitidas pueden tener PDF/email fallidos sin perder estado fiscal.

Queda fuera: automatización.

### 5. Secuencia fiscal segura

Objetivo: introducir serie, ejercicio y contador seguro.

Riesgo principal: concurrencia y convivencia con formatos históricos.

Criterio de aceptación: dos emisiones concurrentes no duplican número.

Queda fuera: múltiples series complejas.

### 6. Servicio idempotente de emisión

Objetivo: implementar `issue_invoice_for_order(order_id)`.

Riesgo principal: crear duplicados por reintentos.

Criterio de aceptación: reintentar devuelve la misma factura.

Queda fuera: PDF/email obligatorios.

### 7. Endpoint administrativo

Objetivo: permitir emisión asistida desde backend admin.

Riesgo principal: permisos o errores no sanitizados.

Criterio de aceptación: solo admin puede emitir y se registra actor.

Queda fuera: emisión automática.

### 8. Vista de pendientes

Objetivo: mostrar pedidos pagados pendientes de factura.

Riesgo principal: confundir pedidos no pagados con pendientes fiscales.

Criterio de aceptación: vista lista solo pedidos facturables.

Queda fuera: gestión masiva.

### 9. PDF desde snapshot

Objetivo: generar PDF determinista desde `InvoiceSnapshot`.

Riesgo principal: diferencias visuales con PDFs históricos.

Criterio de aceptación: PDF nuevo no consulta datos vivos.

Queda fuera: firma o QR VeriFactu definitivo.

### 10. Email reintentable

Objetivo: enviar email de factura sin afectar emisión.

Riesgo principal: duplicar envíos.

Criterio de aceptación: email idempotente o trazado con intentos.

Queda fuera: automatización completa.

### 11. Registro contable

Objetivo: crear `AccountingEntry` desde factura emitida.

Riesgo principal: descuadres por redondeos.

Criterio de aceptación: registro reconstruible desde snapshot.

Queda fuera: Excel físico.

### 12. Exportación Excel

Objetivo: exportar ingresos desde registros internos.

Riesgo principal: usar Excel como origen maestro.

Criterio de aceptación: exportación regenerable bajo demanda.

Queda fuera: edición manual del libro.

### 13. Adaptador VeriFactu

Objetivo: registrar facturas emitidas ante el adaptador fiscal.

Riesgo principal: requisitos normativos incompletos.

Criterio de aceptación: estado, respuesta y errores trazados.

Queda fuera: rectificativas completas si no están definidas.

### 14. Automatización opcional

Objetivo: emitir automáticamente bajo condiciones controladas.

Riesgo principal: emitir facturas antes de validar excepciones comerciales.

Criterio de aceptación: automatización desactivable y observable.

Queda fuera: emisión para casos dudosos.

### 15. Albaranes

Objetivo: añadir documentación operativa de expedición.

Riesgo principal: mezclar albarán con factura.

Criterio de aceptación: albarán independiente y sin alterar factura.

Queda fuera: integración logística compleja.

## 20. Decisiones abiertas

No deben resolverse arbitrariamente:

- Datos fiscales exactos del emisor.
- Cuándo emitir automáticamente.
- Fecha de operación frente a fecha de emisión.
- Facturas rectificativas.
- Pedidos con total cero.
- Facturas manuales sin pedido.
- Varias expediciones.
- Formato contable del Excel.
- Integración concreta con VeriFactu.
- Tratamiento definitivo de `Orders.invoice_number`.
- Política de conservación de PDFs legacy.

## 21. Contradicciones actuales con el dominio objetivo

- El checkout ya no emite factura, pero existe un bloque legacy inalcanzable en `POST /api/orders` que conserva lógica inline de factura.
- Existen dos generadores de numeración y dos formatos.
- `Orders.invoice_number` duplica el número fiscal.
- `Invoices.order_id` no es único.
- `Invoices` permite edición de campos fiscales desde administración.
- La regeneración de PDF puede depender de datos vivos.
- `issue_invoice_for_order()` existe como servicio aislado, pero no es el único camino histórico de creación.
- `invoice_service.py` y `original_invoice_renderer.py` representan dos enfoques distintos de PDF.
- No existe estado fiscal separado de PDF, email, contabilidad o VeriFactu.
- No existe registro contable interno ni exportación Excel como proyección regenerable.

Estas contradicciones no deben resolverse en bloque. Deben guiar la migración incremental.
