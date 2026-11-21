import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [list, detail, client, styles] = await Promise.all([
  readFile(new URL("../components/account/CustomerOrdersList.tsx", import.meta.url), "utf8"),
  readFile(new URL("../components/account/CustomerOrderDetailView.tsx", import.meta.url), "utf8"),
  readFile(new URL("./customer-orders-client.ts", import.meta.url), "utf8"),
  readFile(new URL("../app/globals.css", import.meta.url), "utf8")
]);

assert.match(list, /href=\{`\/mi-cuenta\/pedidos\/\$\{order\.id\}`\}/);
assert.match(list, /onClick=\{\(event\) => handleOpenOrder\(event, order\.id\)\}/);
assert.match(list, /openingOrderIdRef\.current !== null[\s\S]*?event\.preventDefault\(\)/);
assert.match(list, /setOpeningOrderId\(orderId\)/);
assert.match(list, /window\.setTimeout\(resetOpening, 15_000\)/);
assert.match(list, /window\.addEventListener\("pageshow", resetOpening\)/);
assert.match(list, /<MetalSpinner label="Abriendo pedido" \/>Abriendo pedido…/);
assert.match(list, /aria-busy=\{openingOrderId === order\.id\}/);
assert.match(styles, /\.mw-customer-order-card__open\s*\{[^}]*width: 13\.5rem;[^}]*max-width: 100%/s);
assert.match(styles, /@media \(prefers-reduced-motion: reduce\)[\s\S]*?\.mw-metal-spinner svg\s*\{\s*animation: none/s);
assert.match(detail, /fetchCustomerOrderDetail\(token, orderId\)/);
assert.match(client, /Authorization: `Bearer \$\{token\}`/);

console.log("Customer order opening feedback assertions passed");
