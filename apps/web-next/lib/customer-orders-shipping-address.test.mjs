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
assert.match(detail, /order\.shipping_address\.address/);
assert.match(detail, /order\.shipping_address\.postal_code/);

console.log("6 customer order shipping address assertions passed");
