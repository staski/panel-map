#!/usr/bin/env node
// enrich_areas.js — fill an areas.json's img / text / doc from instrument_catalog.json.
//
// Each area's title is matched against the catalog (avionics -> engine ->
// standard, first keyword hit wins) and the matching entry's image / text / doc
// are filled in as server-relative references (e.g. "images/gns430.png"). This
// turns a bare vision-detected areas.json into a runtime-ready panel config that
// references pictures, texts and docs by name — swap those files on the server
// to update, no rebuild (see PANELMAP_WORKFLOW.md).
//
// Usage:
//   node scripts/enrich_areas.js --areas areas.json [--out out.json]
//        [--catalog scripts/instrument_catalog.json] [--overwrite] [--base ""]
//
// By default only MISSING fields are filled (custom img/text/doc are kept);
// --overwrite replaces them with the catalog's standard values. --base prepends
// a path prefix to every referenced file.

const fs = require('fs');
const path = require('path');

function die(m){ console.error('error: ' + m); process.exit(1); }

function parseArgs(argv){
  const a = { catalog: path.join(__dirname, 'instrument_catalog.json'), overwrite: false, base: '' };
  for (let i = 2; i < argv.length; i++){
    const k = argv[i];
    if (k === '--areas') a.areas = argv[++i];
    else if (k === '--out') a.out = argv[++i];
    else if (k === '--catalog') a.catalog = argv[++i];
    else if (k === '--base') a.base = argv[++i];
    else if (k === '--overwrite') a.overwrite = true;
    else if (k === '-h' || k === '--help') a.help = true;
    else die('unknown argument: ' + k);
  }
  return a;
}

const norm = s => String(s || '').toLowerCase().replace(/[^a-z0-9]/g, '');

// Build an ordered [key, entry] list: avionics, then engine, then standard.
function catalogOrder(cat){
  const order = [];
  for (const section of ['avionics', 'engine', 'standard']){
    const grp = cat[section] || {};
    for (const key of Object.keys(grp)) order.push([section + '/' + key, grp[key]]);
  }
  return order;
}

function match(title, ordered){
  const t = norm(title);
  for (const [key, entry] of ordered){
    for (const m of (entry.match || [])){
      if (t.includes(norm(m))) return { key, entry };
    }
  }
  return null;
}

function withBase(p, base){
  if (!base) return p;
  return base.replace(/\/+$/, '') + '/' + p.replace(/^\/+/, '');
}

function main(){
  const args = parseArgs(process.argv);
  if (args.help){ console.log(fs.readFileSync(__filename,'utf-8').split('\n').filter(l=>l.startsWith('//')).map(l=>l.slice(3)).join('\n')); return; }
  if (!args.areas) die('--areas is required');
  if (!fs.existsSync(args.areas)) die('areas file not found: ' + args.areas);
  if (!fs.existsSync(args.catalog)) die('catalog not found: ' + args.catalog);

  const raw = JSON.parse(fs.readFileSync(args.areas, 'utf-8'));
  const doc = Array.isArray(raw) ? { areas: raw } : raw;   // normalise to { name, image, areas }
  const areas = doc.areas;
  if (!Array.isArray(areas)) die("areas file must be an array or have an 'areas' key");
  if (!doc.name) doc.name = 'panel';
  const cat = JSON.parse(fs.readFileSync(args.catalog, 'utf-8'));
  const ordered = catalogOrder(cat);

  // Tolerate a slightly-off schema: fill a missing 'title' from label/name/id.
  let fellBack = 0;
  for (const a of areas) {
    if (a.title == null || String(a.title).trim() === '') {
      const alt = [a.label, a.name, a.id].find(v => v != null && v !== '');
      if (alt != null) { a.title = String(alt); fellBack++; }
    }
  }
  if (fellBack) console.error(`note: ${fellBack} area(s) had no 'title' — used ` +
    `label/name/id instead; the toolchain keys on 'title'.`);

  const setIf = (a, field, val) => {
    if (val === undefined) return;
    if (args.overwrite || a[field] === undefined || a[field] === '') a[field] = withBase(val, args.base);
  };

  const matched = [], unmatched = [];
  const images = new Set(), docs = new Set();
  for (const a of areas){
    const hit = match(a.title, ordered);
    if (!hit){ unmatched.push(a.title || '(untitled)'); continue; }
    setIf(a, 'img', hit.entry.image);
    setIf(a, 'text', hit.entry.text);
    setIf(a, 'doc', hit.entry.doc);          // 'doc' -> the component opens it via href
    matched.push([a.title, hit.key]);
    if (a.img) images.add(a.img);
    if (a.doc) docs.add(a.doc);
  }

  if (!doc.image) console.error("note: no top-level 'image' — set it to the panel " +
    "photo (e.g. images/panel.jpg) so the runtime app can display the panel.");

  const out = args.out || args.areas.replace(/\.json$/, '') + '.enriched.json';
  fs.writeFileSync(out, JSON.stringify(doc, null, 2) + '\n');
  console.log(`wrote ${out}`);
  console.log(`\nmatched ${matched.length}/${areas.length}:`);
  for (const [title, key] of matched) console.log(`  ${(title||'').padEnd(34)} -> ${key}`);
  if (unmatched.length){
    console.log(`\nNO catalog match (${unmatched.length}) — left as-is, fill manually:`);
    for (const t of unmatched) console.log(`  ${t}`);
  }
  console.log(`\nreferenced images (put in the server's images/ dir): ${images.size}`);
  [...images].sort().forEach(f => console.log('  ' + f));
  console.log(`referenced docs (put in the server's docs/ dir): ${docs.size}`);
  [...docs].sort().forEach(f => console.log('  ' + f));
}

main();
