import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { runInNewContext } from 'node:vm';

const script = readFileSync(new URL('../src/static/js/admin_product_evolution.js', import.meta.url), 'utf8');

test('year, metric and product controls update one chart without reloading', async () => {
  const listeners = {};
  const inputs = [];
  const options = { querySelectorAll: () => inputs.filter(input => input.checked),
    replaceChildren: () => { inputs.length = 0; }, append: label => inputs.push(label.input),
    addEventListener: (name, handler) => { listeners.options = handler; } };
  const year = { value: '2026', addEventListener: (name, handler) => { listeners.year = handler; } };
  const metric = { value: 'units', addEventListener: (name, handler) => { listeners.metric = handler; } };
  const message = { hidden: false, textContent: '' };
  const plot = { hidden: true, querySelector: () => ({ getContext: () => ({}) }) };
  const root = { dataset: { url: '/admin/product-evolution-data' } };
  const elements = { 'product-evolution': root, 'product-year': year, 'product-metric': metric,
    'product-options': options, 'product-message': message, 'product-chart': plot };
  const calls = [];
  const charts = [];
  const document = { addEventListener: (name, handler) => { listeners.ready = handler; },
    getElementById: id => elements[id], createElement: () => ({ append(input) { this.input = input; } }) };
  const payload = (selected) => ({ year: Number(year.value), months: Array(12).fill('Mes'),
    future: Array(12).fill(false), current_month: null,
    options: Array.from({ length: 6 }, (_, index) => ({ id: index + 1, name: `Modelo ${index + 1}` })),
    selected, series: Object.fromEntries(selected.map(id => [id, {
      units: Array(12).fill(2), orders: Array(12).fill(1), amount: Array(12).fill(20)
    }])) });
  class Chart {
    constructor(context, config) { this.data = config.data; this.options = config.options; charts.push(this); }
    resize() {}
    update() {}
  }
  runInNewContext(script, { document, Chart, URL, AbortController, Intl, window: { location: { href: 'https://example.test/admin/' } },
    fetch: async url => {
      calls.push(String(url));
      const ids = url.searchParams.getAll('product_id').map(Number);
      return { ok: true, json: async () => payload(ids.length ? ids : [1, 2, 3]) };
    } });
  listeners.ready();
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(charts.length, 1);
  assert.equal(charts[0].data.datasets.length, 3);
  metric.value = 'amount';
  listeners.metric();
  assert.equal(charts[0].data.datasets[0].data[0], 20);
  assert.equal(calls.length, 1);
  inputs[3].checked = true;
  inputs[4].checked = true;
  listeners.options({ target: inputs[4] });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(charts[0].data.datasets.length, 5);
  inputs[5].checked = true;
  listeners.options({ target: inputs[5] });
  assert.equal(inputs[5].checked, false);
  assert.equal(calls.length, 2);
  year.value = '2025';
  listeners.year();
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(charts[0].data.datasets.length, 3);
  assert.equal(new URL(calls[2]).searchParams.get('year'), '2025');
});
