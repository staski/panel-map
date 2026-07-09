#!/usr/bin/env node
// panelareas_from_json.js — generate panelAreas.js (and images.js / docs.js as
// needed) directly from a canonical areas.json, making that JSON the single
// hand-editable source of truth for a panel.
//
// This is the areas.json-first counterpart to crtall.js. Instead of parsing an
// HTML image-map and stubbing texts.js + matching asset filenames by name, it
// reads one manifest that carries geometry AND descriptions AND explicit asset
// references, and inlines title/text as literals (no texts.js indirection).
//
// Usage:
//   node scripts/panelareas_from_json.js --areas areas.json [--outdir ./src]
//
// areas.json:
//   {
//     "name": "panel",                 // optional, informational
//     "image": "cockpitPanel.png",     // optional, informational
//     "areas": [
//       { "title": "Airspeed Indicator", "shape": "circle", "coords": [232,100,60],
//         "text": "Shows indicated airspeed.", "img": "asi.png", "doc": "asi.pdf" }
//     ]
//   }
//   - title, shape ('rect'|'circle'), coords required per area
//   - text, img, doc optional
//   - circle coords = [cx,cy,r]; rect coords = [x1,y1,x2,y2]
//   A bare JSON array of areas is also accepted.
//
// Only images.js / docs.js are emitted when at least one area references an
// img / doc respectively (they carry static imports so Vite can bundle the
// assets). panelAreas.js imports them only when present.

const fs = require('fs');
const path = require('path');

function die(msg) {
  console.error(`error: ${msg}`);
  process.exit(1);
}

function parseArgs(argv) {
  const args = { outdir: './src' };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--areas') args.areas = argv[++i];
    else if (a === '--outdir') args.outdir = argv[++i];
    else if (a === '-h' || a === '--help') args.help = true;
    else die(`unknown argument: ${a}`);
  }
  return args;
}

// Match crtall.js's camelize so generated `name` values stay consistent.
function camelize(text) {
  const a = String(text).toLowerCase()
    .replace(/[-_\s.]+(.)?/g, (_, c) => (c ? c.toUpperCase() : ''));
  return a.substring(0, 1).toLowerCase() + a.substring(1);
}

// Safe JS identifier fragment for import var names (strip non-alphanumerics so
// titles with spaces/parens like "Garmin G5 (attitude)" can't break the output).
function identFrag(text) {
  const c = camelize(text).replace(/[^A-Za-z0-9]/g, '');
  return c || 'x';
}

function loadAreas(file) {
  let data;
  try {
    data = JSON.parse(fs.readFileSync(file, 'utf-8'));
  } catch (e) {
    die(`could not read/parse ${file}: ${e.message}`);
  }
  if (Array.isArray(data)) return data;
  if (data && Array.isArray(data.areas)) return data.areas;
  die("areas file must be a JSON array or an object with an 'areas' key");
}

function validate(areas) {
  const seen = new Set();
  return areas.map((a, i) => {
    const title = String(a.title || '').trim();
    const shape = String(a.shape || '').trim().toLowerCase();
    const coords = a.coords || [];
    if (!title) die(`area #${i} has no title`);
    if (shape !== 'rect' && shape !== 'circle')
      die(`area '${title}': shape must be 'rect' or 'circle', got '${shape}'`);
    if (!Array.isArray(coords) || !coords.every(c => typeof c === 'number'))
      die(`area '${title}': coords must be an array of numbers`);
    const need = shape === 'circle' ? 3 : 4;
    if (coords.length !== need)
      die(`area '${title}': ${shape} needs ${need} coords, got ${coords.length}`);
    const key = camelize(title);
    if (seen.has(key))
      console.error(`warning: area '${title}' collides with another after camelize ('${key}')`);
    seen.add(key);
    return {
      title, shape,
      coords: coords.map(c => Math.round(c)),
      text: a.text != null ? String(a.text) : undefined,
      img: a.img != null ? String(a.img) : undefined,
      doc: a.doc != null ? String(a.doc) : undefined,
      name: key,
      ident: identFrag(title),
    };
  });
}

