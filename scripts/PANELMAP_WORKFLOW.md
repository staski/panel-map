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

3. **Generate the Vue build inputs:**
   ```sh
   node scripts/panelareas_from_json.js --areas areas.json --outdir ./src
   ```
   Emits `panelAreas.js` with `title`/`text` inlined as literals, plus
   `images.js` / `docs.js` (only when areas reference an `img` / `doc`, since
   those carry the static imports Vite needs to bundle the assets). Existing
   files are backed up to `*.ori` first.

## Two ways to reach `panelAreas.js`

- **areas.json-first (preferred):** `panelareas_from_json.js` goes straight from
  the manifest to `panelAreas.js`. Descriptions live in `areas.json`, assets are
  referenced explicitly, and there is no `texts.js` stub to fill in afterward.
- **Legacy HTML route:** drop `panelmap.html` into `~/panelMap/` (with `images/`
  and `docs/`) and run `crtall.js`. This still works, but it re-derives
  everything from the HTML, matches assets by filename, and stubs `texts.js`.

## Notes

- Overlay rendering needs Pillow (`pip3 install pillow`). `--dims`,
  `panelmap.html`, and `panelareas_from_json.js` work with no dependencies.
- The `<img src>` / `width` / `height` in `panelmap.html` are only for browser
  preview; `crtall.js` reads just the `<area>` elements.
- Both generators validate as they go — bad coord counts, unknown shapes, and
  duplicate/colliding titles are reported instead of silently producing a broken
  map.
