import assert from "node:assert/strict";
import {
  DESIGN_SERVICE_REQUEST_STORAGE_KEY,
  DESIGN_SERVICE_REQUEST_STORAGE_VERSION,
  designServiceDraftKey,
  getOrCreateDesignServiceCreationKey,
  rememberDesignServiceRequest
} from "./design-service-request-session.ts";

class MemoryStorage {
  values = new Map();

  getItem(key) {
    return this.values.get(key) ?? null;
  }

  setItem(key, value) {
    this.values.set(key, String(value));
  }

  removeItem(key) {
    this.values.delete(key);
  }
}

const storage = new MemoryStorage();
globalThis.window = { sessionStorage: storage };

const designs = [
  { product_id: 7, width_cm: 200, height_cm: 120 },
  { product_id: 8, width_cm: 100, height_cm: 80 }
];

assert.equal(designServiceDraftKey(designs), designServiceDraftKey([...designs].reverse()));

const first = getOrCreateDesignServiceCreationKey(42, designs);
const retry = getOrCreateDesignServiceCreationKey(42, [...designs].reverse());
assert.equal(first.creation_key, retry.creation_key);
assert.equal(retry.design_request_id, undefined);

const completed = rememberDesignServiceRequest(42, designs, 12);
assert.equal(completed.design_request_id, 12);
assert.equal(getOrCreateDesignServiceCreationKey(42, designs).design_request_id, 12);

const otherUser = getOrCreateDesignServiceCreationKey(43, designs);
assert.notEqual(otherUser.creation_key, first.creation_key);

storage.setItem(DESIGN_SERVICE_REQUEST_STORAGE_KEY, "not-json");
const recovered = getOrCreateDesignServiceCreationKey(42, designs);
assert.equal(recovered.version, DESIGN_SERVICE_REQUEST_STORAGE_VERSION);
assert.equal(recovered.design_request_id, undefined);

console.log("8 design service request session assertions passed");
