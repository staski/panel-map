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
  if (!Array.isArray(cfg) && cfg.image) refs.add(cfg.image);   // panel background image
  for (const a of areas){ if (a.img) refs.add(a.img); if (a.doc) refs.add(a.doc); }

  let copied = 0, kept = 0;
  const missing = [];
  for (const rel of [...refs].sort()){
    const src = path.join(args.db, rel);
    const dst = path.join(args.public, rel);
    if (fs.existsSync(src)){
      fs.mkdirSync(path.dirname(dst), { recursive: true });
      fs.copyFileSync(src, dst);
      copied++;
      console.log('  ✓ ' + rel);
    } else if (fs.existsSync(dst)){
      kept++;                                   // already in public (e.g. panel photo placed by hand)
    } else {
      missing.push(rel);
    }
  }

  console.log(`sync_assets: ${copied} copied from ${args.db}, ${kept} already present, ` +
              `${missing.length} missing.`);
  if (missing.length){
    console.log('  missing (referenced but not in the DB — add them, or provide manually):');
    missing.forEach(m => console.log('    ✗ ' + m));
  }
}

main();
