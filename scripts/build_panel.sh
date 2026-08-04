#!/usr/bin/env bash
#
# build_panel.sh — one command from a cleaned areas.json + cockpit image to a
# deployable dist.zip. The only manual step is editing the map in the browser.
#
#   Input : a cockpit photo + an areas.json (produced by the vision pass)
#   Output: dist.zip (the built web app, ready to deploy — matches put.sh/update.sh)
#   Manual: the panel-map editor pops up; adjust boxes/titles, hit "Save".
#
# Pipeline:
#   validate/clean  ->  EDIT (browser)  ->  web-scale image+coords  ->
#   enrich (catalog img/text/doc)  ->  sync assets from the DB  ->  npm build  ->  zip
#
# Usage:
#   scripts/build_panel.sh --image cockpit.jpg --areas areas.json [options]
#   scripts/build_panel.sh --update [options]      # re-edit the last build
#
# Options:
#   --update        start from the PREVIOUS build instead of --image/--areas:
#                   reuses public/panel/areas.json together with the web image
#                   it belongs to (public/images/...). The image is already
#                   web-sized, so the scaling step is skipped and the coords are
#                   passed through untouched. Use this to refine an existing
#                   panel — feeding a built areas.json back with the ORIGINAL
#                   photo would scale the coords a second time.
#   --aircraft NAME page title becomes "<NAME> Instrument Panel"
#                   (default: the "aircraft" field in areas.json, if present)
#   --title TEXT    full page title, overriding --aircraft
#   --favicon PATH  browser icon, relative to the served root, e.g.
#                   images/detes-icon.png (default: the "favicon" field in
#                   areas.json, else the bundled favicon.svg). If it lives in the
#                   instrument DB it is synced into public/ like any other asset.
#   --name NAME     panel slug for the web image (default: image basename)
#   --max-mb X      web image size budget (default 1.5)
#   --db DIR        instrument database (default: $PANELMAP_DB or ~/panelMap)
#   --mode M        build mode: local (default) | published
#   --base PATH     where the app is served from (default './' = relative to
#                   wherever dist.zip is unpacked — works in any subdirectory).
#                   Pass an absolute path to pin it, e.g. --base /fly/detes/panel/
#                   or --base / to serve from the web root.
#   --clean         wipe public/images + public/docs first (lean production dist)
#   --no-edit       skip the interactive editor (use areas.json as-is)
#   --no-open       don't auto-open the browser for the edit step

set -euo pipefail

# ---- locate repo root (script lives in scripts/) ----
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# ---- defaults / args ----
IMAGE=""; AREAS=""; NAME=""; MAXMB="1.5"; DB="${PANELMAP_DB:-$HOME/panelMap}"
MODE="local"; BASE="./"; CLEAN=0; EDIT=1; OPEN=1; UPDATE=0
AIRCRAFT=""; TITLE=""; FAVICON=""
while [ $# -gt 0 ]; do
  case "$1" in
    --update) UPDATE=1; shift;;
    --aircraft) AIRCRAFT="$2"; shift 2;;
    --title) TITLE="$2"; shift 2;;
    --favicon) FAVICON="$2"; shift 2;;
    --image) IMAGE="$2"; shift 2;;
    --areas) AREAS="$2"; shift 2;;
    --name) NAME="$2"; shift 2;;
    --max-mb) MAXMB="$2"; shift 2;;
    --db) DB="$2"; shift 2;;
    --mode) MODE="$2"; shift 2;;
    --base) BASE="$2"; shift 2;;
    --clean) CLEAN=1; shift;;
    --no-edit) EDIT=0; shift;;
    --no-open) OPEN=0; shift;;
    -h|--help) sed -n '2,36p' "$0"; exit 0;;
    *) echo "build_panel: unknown argument: $1" >&2; exit 2;;
  esac
done
# the app concatenates BASE_URL + "panel/areas.json" etc., so it needs a trailing slash
case "$BASE" in */) ;; *) BASE="$BASE/";; esac
# ---- --update: take the image + map from the previous build (a matched pair) ----
PREV_AREAS="public/panel/areas.json"
if [ "$UPDATE" -eq 1 ]; then
  if [ -n "$IMAGE" ] || [ -n "$AREAS" ]; then
    echo "build_panel: --update takes the image and areas.json from the previous build;" >&2
    echo "             don't combine it with --image/--areas." >&2
    exit 2
  fi
  if [ "$CLEAN" -eq 1 ]; then
    echo "build_panel: --clean would delete the very image --update reuses; not combinable." >&2
    exit 2
  fi
  if [ ! -f "$PREV_AREAS" ]; then
    echo "build_panel: no previous build found ($PREV_AREAS is missing)." >&2
    echo "             Run a normal build first:" >&2
    echo "               scripts/build_panel.sh --image cockpit.jpg --areas areas.json" >&2
    exit 1
  fi
  AREAS="$PREV_AREAS"
  IMGREL="$(node -e "const fs=require('fs');try{process.stdout.write(String(JSON.parse(fs.readFileSync('$PREV_AREAS','utf8')).image||''))}catch(e){}")"
  if [ -z "$IMGREL" ]; then
    echo "build_panel: $PREV_AREAS has no 'image' field — cannot tell which image it belongs to." >&2
    exit 1
  fi
  IMAGE="public/${IMGREL#/}"
  if [ ! -f "$IMAGE" ]; then
    echo "build_panel: the previous build's image is missing: $IMAGE" >&2
    echo "             (referenced as '$IMGREL' by $PREV_AREAS)" >&2
    exit 1
  fi
  echo "build_panel: --update — reusing $IMAGE + $AREAS from the previous build"
