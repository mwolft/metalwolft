import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [client, list, detail, delivery, styles] = await Promise.all([
  readFile(new URL("./customer-orders-client.ts", import.meta.url), "utf8"),
  readFile(new URL("../components/account/CustomerOrdersList.tsx", import.meta.url), "utf8"),
  readFile(new URL("../components/account/CustomerOrderDetailView.tsx", import.meta.url), "utf8"),
  readFile(new URL("../components/account/DesignDeliveryView.tsx", import.meta.url), "utf8"),
  readFile(new URL("../app/globals.css", import.meta.url), "utf8")
]);

assert.match(client, /order_type: "physical"/);
assert.match(client, /order_type: "design_service"/);
assert.match(client, /shipping_address: null/);
assert.match(client, /line_type: "design_service"/);
assert.match(client, /result_available: boolean/);
assert.match(client, /fetchCustomerOrderDesignResult/);
assert.match(client, /fields\.order_type === "design_service"/);
assert.match(client, /fields\.shipping_address === null/);
assert.match(client, /lines\.every\(isCustomerDesignServiceOrderLine\)/);

assert.match(list, /Diseño previo a medida/);
assert.match(list, /order\.design_count/);
assert.match(detail, /Diseños incluidos/);
assert.match(detail, /designService\?\.status\.code === "delivered"/);
assert.match(detail, /Entrega: diseño disponible en esta página\./);
assert.match(detail, /Plazo estimado:/);
assert.match(detail, /designService\?\.result_available/);
assert.match(detail, /Descargar diseño/);
assert.match(detail, /designService\?\.result_available && !designDelivery/);
assert.match(detail, /downloadAll=\{designService\?\.result_available \?/);
assert.match(detail, /onClick: handleDownloadDesignResult/);
assert.match(client, /design_delivery\?: CustomerDesignDelivery/);
assert.match(client, /fetchCustomerDesignFile/);
assert.match(detail, /<DesignDeliveryView/);
assert.match(delivery, /ModernGrilleViewerLoader/);
assert.doesNotMatch(delivery, /Ver diseño en 3D/);
assert.match(delivery, /<PrivateModel orderId=\{orderId\}/);
assert.match(delivery, /IntersectionObserver/);
assert.match(delivery, /PrivateModelFallbackImage/);
assert.match(delivery, /URL\.revokeObjectURL/);
assert.match(delivery, /<h3 id="design-delivery-title">Diseños preparados<\/h3>/);
assert.match(delivery, /onClick=\{downloadAll\.onClick\}/);
assert.match(delivery, /Descargar todos los archivos/);
assert.match(delivery, /downloadAll\?\.error/);
assert.match(styles, /\.mw-design-delivery__heading\s*\{[^}]*flex-wrap: wrap;/s);
assert.match(delivery, /onClick=\{\(event\) => \{ event\.stopPropagation\(\); void download\(preview\.file\); \}\}/);
assert.match(detail, /\{!isDesignService \? <section className="mw-customer-order-guides"/);

console.log("25 design-service customer order assertions passed");
