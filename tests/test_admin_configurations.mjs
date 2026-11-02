import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { runInNewContext } from 'node:vm';

const script = readFileSync(new URL('../src/static/js/admin_configurations.js', import.meta.url), 'utf8');

test('measure selector displays exactly the selected distribution', () => {
  const panels = ['height', 'width', 'area'].map((measure) => ({ dataset: { measure }, hidden: measure !== 'height' }));
  let onChange;
  const select = { value: 'height', addEventListener: (event, callback) => {
    assert.equal(event, 'change');
    onChange = callback;
  } };
  runInNewContext(script, { document: {
    getElementById: (id) => id === 'config-measure' ? select : null,
    querySelectorAll: () => panels,
  } });
  assert.equal(typeof onChange, 'function');
  for (const measure of ['width', 'area', 'height']) {
    select.value = measure;
    onChange();
    assert.deepEqual(panels.filter((panel) => !panel.hidden).map((panel) => panel.dataset.measure), [measure]);
  }
});

test('other admin pages without the selector are unaffected', () => {
  runInNewContext(script, { document: { getElementById: () => null } });
});
