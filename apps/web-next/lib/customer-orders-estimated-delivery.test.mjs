import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { formatCivilDateEs } from "./delivery-estimate.ts";

assert.equal(formatCivilDateEs("2026-08-14"), "14 de agosto de 2026");
assert.equal(formatCivilDateEs("2026-01-01"), "1 de enero de 2026");
assert.equal(formatCivilDateEs("2026-02-30"), null);

const sources = Object.fromEntries(
  await Promise.all(
    [
      ["client", "customer-orders-client.ts"],
      ["list", "../components/account/CustomerOrdersList.tsx"],
      ["detail", "../components/account/CustomerOrderDetailView.tsx"]
    ].map(async ([name, path]) => [name, await readFile(new URL(path, import.meta.url), "utf8")])
  )
);

assert.match(sources.client, /estimated_delivery_at: string \| null/);
assert.match(sources.client, /isNullableCivilDate\(value\.estimated_delivery_at\)/);
assert.match(sources.client, /formatCivilDateEs\(value\) !== null/);

for (const view of [sources.list, sources.detail]) {
  assert.match(view, /<strong>Entrega estimada:<\/strong>/);
  assert.match(view, /Fecha orientativa sujeta al proceso de fabricación y transporte\./);
  assert.match(view, /<time dateTime=/);
  assert.match(view, /estimatedDeliveryDate \?/);
  assert.doesNotMatch(view, /fetchDeliveryEstimate|<DeliveryEstimate/);
  assert.doesNotMatch(view, /sin asignar|pendiente de entrega/i);
}

assert.equal((sources.list.match(/<strong>Entrega estimada:<\/strong>/g) || []).length, 1);
assert.equal((sources.detail.match(/<strong>Entrega estimada:<\/strong>/g) || []).length, 1);

console.log("20 customer order estimated delivery assertions passed");