// Back up an existing file to <file>.ori before overwriting (mirrors crtall.js).
function backup(file) {
  if (fs.existsSync(file)) {
    try { fs.renameSync(file, `${file}.ori`); }
    catch (e) { console.error(`could not back up ${file}: ${e.message} (continuing)`); }
  }
}

function main() {
  const args = parseArgs(process.argv);
  if (args.help) {
    console.log(fs.readFileSync(__filename, 'utf-8').split('\n')
      .filter(l => l.startsWith('//')).map(l => l.slice(3)).join('\n'));
    return;
  }
  if (!args.areas) die('--areas is required');
  if (!fs.existsSync(args.areas)) die(`areas file not found: ${args.areas}`);

  const areas = validate(loadAreas(args.areas));
  if (areas.length === 0) die('areas file contains no areas');

  const withImg = areas.filter(a => a.img);
  const withDoc = areas.filter(a => a.doc);

  fs.mkdirSync(args.outdir, { recursive: true });

  // --- panelAreas.js ---
  const imports = [];
  if (withImg.length) imports.push("import images from './images';");
  if (withDoc.length) imports.push("import docs from './docs';");

  const objs = areas.map((a, idx) => {
    const lines = [
      `    name: ${JSON.stringify(a.name)},`,
      `    shape: ${JSON.stringify(a.shape)},`,
      `    coords: [${a.coords.join(',')}],`,
      `    id: ${JSON.stringify(String(idx))},`,
      `    title: ${JSON.stringify(a.title)},`,
    ];
    if (a.text !== undefined) lines.push(`    text: ${JSON.stringify(a.text)},`);
    if (a.img) lines.push(`    img: images.img${a.ident},`);
    if (a.doc) lines.push(`    href: docs.doc${a.ident},`);
    // drop the trailing comma on the last property for tidiness
    lines[lines.length - 1] = lines[lines.length - 1].replace(/,$/, '');
    return `  {\n${lines.join('\n')}\n  }`;
  });

  const panelAreasJs =
    `${imports.join('\n')}${imports.length ? '\n\n' : ''}` +
    `var panelAreas = [\n${objs.join(',\n')}\n];\n\n` +
    `export {\n\tpanelAreas,\n};\n`;

  const panelAreasPath = path.join(args.outdir, 'panelAreas.js');
  backup(panelAreasPath);
  fs.writeFileSync(panelAreasPath, panelAreasJs);
  console.log(`wrote ${panelAreasPath}  (${areas.length} areas)`);

  // --- images.js (only if referenced) ---
  if (withImg.length) {
    let js = '';
    withImg.forEach(a => { js += `import img${a.ident} from './images/${a.img}';\n`; });
    js += '\nexport default {\n';
    withImg.forEach(a => { js += `  'img${a.ident}': img${a.ident},\n`; });
    js += '};\n';
    const p = path.join(args.outdir, 'images.js');
    backup(p);
    fs.writeFileSync(p, js);
    console.log(`wrote ${p}  (${withImg.length} images)`);
  }

  // --- docs.js (only if referenced) ---
  if (withDoc.length) {
    let js = '';
    withDoc.forEach(a => { js += `import doc${a.ident} from './docs/${a.doc}';\n`; });
    js += '\nexport default {\n';
    withDoc.forEach(a => { js += `  'doc${a.ident}': doc${a.ident},\n`; });
    js += '};\n';
    const p = path.join(args.outdir, 'docs.js');
    backup(p);
    fs.writeFileSync(p, js);
    console.log(`wrote ${p}  (${withDoc.length} docs)`);
  }

  if (!withImg.length) console.log('note: no areas reference an img — images.js not written');
  if (!withDoc.length) console.log('note: no areas reference a doc — docs.js not written');
}

main();
