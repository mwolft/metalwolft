import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [layout, cartFlow, paymentStep, stripeSection] = await Promise.all([
  readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
  readFile(new URL("../components/cart/CartFlow.tsx", import.meta.url), "utf8"),
  readFile(new URL("../components/cart/CartPaymentStep.tsx", import.meta.url), "utf8"),
  readFile(new URL("../components/cart/StripePaymentSection.tsx", import.meta.url), "utf8")
]);

for (const source of [layout, cartFlow, paymentStep]) {
  assert.doesNotMatch(source, /@stripe\//);
  assert.doesNotMatch(source, /loadStripe\(/);
}

assert.match(cartFlow, /dynamic\(\s*\(\) => import\("@\/components\/cart\/CartPaymentStep"\)/s);
assert.match(paymentStep, /dynamic\(\s*\(\) => import\("@\/components\/cart\/StripePaymentSection"\)/s);
assert.match(paymentStep, /paymentMethod === "card"[\s\S]*?<StripePaymentSection/);
assert.match(stripeSection, /import \{ loadStripe \} from "@stripe\/stripe-js"/);
assert.match(stripeSection, /loadStripe\(stripePublishableKey\)/);

console.log("9 Stripe lazy-loading assertions passed");
