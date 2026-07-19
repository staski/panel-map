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
#
# Options:
#   --name NAME     panel slug for the web image (default: image basename)
#   --max-mb X      web image size budget (default 1.5)
#   --db DIR        instrument database (default: $PANELMAP_DB or ~/panelMap)
#   --mode M        build mode: local (default) | published
#   --clean         wipe public/images + public/docs first (lean production dist)
#   --no-edit       skip the interactive editor (use areas.json as-is)
#   --no-open       don't auto-open the browser for the edit step

set -euo pipefail

# ---- locate repo root (script lives in scripts/) ----
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# ---- defaults / args ----
IMAGE=""; AREAS=""; NAME=""; MAXMB="1.5"; DB="${PANELMAP_DB:-$HOME/panelMap}"
MODE="local"; CLEAN=0; EDIT=1; OPEN=1
while [ $# -gt 0 ]; do
  case "$1" in
    --image) IMAGE="$2"; shift 2;;
    --areas) AREAS="$2"; shift 2;;
    --name) NAME="$2"; shift 2;;
    --max-mb) MAXMB="$2"; shift 2;;
    --db) DB="$2"; shift 2;;
    --mode) MODE="$2"; shift 2;;
    --clean) CLEAN=1; shift;;
    --no-edit) EDIT=0; shift;;
    --no-open) OPEN=0; shift;;
    -h|--help) sed -n '2,32p' "$0"; exit 0;;
    *) echo "build_panel: unknown argument: $1" >&2; exit 2;;
  esac
done
[ -n "$IMAGE" ] || { echo "build_panel: --image is required" >&2; exit 2; }
[ -n "$AREAS" ] || { echo "build_panel: --areas is required" >&2; exit 2; }
[ -f "$IMAGE" ] || { echo "build_panel: image not found: $IMAGE" >&2; exit 2; }
[ -f "$AREAS" ] || { echo "build_panel: areas.json not found: $AREAS" >&2; exit 2; }
[ -n "$NAME" ] || NAME="$(basename "$IMAGE" | sed 's/\.[^.]*$//')"

step(){ echo; echo "━━ $* ━━"; }

# ---- 1. validate + clean ----
step "1/7  Validate & clean areas.json"
python3 scripts/panelmap_from_image.py --areas "$AREAS" --image "$IMAGE"

# ---- 2. interactive edit ----
if [ "$EDIT" -eq 1 ]; then
  step "2/7  Edit in the browser — adjust the map, then press Save"
  OPENFLAG=""; [ "$OPEN" -eq 0 ] && OPENFLAG="--no-open"
  python3 scripts/edit_server.py --image "$IMAGE" --areas "$AREAS" $OPENFLAG
else
  step "2/7  (skipped — --no-edit)"
fi

# ---- 3. web-scale the image + coords together ----
step "3/7  Scale the panel image for the web (<= ${MAXMB} MB)"
mkdir -p public/images public/docs public/panel
[ "$CLEAN" -eq 1 ] && { echo "  --clean: clearing public/images and public/docs"; rm -f public/images/* public/docs/*; }
SCALED="$(mktemp -t areas_scaled.XXXXXX).json"
python3 scripts/scale_panel.py --image "$IMAGE" --areas "$AREAS" --max-mb "$MAXMB" \
  --out-image "public/images/${NAME}.jpg" --out-areas "$SCALED"

# ---- 4. enrich from the catalog ----
step "4/7  Enrich (pictures / texts / docs from the catalog)"
node scripts/enrich_areas.js --areas "$SCALED" --out public/panel/areas.json

# ---- 5. sync referenced assets from the instrument DB ----
step "5/7  Sync instrument assets from the DB ($DB)"
node scripts/sync_assets.js --db "$DB"

# ---- 6. build the web app ----
step "6/7  Build the web app (mode: $MODE)"
if [ "$MODE" = "published" ]; then npm run build:published; else npm run build; fi

# ---- 7. package ----
step "7/7  Package dist.zip"
rm -f dist.zip
( cd dist && zip -qr ../dist.zip . )
rm -f "$SCALED"

echo
echo "✅ done — $(du -h dist.zip | cut -f1)  →  $ROOT/dist.zip"
echo "   deploy it with scripts/put.sh + scripts/update.sh (sftp upload + unzip)."
