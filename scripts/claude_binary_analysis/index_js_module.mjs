#!/usr/bin/env node
// Parse a carved module without executing it and retain exact byte ranges.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';

const [input, output, plugin] = process.argv.slice(2);
if (!input || !output || !plugin) {
  throw new Error('usage: index_js_module.mjs INPUT OUTPUT PRETTIER_BABEL_PLUGIN');
}
const packagePath = path.resolve(path.dirname(plugin), '../package.json');
if (JSON.parse(fs.readFileSync(packagePath)).version !== '3.6.2') {
  throw new Error('Expected Prettier 3.6.2 parser');
}
const bytes = fs.readFileSync(input);
const source = bytes.toString('utf8');
if (!Buffer.from(source).equals(bytes)) throw new Error('Module is not UTF-8');
const sidecar = JSON.parse(fs.readFileSync(input + '.json'));
const hash = data => crypto.createHash('sha256').update(data).digest('hex');
if (hash(bytes) !== sidecar.segment.sha256 || bytes.length !== sidecar.segment.length) {
  throw new Error('Carved module differs from its provenance');
}
const { parsers } = await import(pathToFileURL(path.resolve(plugin)));
const ast = parsers.babel.parse(source, { sourceType: 'module' });
const symbols = [];
function record(node, name, kind) {
  const start = Buffer.byteLength(source.slice(0, node.start));
  const end = Buffer.byteLength(source.slice(0, node.end));
  symbols.push({
    name, kind,
    start: sidecar.segment.start + start,
    end_exclusive: sidecar.segment.start + end,
    length: end - start,
    sha256: hash(bytes.subarray(start, end)),
  });
}
function visit(node) {
  if (!node || typeof node !== 'object') return;
  if (['FunctionDeclaration', 'ClassDeclaration'].includes(node.type) && node.id) {
    record(node, node.id.name, node.type);
  }
  if (['ObjectMethod', 'ClassMethod'].includes(node.type) && !node.computed) {
    record(node, node.key.name ?? node.key.value, node.type);
  }
  for (const [key, value] of Object.entries(node)) {
    if (['loc', 'comments', 'tokens'].includes(key)) continue;
    if (Array.isArray(value)) value.forEach(visit);
    else if (value && typeof value === 'object') visit(value);
  }
}
for (const node of ast.program.body) {
  if (node.type === 'VariableDeclaration') {
    for (const declaration of node.declarations) {
      if (declaration.id.type === 'Identifier') record(declaration, declaration.id.name, 'VariableDeclarator');
    }
  }
  visit(node);
}
const imports = ast.program.body.filter(n => n.type === 'ImportDeclaration').map(n => ({
  source: n.source.value,
  bindings: n.specifiers.map(s => ({ local: s.local.name, imported: s.imported?.name ?? s.type })),
}));
const exports = ast.program.body.filter(n => n.type === 'ExportNamedDeclaration').flatMap(n =>
  n.specifiers.map(s => ({ local: s.local.name, exported: s.exported.name })));
const result = JSON.stringify({ schema_version: 1, parser: 'Prettier 3.6.2 Babel', payload: sidecar.payload, segment: sidecar.segment, imports, exports, symbols }, null, 2) + '\n';
if (fs.existsSync(output) && fs.readFileSync(output, 'utf8') !== result) throw new Error('Refusing to overwrite different index');
fs.mkdirSync(path.dirname(output), { recursive: true });
fs.writeFileSync(output, result);
console.log(output);
