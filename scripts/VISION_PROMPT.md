# The vision prompt

The detection step runs in a **fresh Claude session** that has no memory of this
project, so the prompt has to carry it. Everything below exists because a cold
session got it wrong at least once — see the table at the end.

Paste this, attach the cockpit photo, and let it run:

---

```
Create a panel map from the attached cockpit photo.

1. FIRST read BOTH documents, in full:
   https://raw.githubusercontent.com/staski/panel-map/main/scripts/PANELMAP_WORKFLOW.md
   https://raw.githubusercontent.com/staski/panel-map/main/scripts/INSTRUMENT_IDENTIFICATION.md
   INSTRUMENT_IDENTIFICATION.md governs what each instrument is and how to title it.

2. ZOOM IN before deciding anything: crop and magnify each cluster (left six-pack,
   centre avionics stack, right/engine group, sub-panels) at 3-4x. This is what
   reveals partly hidden gauges and gives good centres and radii.

3. BE COMPLETE: read each cluster as a grid and account for every cell, including
   round gauges hidden behind the control yokes. Do NOT map placards, switches,
   circuit breakers, annunciator panels or empty instrument holes.

4. TITLES: read model names off the faceplate where they are printed (GNS430,
   KX155, KMA24, TT31). For indicators use FUNCTIONAL titles - CDI,
   CDI/Glideslope, HSI, ADF Indicator - instead of guessing a model number; put
   any uncertain model in the "text" field, never in "title".

5. Read the aircraft registration off the placard and record it as top-level
   "aircraft".

6. Output areas.json exactly per the OUTPUT CONTRACT: every area needs title,
   shape and coords; include top-level "image" (the photo's filename) and
   "aircraft". Save areas.json and the photo together in one directory.

7. VALIDATE AND SELF-CHECK:
     python3 panelmap_from_image.py --areas areas.json --image <photo>
   (fetch that script from raw.githubusercontent.com if you don't have the repo).
   It writes overlay.png - actually LOOK at that overlay, and fix anything
   misplaced, missing or mislabelled. Repeat until it is right.

8. Finish by listing what you were unsure about (model numbers, ambiguous glass
   displays) so I can confirm those.
```

---

Then bring the resulting `areas.json` and photo back here and run the build:

```sh
scripts/build_panel.sh --image cockpit.jpg --areas areas.json
```

## Why each instruction is there

| Instruction | The failure it prevents |
|---|---|
| Read `INSTRUMENT_IDENTIFICATION.md` **first** | Sessions follow the workflow doc but skip the *linked* identification rules, then mislabel a GI-275 as a G5 or lump a whole avionics stack into one box. |
| Zoom into each cluster | A full-frame look missed three instruments on a real panel (an altimeter, a yoke-hidden VSI and an HSI), and produced looser centres/radii. |
| Grid scan, include yoke-hidden gauges | Round gauges are systematically under-counted; the ones a control yoke crosses are missed most often. |
| Don't map placards / switches / empty holes | A warning annunciator was boxed as the chronometer, and empty instrument cutouts were mapped as gauges. |
| Functional titles for indicators | CDI is the single most common mis-identification — labelled HSI or RMI. A wrong model name is worse than a generic correct one, because the catalogue matches on `title`. |
| Record the registration | It is legible in practically every cockpit photo and becomes the browser page title. |
| Pass `--image` to the validator | Without it the validator cannot bounds-check the coords or record `imageSize`, which is what later protects the map from being scaled twice. |
| Look at the overlay it just produced | Self-correction actually works — one session did this unprompted and caught its own mistakes before finishing. |
| List the uncertainties | Model numbers are the known weak spot; geometry rarely needs correcting, names often do. |

## Keeping this in sync

This prompt points at `PANELMAP_WORKFLOW.md` and `INSTRUMENT_IDENTIFICATION.md`
by raw URL on `main`, so a session always reads the current rules. When a new
recognition rule is learned, it belongs in `INSTRUMENT_IDENTIFICATION.md` — only
add something here if a session ignored the rule despite it being documented.
