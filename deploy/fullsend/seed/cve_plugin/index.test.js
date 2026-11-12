import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, writeFile, mkdir, symlink, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { collectContext } from './index.js';

async function fixture(fn) {
  const root = await mkdtemp(path.join(os.tmpdir(), 'bb-cve-test-'));
  try {
    await writeFile(path.join(root, 'alert.json'), JSON.stringify({dependency: {manifest_path: 'package.json'}, security_vulnerability: {package: {name: 'example', ecosystem: 'npm'}}}));
    await writeFile(path.join(root, 'package-lock.json'), JSON.stringify({lockfileVersion: 3, packages: {'': {}, 'node_modules/example': {version: '1.0.0'}}}));
    await writeFile(path.join(root, 'package.json'), JSON.stringify({dependencies: {example: '1.0.0'}}));
    await fn(root);
  } finally { await rm(root, {recursive: true, force: true}); }
}

test('reports partial evidence from selected files', () => fixture(async root => {
  const result = await collectContext({alert: 'alert.json', lockfile: 'package-lock.json'}, root);
  assert.equal(result.matchCount, 1);
  assert.equal(result.matches[0].version, '1.0.0');
  assert.deepEqual(result.declarations, {dependencies: '1.0.0'});
}));

test('rejects traversal and outside symlinks', () => fixture(async root => {
  await assert.rejects(collectContext({alert: '../alert.json', lockfile: 'package-lock.json'}, root), /inside/);
  await symlink(os.tmpdir(), path.join(root, 'outside'));
  await assert.rejects(collectContext({alert: 'outside/alert.json', lockfile: 'package-lock.json'}, root));
}));

test('rejects unsupported lockfiles and cancellation', () => fixture(async root => {
  await writeFile(path.join(root, 'package-lock.json'), JSON.stringify({lockfileVersion: 1}));
  await assert.rejects(collectContext({alert: 'alert.json', lockfile: 'package-lock.json'}, root), /Unsupported/);
  const controller = new AbortController();
  controller.abort();
  await assert.rejects(collectContext({alert: 'alert.json', lockfile: 'package-lock.json'}, root, controller.signal), {name: 'AbortError'});
}));

test('warns instead of inferring safety from missing entries', () => fixture(async root => {
  await writeFile(path.join(root, 'package-lock.json'), JSON.stringify({lockfileVersion: 3, packages: {'': {}}}));
  const result = await collectContext({alert: 'alert.json', lockfile: 'package-lock.json'}, root);
  assert.equal(result.matchCount, 0);
  assert.ok(result.warnings.some(w => w.includes('not-affected')));
}));
