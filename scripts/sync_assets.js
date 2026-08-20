#!/usr/bin/env node
// sync_assets.js — copy the instrument pictures & docs a panel actually uses
// from a universal instrument database into the served runtime directory.
//
// The "database" is just a directory of all instruments you know about, laid out
// like the served tree: <db>/images/<name> and <db>/docs/<name>. A panel's
// runtime config (public/panel/areas.json) references the ones it needs by name
// (img / doc, plus the panel image). This copies exactly those into public/, so
// the app serves them — update the DB and re-run to refresh, no rebuild.
//
// The extension does not have to match: if the config asks for images/clock.png
// and the database holds images/clock.jpg, that file is used and the config is
// repointed at it (so the served name matches the actual format). Only the
// extension may differ, and only within the same kind of asset.
//
// Runs as the postinstall step, and can be run by hand any time.
//
// Usage:
//   node scripts/sync_assets.js [--db <dir>] [--config public/panel/areas.json] [--public public]
//
//   --db      universal instrument DB (default: $PANELMAP_DB or ~/panelMap)
//   --config  panel runtime config to read references from (default public/panel/areas.json)
//   --public  target served directory the references are relative to (default public)
//
// Exits quietly (status 0) if the DB or the config is absent, so `npm install`
// never fails on a machine without a database.

const fs = require('fs');
const path = require('path');
const os = require('os');

const IMG_EXT = ['.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg'];
const DOC_EXT = ['.pdf'];

// Locate <rel> in the database, tolerating a different file extension: the
// catalogue may say images/clock.png while the DB holds images/clock.jpg. Only
// the extension may differ — same directory, same base name, and an image never
// resolves to a document. Returns the path that actually exists, or null.
function findByBaseName(db, rel){
  const ext = path.extname(rel).toLowerCase();
  const allowed = DOC_EXT.includes(ext) ? DOC_EXT : IMG_EXT;
  const dir = path.dirname(rel);
  const base = path.basename(rel, path.extname(rel)).toLowerCase();
  let entries;
  try { entries = fs.readdirSync(path.join(db, dir)); } catch (e) { return null; }
  const hit = entries.find(f =>
    path.basename(f, path.extname(f)).toLowerCase() === base &&
    allowed.includes(path.extname(f).toLowerCase()));
  if (!hit) return null;
  return dir === '.' ? hit : `${dir}/${hit}`;
}

function parseArgs(argv){
  const a = {
    config: 'public/panel/areas.json',
    public: 'public',
    db: process.env.PANELMAP_DB || path.join(os.homedir(), 'panelMap'),
  };
  for (let i = 2; i < argv.length; i++){
    const k = argv[i];
    if (k === '--db') a.db = argv[++i];
    else if (k === '--config') a.config = argv[++i];
    else if (k === '--public') a.public = argv[++i];
    else if (k === '-h' || k === '--help') a.help = true;
    else { console.error('sync_assets: unknown argument: ' + k); process.exit(2); }
  }
  return a;
}

function main(){
  const args = parseArgs(process.argv);
  if (args.help){
    console.log(fs.readFileSync(__filename, 'utf8').split('\n')
      .filter(l => l.startsWith('//')).map(l => l.slice(3)).join('\n'));
    return;
  }
  if (!fs.existsSync(args.config)){
    console.log(`sync_assets: no panel config at ${args.config} — nothing to sync.`);
    return;
  }
  if (!fs.existsSync(args.db)){
    console.log(`sync_assets: instrument DB '${args.db}' not found — skipping ` +
                `(set PANELMAP_DB or pass --db).`);
    return;
  }

  let cfg;
  try { cfg = JSON.parse(fs.readFileSync(args.config, 'utf8')); }
  catch (e) { console.error('sync_assets: could not parse ' + args.config + ': ' + e.message); return; }

  const areas = Array.isArray(cfg) ? cfg : (cfg.areas || []);
  const refs = new Set();
  if (!Array.isArray(cfg) && cfg.image) refs.add(cfg.image);       // panel background image
  if (!Array.isArray(cfg) && cfg.favicon) refs.add(cfg.favicon);   // browser icon
  for (const a of areas){ if (a.img) refs.add(a.img); if (a.doc) refs.add(a.doc); }

  let copied = 0, kept = 0;
  const missing = [];
  const rewrite = new Map();                    // referenced path -> path found in the DB
  const copy = (from, toRel) => {
    const dst = path.join(args.public, toRel);
    fs.mkdirSync(path.dirname(dst), { recursive: true });
    fs.copyFileSync(from, dst);
    copied++;
  };
  for (const rel of [...refs].sort()){
    // An exact name always wins — in the DB first, then whatever is already in
    // public/. Only when neither exists do we accept a different extension, so a
    // loose match can never displace a file that was named exactly right.
    if (fs.existsSync(path.join(args.db, rel))){
      copy(path.join(args.db, rel), rel);
      console.log('  ✓ ' + rel);
      continue;
    }
    if (fs.existsSync(path.join(args.public, rel))){
      kept++;                                   // already in public (e.g. panel photo placed by hand)
      continue;
    }
    const found = findByBaseName(args.db, rel);
    if (found){                                 // same instrument, different extension
      copy(path.join(args.db, found), found);
      rewrite.set(rel, found);
      console.log(`  ✓ ${rel}  ->  ${found}  (extension differs in the DB)`);
    } else {
      missing.push(rel);
    }
  }

  // Point the config at the files that actually exist, so the served name and
  // its content type agree (a JPEG must not be served as clock.png).
  if (rewrite.size){
    const fix = v => (v && rewrite.has(v)) ? rewrite.get(v) : v;
    if (!Array.isArray(cfg)){
      if (cfg.image) cfg.image = fix(cfg.image);
      if (cfg.favicon) cfg.favicon = fix(cfg.favicon);
    }
    for (const a of areas){
      if (a.img) a.img = fix(a.img);
      if (a.doc) a.doc = fix(a.doc);
    }
    fs.writeFileSync(args.config, JSON.stringify(cfg, null, 2) + '\n');
    console.log(`sync_assets: repointed ${rewrite.size} reference(s) in ${args.config} ` +
                `to the file names found in the DB.`);
  }

  console.log(`sync_assets: ${copied} copied from ${args.db}, ${kept} already present, ` +
              `${missing.length} missing.`);
  if (missing.length){
    console.log('  missing (referenced but not in the DB — add them, or provide manually):');
    missing.forEach(m => console.log('    ✗ ' + m));
  }
}

main();
