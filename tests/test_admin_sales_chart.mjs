import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { runInNewContext } from 'node:vm';

test('commercial chart switches units without navigation and hides future months', () => {
  let onReady;
  let onChange;
  let updates = 0;
  let chart;
  const activity = (amounts, counts, units, tickets, future, currentMonth) =>
    ({ amounts, counts, units, tickets, future, current_month: currentMonth });
  const canvas = {
    id: 'salesChart-2026',
    dataset: {
      labels: JSON.stringify(['Jan', 'Feb', 'Mar']),
      selected: JSON.stringify(activity([10, 0, 0], [2, 0, 0], [5, 0, 0], [5, 0, 0],
        [false, false, true], 2)),
      previous: JSON.stringify(activity([4, 6, 8], [1, 2, 3], [1, 2, 3], [4, 3, 2.67],
        [false, false, true], null)),
      summaries: JSON.stringify({
        amounts: { current: 10, previous: 10, delta: 0, percent: 0 },
        counts: { current: 2, previous: 3, delta: -1, percent: -33.33 },
        units: { current: 5, previous: 0, delta: 5, percent: null },
        tickets: { current: 5, previous: 3.33, delta: 1.67, percent: 50.15 },
      }),
      previousYear: '2025',
      partial: 'true',
    },
    getContext: () => ({}),
    setAttribute(name, value) { this[name] = value; },
  };
  const metric = {
    value: 'amount',
    addEventListener(name, handler) { if (name === 'change') onChange = handler; },
  };
  const compare = { checked: false, addEventListener(name, handler) { this.onChange = handler; } };
  const summary = { hidden: true, textContent: '' };
  const document = {
    addEventListener(name, handler) { if (name === 'DOMContentLoaded') onReady = handler; },
    querySelector: () => canvas,
    getElementById: (id) => ({ 'sales-metric': metric, 'sales-compare': compare,
      'sales-summary': summary })[id],
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
  metric.value = 'units';
  compare.checked = true;
  compare.onChange();
  assert.equal(chart.data.datasets.length, 2);
  assert.deepEqual(Array.from(chart.data.datasets[0].data), [5, 0, null]);
  assert.deepEqual(Array.from(chart.data.datasets[1].data), [1, 2, null]);
  assert.equal(chart.options.plugins.legend.display, true);
  assert.match(summary.textContent, /Sin base comparable/);
  assert.equal(summary.hidden, false);
  metric.value = 'tickets';
  onChange();
  assert.equal(chart.options.scales.y.title.text, 'Ticket medio (€)');
  compare.checked = false;
  compare.onChange();
  assert.equal(chart.data.datasets.length, 1);
  assert.equal(summary.hidden, true);
});
