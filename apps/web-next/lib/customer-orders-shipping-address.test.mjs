import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [client, detail] = await Promise.all([
  readFile(new URL("./customer-orders-client.ts", import.meta.url), "utf8"),
  readFile(
    new URL("../components/account/CustomerOrderDetailView.tsx", import.meta.url),
    "utf8"
  )
]);

assert.match(client, /address: string \| null/);
assert.match(client, /postal_code: string \| null/);
assert.match(client, /isNullableString\(value\.address\)/);
assert.match(client, /isNullableString\(value\.postal_code\)/);
assert.match(detail, /shippingAddress\.address/);
assert.match(detail, /shippingAddress\.postal_code/);
assert.match(detail, /Ayuda con tu reja/);
assert.match(detail, /href="\/instalation-rejas-para-ventanas"/);
assert.match(detail, /href="\/mantenimiento-acabado-rejas-metalicas"/);
assert.match(detail, /Mantenimiento y acabado/);

console.log("9 customer order shipping address assertions passed");
