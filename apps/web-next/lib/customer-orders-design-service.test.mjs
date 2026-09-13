import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [client, list, detail] = await Promise.all([
  readFile(new URL("./customer-orders-client.ts", import.meta.url), "utf8"),
  readFile(new URL("../components/account/CustomerOrdersList.tsx", import.meta.url), "utf8"),
  readFile(new URL("../components/account/CustomerOrderDetailView.tsx", import.meta.url), "utf8")
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
assert.match(detail, /Entrega: te avisaremos cuando esté listo\./);
assert.match(detail, /Plazo estimado:/);
assert.match(detail, /designService\?\.result_available/);
assert.match(detail, /Descargar diseño/);
assert.match(detail, /\{!isDesignService \? <section className="mw-customer-order-guides"/);

console.log("18 design-service customer order assertions passed");
