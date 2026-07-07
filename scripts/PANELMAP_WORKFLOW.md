# Building a panel map from a cockpit photo

The tedious part of creating a new virtual panel is authoring `panelmap.html` —
measuring every instrument's pixel box by hand. This workflow removes that toil
by pairing a **vision pass** (identify the instruments) with a **scaffolding
tool** (`panelmap_from_image.py`) that handles all the deterministic plumbing.

## The pipeline

```
cockpit photo ──▶ vision detection ──▶ areas.json ──▶ panelmap_from_image.py ──▶ panelmap.html + overlay.png
                     (Claude)                             (this repo)                        │
                                                                                            ▼
                                                                              verify overlay, correct labels
                                                                                            │
                                                                                            ▼
                                                                     ~/panelMap/panelmap.html ──▶ crtall.js
```

## Steps

1. **Get the image dimensions** (optional, handy when sanity-checking coords):
   ```sh
   python3 scripts/panelmap_from_image.py --image panel.jpg --dims
   # 1280x511
   ```

2. **Detect instruments → `areas.json`.** Have Claude look at the photo and emit
   a regions file. Coordinates are in the image's natural pixel space; round
   gauges are `circle` = `[cx, cy, r]`, screens/radios are `rect` =
   `[x1, y1, x2, y2]`:
   ```json
   {
     "name": "panel",
     "areas": [
       {"title": "Airspeed Indicator", "shape": "circle", "coords": [232, 100, 60]},
       {"title": "Avidyne IFD540",     "shape": "rect",   "coords": [893, 63, 1197, 202]}
     ]
   }
   ```

3. **Generate the map + overlay:**
   ```sh
   python3 scripts/panelmap_from_image.py \
       --image panel.jpg --areas areas.json --outdir ./out
   # wrote ./out/panelmap.html  (N areas, image WxH)
   # wrote ./out/overlay.png
   ```
   `panelmap.html` is emitted in the exact `<area title shape coords>` format
   that `crtall.js` consumes. `overlay.png` draws every box + label on the photo
   so you can verify placement at a glance.

4. **Verify & correct.** Eyeball `overlay.png`. Geometry is usually close;
   instrument *labels* often need a human (the model can't always tell a G5 from
   a GI-275, or read a faded radio's model number). Edit `areas.json` and re-run.
   The tool validates as it goes — wrong coord counts, unknown shapes, and
   duplicate titles (which collide in `crtall.js`, since it keys by title) are
   reported instead of silently producing a broken map.

5. **Feed into the existing generator.** Drop the finished `panelmap.html` into
   `~/panelMap/` alongside `images/` and `docs/`, then run `crtall.js` to
   generate `panelAreas.js` / `images.js` / `docs.js` / `texts.js`.

## Notes

- Overlay rendering needs Pillow (`pip3 install pillow`). `--dims` and
  `panelmap.html` generation work with no dependencies.
- The `<img src>` / `width` / `height` in `panelmap.html` are only for browser
  preview; `crtall.js` reads just the `<area>` elements.