fi

[ -n "$IMAGE" ] || { echo "build_panel: --image is required (or use --update)" >&2; exit 2; }
[ -n "$AREAS" ] || { echo "build_panel: --areas is required (or use --update)" >&2; exit 2; }
[ -f "$IMAGE" ] || { echo "build_panel: image not found: $IMAGE" >&2; exit 2; }
[ -f "$AREAS" ] || { echo "build_panel: areas.json not found: $AREAS" >&2; exit 2; }
[ -n "$NAME" ] || NAME="$(basename "$IMAGE" | sed 's/\.[^.]*$//')"

step(){ echo; echo "━━ $* ━━"; }

# ---- 1. validate + clean ----
step "1/7  Validate & clean areas.json"
# --no-overlay: the editor (next step) shows the map, and the overlay would
# otherwise be written next to the areas file — i.e. into the served public/panel/
python3 scripts/panelmap_from_image.py --areas "$AREAS" --image "$IMAGE" --no-overlay

# ---- 2. interactive edit ----
if [ "$EDIT" -eq 1 ]; then
  step "2/7  Edit in the browser — adjust the map, then press Save"
  OPENFLAG=""; [ "$OPEN" -eq 0 ] && OPENFLAG="--no-open"
  python3 scripts/edit_server.py --image "$IMAGE" --areas "$AREAS" $OPENFLAG
else
  step "2/7  (skipped — --no-edit)"
fi

# ---- 3. web-scale the image + coords together ----
mkdir -p public/images public/docs public/panel
if [ "$UPDATE" -eq 1 ]; then
  # the reused image is already web-sized and the coords already match it —
  # re-scaling would shrink them a second time, so pass both through untouched
  step "3/7  (skipped — --update reuses the already web-scaled image)"
  SCALED="$AREAS"
  SCALED_IS_TEMP=0
else
  step "3/7  Scale the panel image for the web (<= ${MAXMB} MB)"
  [ "$CLEAN" -eq 1 ] && { echo "  --clean: clearing public/images and public/docs"; rm -f public/images/* public/docs/*; }
  SCALED="$(mktemp -t areas_scaled.XXXXXX).json"
  SCALED_IS_TEMP=1
  python3 scripts/scale_panel.py --image "$IMAGE" --areas "$AREAS" --max-mb "$MAXMB" \
    --out-image "public/images/${NAME}.jpg" --out-areas "$SCALED"
fi

# ---- 4. enrich from the catalog ----
step "4/7  Enrich (pictures / texts / docs from the catalog)"
node scripts/enrich_areas.js --areas "$SCALED" --out public/panel/areas.json

# ---- 5. sync referenced assets from the instrument DB ----
step "5/7  Sync instrument assets from the DB ($DB)"
node scripts/sync_assets.js --db "$DB"

# ---- 6. build the web app ----
# ---- page title + favicon: CLI > areas.json fields > .env defaults ----
# read the fields from the enriched config we just wrote
jsonfield(){ node -e "const fs=require('fs');try{process.stdout.write(String(JSON.parse(fs.readFileSync('public/panel/areas.json','utf8'))['$1']||''))}catch(e){}"; }
[ -n "$AIRCRAFT" ] || AIRCRAFT="$(jsonfield aircraft)"
[ -n "$FAVICON" ]  || FAVICON="$(jsonfield favicon)"
[ -n "$TITLE" ] || { [ -n "$AIRCRAFT" ] && TITLE="$AIRCRAFT Instrument Panel"; }
[ -n "$TITLE" ]   && export VITE_PANEL_TITLE="$TITLE"
[ -n "$FAVICON" ] && export VITE_PANEL_FAVICON="$FAVICON"

step "6/7  Build the web app (mode: $MODE, base: $BASE)"
echo "     title:   ${VITE_PANEL_TITLE:-<.env default>}"
echo "     favicon: ${VITE_PANEL_FAVICON:-<.env default>}"
if [ "$MODE" = "published" ]; then
  npm run build:published -- --base="$BASE"
else
  npm run build -- --base="$BASE"
fi

# ---- 7. package ----
step "7/7  Package dist.zip"
rm -f dist.zip
( cd dist && zip -qr ../dist.zip . )
[ "${SCALED_IS_TEMP:-0}" -eq 1 ] && rm -f "$SCALED"

echo
echo "✅ done — $(du -h dist.zip | cut -f1)  →  $ROOT/dist.zip"
echo "   deploy it with scripts/put.sh + scripts/update.sh (sftp upload + unzip)."
