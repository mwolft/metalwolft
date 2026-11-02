import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { runInNewContext } from 'node:vm';

const script = readFileSync(new URL('../src/static/js/admin_google_ads_monthly.js', import.meta.url), 'utf8');

test('cost, registered amount and order count retain separate axes and missing months', () => {
  let ready;
  let config;
  const canvas = { dataset: {
    labels: '["2025-06","2025-07","2025-08"]', costs: '[0,null,172.12]',
    sales: '[0,50,0]', orders: '[0,1,0]', future: '[false,false,false]',
    partial: '[true,false,false]'
  }, getContext: () => ({}) };
  class Chart { constructor(context, options) { config = options; } }
  runInNewContext(script, { Chart, Intl, document: {
    addEventListener: (name, callback) => { ready = callback; },
    getElementById: id => id === 'ads-monthly-chart' ? canvas : null
  } });
  ready();
  assert.equal(config.type, 'line');
  assert.equal(config.data.datasets.map(series => series.yAxisID).join(','), 'yAds,ySales,yOrders');
  assert.equal(config.data.datasets[0].data[1], null);
  assert.match(config.data.labels[0], /cobertura parcial/);
  assert.equal(config.options.scales.yOrders.ticks.precision, 0);
});
