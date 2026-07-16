# Building a panel map from a cockpit photo

The tedious part of creating a new virtual panel used to be measuring every
instrument's pixel box by hand and hand-filling descriptions. This workflow
replaces that with a single canonical source, **`areas.json`**, produced by a
vision pass and consumed by a small toolchain.

## `areas.json` — the source of truth (OUTPUT CONTRACT)

The vision pass MUST emit `areas.json` in exactly this shape — the whole
toolchain keys on it:

```json
{
  "name": "panel",                     // optional (defaults to "panel")
  "image": "images/cockpitPanel.png",  // panel background photo (required for the runtime app)
  "areas": [
    {
      "title": "Airspeed Indicator",    // REQUIRED — the human instrument name
      "shape": "circle",                // REQUIRED — "circle" | "rect"
      "coords": [232, 100, 60],         // REQUIRED — circle [cx,cy,r], rect [x1,y1,x2,y2]
      "text": "Shows indicated airspeed in knots.",  // optional
      "img":  "images/asi.png",         // optional (popup picture)
      "doc":  "docs/asi.pdf"            // optional (manual opened on click)
    },
    { "title": "Avidyne IFD540", "shape": "rect", "coords": [893, 63, 1197, 202] }
  ]
}
```

Contract, most important first:

- **Every area MUST have a `title`** — the human instrument name ("Altimeter",
  "Garmin GNS430", …). It is the key the entire chain uses: catalog matching,
  the popup heading, and the `<area>` label. **Do NOT label areas with an
  `id`/number, and never omit `title`** — a missing title breaks enrichment and
  generation. (An `id` field, if present, is ignored.)
- `shape` (`rect` | `circle`) and `coords` are required. `coords` are in the
  image's **natural pixel space**: `circle` = `[cx, cy, r]`, `rect` =
  `[x1, y1, x2, y2]`.
- Top-level **`image`** is the panel background photo (required for the runtime
  app); `name` is optional. `text` / `img` / `doc` are optional — `enrich_areas.js`
  fills them from the catalog.
- **Validate before continuing:** always run `panelmap_from_image.py` (below) on
  the areas.json. It checks the schema — a missing `title`, wrong `shape`, or
  malformed `coords` — and writes back a cleaned copy, catching slips immediately.

## The pipeline

```
cockpit photo ─▶ vision ─▶ areas.json ─▶ panelmap_from_image.py  (validate + clean areas.json)
                (Claude)       │              │
                               │              └─▶ view / fine-tune in panelmap_editor.html
                               └────────▶ enrich_areas.js ─▶ public/panel/areas.json ─▶ sync_assets.js
                                          (fills img/text/doc from the catalog)         (pull pics/docs from the DB)
```

Every tool reads the same `areas.json`, so the map, the preview, and the runtime
config never drift apart.

> **Required first step:** before the vision pass, **read
> [`INSTRUMENT_IDENTIFICATION.md`](INSTRUMENT_IDENTIFICATION.md) in full** — its
> recognition cues, the titling rule (function vs model), shape disambiguation,
> the completeness checklist, and the placement/mislabel pitfalls. Detection
> quality depends on it; consult it without being prompted to.

## Steps

1. **Read the reference, then detect → `areas.json`.** First read
   `INSTRUMENT_IDENTIFICATION.md` in full (required — see the callout above); it
   is an input to this step, not optional background. Then look at the photo and
   emit the manifest above, applying its recognition cues, titling rule, shape
   rules and *completeness* checklist (find every round gauge). **Zoom in** —
   crop each instrument cluster and magnify it (e.g. 3–4×) before finalizing; it
   reveals gauges the full-frame view misses (partial/occluded ones) and gives
   noticeably better centers and radii, so the seeds often need no geometric
   refine at all. (Need the pixel size while checking coords?
   `python3 scripts/panelmap_from_image.py --image panel.jpg --dims`.)

2. **Validate, clean & eyeball:**
   ```sh
   python3 scripts/panelmap_from_image.py --areas areas.json --image panel.jpg
   # validates the schema and rewrites areas.json cleaned (rounds coords,
   # normalises rect corners to [x1<x2,y1<y2], defaults name, fills a missing
   # title from id/name/label), and renders overlay.png so the detection can be
   # eyeballed. --no-overlay skips the overlay; --out writes the cleaned copy elsewhere.
   ```
   This is the schema gate — it fails loudly on a broken map, warns on
   recoverable issues, and flags coords outside the image. **Look at `overlay.png`
   to check the first shot** (the vision pass should do this to self-verify), then
   fine-tune: edit `areas.json` and re-run, or use the graphical editor
   (`scripts/panelmap_editor.html`) to drag/resize/delete shapes and download the
   result. Geometry is usually close; instrument *labels* often need a human (a G5
   vs a GI-275, a faded radio's model number).

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

### Shrinking the panel image for the web

Identify on a high-res photo (better recognition), but serve a smaller one
(≈1–2 MB). The `areas.json` coords are in the *served* image's pixel space, so
the image and the coords must shrink **together** — `scale_panel.py` does both:

```sh
python3 scripts/scale_panel.py --image panel.jpg --areas areas.json --max-mb 1.5
# scales the image + every coordinate by the same factor; writes panel_web.jpg +
# areas_web.json (coords scaled, 'image' field updated). Targets: --max-mb / --max-dim / --scale.
```

Use the scaled `*_web.jpg` as your `public/images/` panel image and the scaled
`areas_web.json` as `public/panel/areas.json`. (Requires Pillow.)

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

- Validation, cleaning, and `--dims` work with no dependencies; only the optional
  `--overlay` PNG needs Pillow (`pip3 install pillow`).
- The tools validate as they go — bad coord counts, unknown shapes, and
  duplicate/colliding titles are reported instead of silently producing a broken
  map.
