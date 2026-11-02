import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { runInNewContext } from 'node:vm';

function harness(selectedAmounts = [10, 20, 0], previousAmounts = [5, 15, 0]) {
  const activity = (amounts, counts, units, tickets) => ({
    amounts, counts, units, tickets, future: [false, false, true], current_month: 2,
  });
  const canvas = {
    id: 'salesChart-2026', parentElement: { hidden: false },
    dataset: {
      labels: JSON.stringify(['Jan', 'Feb', 'Mar']),
      selected: JSON.stringify(activity(selectedAmounts, [2, 3, 0], [4, 0, 0], [5, 6.67, 0])),
      previous: JSON.stringify(activity(previousAmounts, [1, 2, 0], [1, 2, 0], [5, 7.5, 0])),
      summaries: JSON.stringify({
        amounts: { current: 30, previous: 20, delta: 10, percent: 50 },
        counts: { current: 5, previous: 3, delta: 2, percent: 66.67 },
        units: { current: 4, previous: 3, delta: 1, percent: 33.33 },
        tickets: { current: 6, previous: 6.67, delta: -0.67, percent: -10.04 },
      }),
      previousYear: '2025', partial: 'true',
    },
    getContext: () => ({}), setAttribute(name, value) { this[name] = value; },
  };
  const checkboxes = ['amount', 'orders', 'units', 'tickets'].map(value =>
    ({ value, checked: value === 'amount' || value === 'units' }));
  const metrics = {
    querySelectorAll: () => checkboxes.filter(item => item.checked),
    addEventListener(name, handler) { this.onChange = handler; },
  };
  const mode = { value: 'trend', addEventListener(name, handler) { this.onChange = handler; } };
  const compare = { checked: false, addEventListener(name, handler) { this.onChange = handler; } };
  const summary = {
    hidden: true, children: [], replaceChildren() { this.children = []; },
    appendChild(child) { this.children.push(child); },
  };
  const empty = { hidden: true, textContent: '' };
  const panels = checkboxes.map(({ value }) => {
    const plot = { getContext: () => ({}), setAttribute(name, text) { this[name] = text; } };
    return { dataset: { metric: value }, hidden: true, querySelector: () => plot };
  });
  const realCharts = { hidden: true, querySelectorAll: () => panels };
  const document = {
    addEventListener(name, handler) { if (name === 'DOMContentLoaded') this.onReady = handler; },
    querySelector: () => canvas,
    getElementById: id => ({ 'sales-metrics': metrics, 'sales-mode': mode,
      'sales-compare': compare, 'sales-summary': summary, 'sales-empty': empty,
      'sales-real-charts': realCharts })[id],
    createElement: () => ({ textContent: '' }),
  };
  const charts = [];
  class Chart {
    constructor(context, config) {
      this.data = config.data;
      this.options = config.options;
      this.type = config.type;
      charts.push(this);
    }
    update() { this.updates = (this.updates || 0) + 1; }
    resize() { this.resizes = (this.resizes || 0) + 1; }
  }
  runInNewContext(readFileSync(new URL('../src/static/js/admin_sales_chart.js', import.meta.url), 'utf8'),
    { document, Chart, Intl });
  document.onReady();
  return { canvas, checkboxes, metrics, mode, compare, summary, empty, panels, realCharts, charts };
}

test('multiple trends normalize independently, retain raw tooltip values and mask future', () => {
  const ui = harness();
  const chart = ui.charts[0];
  assert.equal(chart.type, 'line');
  assert.equal(chart.data.datasets.length, 2);
  assert.deepEqual(Array.from(chart.data.datasets[0].data), [100, 200, null]);
  assert.deepEqual(Array.from(chart.data.datasets[1].data), [100, 0, null]);
  assert.match(chart.data.labels[1], /en curso/);
  assert.match(chart.data.labels[2], /futuro/);
  const tooltip = chart.options.plugins.tooltip.callbacks.label({ dataset: chart.data.datasets[0], dataIndex: 1 });
  assert.match(tooltip, /20,00 €/);
  ui.checkboxes[1].checked = true;
  ui.metrics.onChange();
  assert.equal(chart.data.datasets.length, 3);
  ui.checkboxes.forEach(item => { item.checked = false; });
  ui.metrics.onChange();
  assert.equal(ui.empty.hidden, false);
  assert.equal(ui.canvas.parentElement.hidden, true);
});

test('prior year uses dashed lines and real values use separate charts', () => {
  const ui = harness();
  ui.compare.checked = true;
  ui.compare.onChange();
  assert.equal(ui.charts[0].data.datasets.length, 4);
  assert.deepEqual(Array.from(ui.charts[0].data.datasets[1].borderDash), [6, 4]);
  assert.equal(ui.charts[0].data.datasets[0].borderColor, ui.charts[0].data.datasets[1].borderColor);
  assert.match(ui.summary.children[1].textContent, /2026.*2025.*50/);
  ui.mode.value = 'real';
  ui.mode.onChange();
  assert.equal(ui.realCharts.hidden, false);
  assert.equal(ui.charts.length, 3);
  assert.deepEqual(Array.from(ui.charts[1].data.datasets[0].data), [10, 20, null]);
  assert.deepEqual(Array.from(ui.charts[2].data.datasets[0].data), [4, 0, null]);
});

test('zero-only trends show a clear indication without dividing by zero', () => {
  const ui = harness([0, 0, 0], [0, 0, 0]);
  ui.checkboxes[2].checked = false;
  ui.metrics.onChange();
  assert.equal(ui.canvas.parentElement.hidden, true);
  assert.equal(ui.empty.hidden, false);
  assert.match(ui.empty.textContent, /No hay valores/);
});
