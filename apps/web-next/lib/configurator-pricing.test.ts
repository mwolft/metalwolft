import assert from "node:assert/strict";
import {
  ANCHORAGE_FRONT_PLATES,
  ANCHORAGE_INTERIOR_HOLES
} from "./configurator-options";
import { calculateConfiguratorPrice } from "./configurator-pricing";

type TestCase = {
  name: string;
  assertion: () => void;
};

const tests: TestCase[] = [];

function test(name: string, assertion: () => void) {
  tests.push({ name, assertion });
}

function unitPrice(input: {
  height: number;
  width: number;
  pricePerM2?: number;
  discountedPricePerM2?: number | null;
  anchorage?: typeof ANCHORAGE_INTERIOR_HOLES | typeof ANCHORAGE_FRONT_PLATES;
}) {
  const quote = calculateConfiguratorPrice({
    rawHeight: String(input.height),
    rawWidth: String(input.width),
    pricePerM2: input.pricePerM2 ?? 100,
    discountedPricePerM2: input.discountedPricePerM2 ?? null,
    anchorage: input.anchorage ?? ANCHORAGE_INTERIOR_HOLES
  });

  if (quote.ok === false) {
    throw new Error(quote.error);
  }

  return quote.unitPrice;
}

test("30x30 interiores = 95,00", () => {
  assert.equal(unitPrice({ height: 30, width: 30 }), 95);
});

test("30x30 pletinas = 119,95", () => {
  assert.equal(unitPrice({ height: 30, width: 30, anchorage: ANCHORAGE_FRONT_PLATES }), 119.95);
});

test("100x100 interiores con precio 100 = 100,00", () => {
  assert.equal(unitPrice({ height: 100, width: 100, pricePerM2: 100 }), 100);
});

test("100x100 pletinas con precio 100 = 124,95", () => {
  assert.equal(
    unitPrice({ height: 100, width: 100, pricePerM2: 100, anchorage: ANCHORAGE_FRONT_PLATES }),
    124.95
  );
});

test("suma 400 válida", () => {
  assert.equal(unitPrice({ height: 150, width: 250 }), 375);
});

test("suma 401 inválida", () => {
  const quote = calculateConfiguratorPrice({
    rawHeight: "151",
    rawWidth: "250",
    pricePerM2: 100,
    anchorage: ANCHORAGE_INTERIOR_HOLES
  });

  assert.equal(quote.ok, false);
  assert.match(quote.error, /400 cm/);
});

test("medida 29 inválida", () => {
  const quote = calculateConfiguratorPrice({
    rawHeight: "29",
    rawWidth: "100",
    pricePerM2: 100,
    anchorage: ANCHORAGE_INTERIOR_HOLES
  });

  assert.equal(quote.ok, false);
  assert.match(quote.error, /30 cm/);
});

test("medida 251 inválida", () => {
  const quote = calculateConfiguratorPrice({
    rawHeight: "251",
    rawWidth: "100",
    pricePerM2: 100,
    anchorage: ANCHORAGE_INTERIOR_HOLES
  });

  assert.equal(quote.ok, false);
  assert.match(quote.error, /250 cm/);
});

test("usa precio rebajado si existe", () => {
  assert.equal(unitPrice({ height: 100, width: 100, pricePerM2: 100, discountedPricePerM2: 80 }), 95);
});

test("área menor de 0,2 aplica multiplicador 3 y mínimo", () => {
  assert.equal(unitPrice({ height: 30, width: 30, pricePerM2: 300 }), 95);
});

test("redondeo a dos decimales", () => {
  assert.equal(unitPrice({ height: 100, width: 100, pricePerM2: 100.129 }), 100.13);
});

for (const { name, assertion } of tests) {
  assertion();
  console.log(`ok - ${name}`);
}

console.log(`${tests.length} configurator pricing tests passed`);
