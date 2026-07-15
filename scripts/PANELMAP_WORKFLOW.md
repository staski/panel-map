# Building a panel map from a cockpit photo

The tedious part of creating a new virtual panel used to be authoring
`panelmap.html` — measuring every instrument's pixel box by hand and then
hand-filling descriptions. This workflow replaces that with a single canonical
source, **`areas.json`**, produced by a vision pass and consumed by two tools.

## `areas.json` is the source of truth

One hand-editable file describes the whole panel — geometry, labels,
descriptions, and asset references:

```json
{
  "name": "panel",
  "image": "cockpitPanel.png",
  "areas": [
    {
      "title": "Airspeed Indicator",
      "shape": "circle",
      "coords": [232, 100, 60],
      "text": "Shows indicated airspeed in knots.",
      "img":  "asi.png",
      "doc":  "asi.pdf"
    },
    { "title": "Avidyne IFD540", "shape": "rect", "coords": [893, 63, 1197, 202] }
  ]
}
```

- `title`, `shape` (`rect` | `circle`), `coords` are required per area.
- `coords`: `circle` = `[cx, cy, r]`, `rect` = `[x1, y1, x2, y2]`, in the image's
  natural pixel space.
- `text`, `img`, `doc` are optional (description shown in the popup, popup image,
  and manual PDF opened on click).
- Top-level `image` names the panel background photo.

## The pipeline

```
                                    ┌─▶ panelmap_from_image.py ─▶ panelmap.html + overlay.png   (preview / verify)
cockpit photo ─▶ vision ─▶ areas.json ┤
                (Claude)             └─▶ panelareas_from_json.js ─▶ panelAreas.js (+ images.js / docs.js)   (build inputs)
```

Both tools read the same `areas.json`, so the map, the preview, and the
generated Vue inputs never drift apart.

## Steps

1. **Detect instruments → `areas.json`.** Have Claude look at the photo and emit
   the manifest above, using `INSTRUMENT_IDENTIFICATION.md` to recognize and
   label instruments (shape rules, common-instrument cues, and the *completeness*
   checklist for finding every round gauge). **Zoom in** — crop each instrument
   cluster and magnify it (e.g. 3–4×) before finalizing; it reveals gauges the
   full-frame view misses (partial/occluded ones) and gives noticeably better
   centers and radii, so the seeds often need no geometric refine at all. (Need
   the pixel size while checking coords?
   `python3 scripts/panelmap_from_image.py --image panel.jpg --dims`.)

2. **Preview & verify:**
   ```sh
   python3 scripts/panelmap_from_image.py --areas areas.json --outdir ./out
   # wrote ./out/panelmap.html  (N areas, image WxH)
   # wrote ./out/overlay.png
   ```
   `overlay.png` draws every box + label on the photo. Geometry is usually
   close; instrument *labels* often need a human (the model can't always tell a
   G5 from a GI-275, or read a faded radio's model number). Edit `areas.json`
   and re-run. The image comes from the manifest's `image` field, or pass
   `--image` to override.

   **Optional — snap circles to their bezels:** hand-estimated circle centers
   and radii drift by a few pixels. `panelmap_refine.py` uses the dark-bezel /
   lighter-panel contrast to snap each `circle` to its true outer bezel:
   ```sh
   python3 scripts/panelmap_refine.py --areas areas.json --outdir ./out
   # wrote ./out/areas.refined.json + ./out/refine_overlay.png (yellow=seed, green=refined)
   ```
   It never overwrites your `areas.json` (writes `areas.refined.json`) and always
   emits a before/after overlay to eyeball. Two methods (`--method`):
   - `ring` (default) — a **do-no-harm** tightening pass: edge-fits the outer
     bezel but is *coverage-preserving*, so it only adjusts a circle when the
     result still covers the seed's dial (a good, well-centered seed is kept as
     is rather than decentered). Small capture range — it won't fix a large
     drift; use `bbox` for that.
   - `bbox` — bounded bounding-box, then inscribes a circle that never exceeds
     the seed radius; recovers badly-drifted seeds and stays *inside* the
     instrument (slightly conservative/smaller). Prefer this when the initial
     circles are drifted by a large fraction of their radius.

3. **Fill in pictures, texts and docs from the catalog:**
   ```sh
   node scripts/enrich_areas.js --areas areas.json --out panel/areas.json
   ```
   Matches each area's title against `scripts/instrument_catalog.json`
   (avionics → engine → standard) and fills `img` / `text` / `doc` with the
   standard picture, description and documentation for that instrument type, as
   **server-relative references** (`images/…`, `docs/…`). Only missing fields are
   filled (custom values are kept; `--overwrite` forces catalog values). It
   prints the set of referenced image/doc files to place on the server. Edit the
   catalog to change the standard picture/text/doc for a whole instrument class.

## Deploying: runtime assets (update without rebuilding)

The demo app loads its panel config **and** all assets at runtime, so pictures,
docs and texts can be swapped on the server with no rebuild.

- Put the enriched config at **`public/panel/areas.json`**, the panel image and
  instrument pictures under **`public/images/`**, and manuals under
  **`public/docs/`**. Everything in `public/` is served verbatim and copied into
  `dist/`.
- Build once (`npm run build`). `App.vue` fetches `panel/areas.json` at runtime
  (resolved against `import.meta.env.BASE_URL`, so it works under any deploy
  path), and references each `img` / `doc` by URL — no build-time bundling.
- **To update after deployment:** replace a file in `dist/images/` or
  `dist/docs/`, or edit `dist/panel/areas.json`, directly on the server. The
  change appears on the next page load; the app is never rebuilt.

The published `@staski/panel-map` component is unchanged — it already accepts
plain URL strings for `img` / `href`; only the demo *App* changed (fetch vs
import).

## Populating assets from the instrument database

`scripts/sync_assets.js` copies the pictures & docs a panel actually references
out of a **universal instrument database** (a directory of every instrument you
know, laid out as `<db>/images/…` and `<db>/docs/…`) into `public/`:

```sh
node scripts/sync_assets.js            # db defaults to $PANELMAP_DB or ~/panelMap
node scripts/sync_assets.js --db /path/to/db --public dist   # e.g. refresh a deployed tree
```

It reads `public/panel/areas.json`, copies each referenced `image` / `img` /
`doc` from the DB into the matching `public/` path, and reports what was copied,
what was already present, and what's missing from the DB. It also runs as the
**`postinstall`** step, and exits quietly if the DB or config is absent (so
`npm install` never fails). To update an instrument's picture or manual for every
panel that uses it, drop the new file into the DB and re-run.

> The names a panel references (from `enrich_areas.js` / the catalog) must match
> the filenames in the DB. Keep `instrument_catalog.json` and the DB in sync.

## Notes

- Overlay rendering needs Pillow (`pip3 install pillow`). `--dims` and
  `panelmap.html` generation work with no dependencies.
- The `<img src>` / `width` / `height` in `panelmap.html` are only for browser
  preview; consumers read just the `<area>` elements.
- The tools validate as they go — bad coord counts, unknown shapes, and
  duplicate/colliding titles are reported instead of silently producing a broken
  map.
