#!/usr/bin/env node
// stage-lib.js — stage the publishable @staski/panel-map package in dist-lib/.
//
// Run after the library build (`npm run buildlib`, or use `npm run stage:lib`
// which does both). It drops the library's own package.json (scripts/
// package.lib.json, with paths relative to dist-lib/) plus README/LICENSE into
// dist-lib/, from which the package is published with NO manifest swap:
//
//   npm run stage:lib
//   cd dist-lib && npm publish        # bump version in scripts/package.lib.json first
//
// The app's root package.json (demo-panel) is never touched.

const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const dist = path.join(root, 'dist-lib');

if (!fs.existsSync(dist)) {
  console.error('stage-lib: dist-lib/ not found — run `npm run buildlib` first.');
  process.exit(1);
}

fs.copyFileSync(path.join(__dirname, 'package.lib.json'), path.join(dist, 'package.json'));
for (const f of ['README.md', 'LICENSE']) {
  const src = path.join(root, f);
  if (fs.existsSync(src)) fs.copyFileSync(src, path.join(dist, f));
}

const pkg = JSON.parse(fs.readFileSync(path.join(dist, 'package.json'), 'utf8'));
console.log(`staged ${pkg.name}@${pkg.version} in dist-lib/`);
console.log('  contents: ' + fs.readdirSync(dist).sort().join(', '));
console.log('  to publish (bump version in scripts/package.lib.json first if needed):');
console.log('    cd dist-lib && npm publish');
