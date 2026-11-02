import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { runInNewContext } from 'node:vm';

test('commercial chart switches units without navigation and hides future months', () => {
  let onReady;
  let onChange;
  let updates = 0;
  let chart;
  const canvas = {
    id: 'salesChart-2026',
    dataset: {
      labels: JSON.stringify(['Jan', 'Feb', 'Mar']),
      amounts: JSON.stringify([10, 0, 0]),
      orders: JSON.stringify([2, 0, 0]),
      future: JSON.stringify([false, false, true]),
      currentMonth: '2',
    },
    getContext: () => ({}),
    setAttribute(name, value) { this[name] = value; },
  };
  const metric = {
    value: 'amount',
    addEventListener(name, handler) { if (name === 'change') onChange = handler; },
  };
  const document = {
    addEventListener(name, handler) { if (name === 'DOMContentLoaded') onReady = handler; },
    querySelector: () => canvas,
    getElementById: () => metric,
  };
  class Chart {
    constructor(context, config) {
      this.data = config.data;
      this.options = config.options;
      chart = this;
      assert.equal(config.type, 'bar');
    }
    update() { updates++; }
  }

  runInNewContext(readFileSync(new URL('../src/static/js/admin_sales_chart.js', import.meta.url), 'utf8'),
    { document, Chart });
  onReady();
  assert.deepEqual(Array.from(chart.data.datasets[0].data), [10, 0, null]);
  assert.match(chart.data.labels[1], /en curso/);
  assert.match(chart.data.labels[2], /futuro/);
  metric.value = 'orders';
  onChange();
  assert.deepEqual(Array.from(chart.data.datasets[0].data), [2, 0, null]);
  assert.equal(chart.options.scales.y.title.text, 'Pedidos registrados');
  assert.equal(canvas['aria-label'], 'Pedidos registrados por mes en 2026');
  assert.equal(updates, 1);
});
