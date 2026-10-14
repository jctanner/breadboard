'use strict';

// Execute the real console code with a minimal DOM; API reads hit only the
// isolated local mock relay started by reproduce.py.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const config = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const nodes = new Map();
class Element {
  constructor() { this.children = []; this.value = ''; this.textContent = ''; }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; }
  addEventListener() {}
  setAttribute() {}
  focus() {}
}
const element = id => {
  if (!nodes.has(id)) nodes.set(id, new Element());
  return nodes.get(id);
};
const context = vm.createContext({
  document: {
    getElementById: element,
    createElement: () => new Element(),
    createTextNode: value => value,
    querySelectorAll: () => [],
  },
  window: { location: { origin: config.base }, addEventListener() {} },
  FormData: class { *[Symbol.iterator]() {} },
  URLSearchParams,
  fetch: async (path, options) => {
    assert.equal(options.method, 'GET');
    assert.ok(path.startsWith('/api/private/v1/telemetry/requests?'));
    return fetch(config.base + path, options);
  },
});
vm.runInContext(fs.readFileSync(config.source, 'utf8'), context);
vm.runInContext(`state.key = ${JSON.stringify(config.admin_key)};`, context);
const integer = id => Number(element(id).textContent.replace(/\D/g, ''));
const snapshot = stage => ({
  stage,
  requests: integer('stat-requests'),
  input_tokens: integer('stat-input'),
  output_tokens: integer('stat-output'),
  cache_tokens: integer('stat-cache'),
  older_available: !element('load-more').hidden,
  pagination_note: element('pagination-note').textContent,
});
(async () => {
  const observations = [];
  await vm.runInContext('loadTelemetry()', context);
  observations.push(snapshot('initial_load'));
  if (config.exercise_refresh) {
    while (vm.runInContext('state.cursor !== null', context)) {
      await vm.runInContext('loadTelemetry(true)', context);
    }
    observations.push(snapshot('all_pages_loaded'));
    await vm.runInContext('loadTelemetry()', context);
    observations.push(snapshot('refresh_without_new_requests'));
  }
  process.stdout.write(JSON.stringify(observations));
})().catch(error => { process.stderr.write(error.message + '\n'); process.exitCode = 1; });
