import assert from "node:assert/strict";
import {
  DESIGN_SERVICE_DRAFT_STORAGE_KEY,
  DESIGN_SERVICE_DRAFT_VERSION,
  clearDesignServiceDraft,
  consumeDesignServiceDraft,
  loadDesignServiceDraft,
  normalizeDesignServiceDraftItems,
  saveDesignServiceDraft,
  startDesignServiceDraft
} from "./design-service-draft.ts";

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

const maryland = {
  product_id: 7,
  product_slug: "maryland",
  product_name: "Maryland",
  width_cm: 200,
  height_cm: 120
};

assert.deepEqual(normalizeDesignServiceDraftItems([maryland, { ...maryland }, { ...maryland, width_cm: 150 }]), [
  maryland,
  { ...maryland, width_cm: 150 }
]);
assert.deepEqual(normalizeDesignServiceDraftItems([{ ...maryland, product_id: 0 }]), []);

assert.deepEqual(saveDesignServiceDraft([maryland, { ...maryland }]), [maryland]);
assert.deepEqual(JSON.parse(storage.getItem(DESIGN_SERVICE_DRAFT_STORAGE_KEY)), {
  version: DESIGN_SERVICE_DRAFT_VERSION,
  items: [maryland]
});
assert.deepEqual(loadDesignServiceDraft(), [maryland]);

assert.deepEqual(consumeDesignServiceDraft(), [maryland]);
assert.equal(storage.getItem(DESIGN_SERVICE_DRAFT_STORAGE_KEY), null);

const albany = { ...maryland, product_id: 8, product_slug: "albany", product_name: "Albany" };
saveDesignServiceDraft([albany]);
assert.deepEqual(startDesignServiceDraft(maryland, false), [maryland]);
assert.equal(storage.getItem(DESIGN_SERVICE_DRAFT_STORAGE_KEY), null);

saveDesignServiceDraft([albany]);
assert.deepEqual(startDesignServiceDraft(null, false), []);
assert.equal(storage.getItem(DESIGN_SERVICE_DRAFT_STORAGE_KEY), null);

saveDesignServiceDraft([maryland, albany]);
assert.deepEqual(startDesignServiceDraft(null, true), [maryland, albany]);
assert.equal(storage.getItem(DESIGN_SERVICE_DRAFT_STORAGE_KEY), null);

storage.setItem(DESIGN_SERVICE_DRAFT_STORAGE_KEY, "not-json");
assert.deepEqual(loadDesignServiceDraft(), []);
assert.equal(storage.getItem(DESIGN_SERVICE_DRAFT_STORAGE_KEY), null);

storage.setItem(DESIGN_SERVICE_DRAFT_STORAGE_KEY, JSON.stringify({ version: 99, items: [maryland] }));
assert.deepEqual(loadDesignServiceDraft(), []);
assert.equal(storage.getItem(DESIGN_SERVICE_DRAFT_STORAGE_KEY), null);

saveDesignServiceDraft([maryland]);
clearDesignServiceDraft();
assert.equal(storage.getItem(DESIGN_SERVICE_DRAFT_STORAGE_KEY), null);

console.log("20 design service draft assertions passed");
