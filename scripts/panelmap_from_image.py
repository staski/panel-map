#!/usr/bin/env python3
"""
panelmap_from_image.py — validate and clean an areas.json panel map.

The instrument *detection* (which box is what) comes from a vision pass (Claude
looking at the cockpit photo). This script is the deterministic gate after it:
it validates that areas.json meets the schema the rest of the toolchain needs
and writes back a cleaned copy.

It:
  * checks every area has a usable `title` (falling back to label/name/id with a
    warning), a valid `shape` (rect|circle) and the right number of numeric
    `coords`;
  * rounds coords to ints and normalises rect coords to [x1<x2, y1<y2];
  * wraps a bare array, defaults the map `name`, and warns on a missing `image`;
  * preserves every other field (text, img, doc, …);
  * optionally bounds-checks coords against the image, and can render a
    verification overlay (`--overlay`) — though the graphical editor
    (scripts/panelmap_editor.html) is the usual way to view/adjust the map.

Usage
-----
  # validate + clean in place
  python3 scripts/panelmap_from_image.py --areas areas.json

  # write the cleaned copy elsewhere, and also drop a verification overlay
  python3 scripts/panelmap_from_image.py --areas areas.json --out clean.json \
      --image panel.jpg --overlay

  # just print the image's pixel dimensions (handy when hand-writing coords)
  python3 scripts/panelmap_from_image.py --image panel.jpg --dims

areas.json schema (see scripts/PANELMAP_WORKFLOW.md for the full contract)
  {
    "name": "panel",                     # optional, defaults to "panel"
    "image": "images/panel.jpg",         # panel photo (required for the runtime app)
    "areas": [
      {"title": "Clock",             "shape": "circle", "coords": [102, 95, 54]},
      {"title": "Airspeed Indicator","shape": "rect",   "coords": [175, 45, 290, 160]}
    ]
  }
  - every area MUST have a `title` (the human instrument name — not an id/number)
  - "circle" coords are [cx, cy, r]; "rect" coords are [x1, y1, x2, y2]
  - a bare array is accepted and wrapped as { "name": "panel", "areas": [...] }

Overlay rendering requires Pillow; everything else works with no dependencies.
"""

import argparse
import json
import os
import sys


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def image_size(path):
    """Return (width, height) in pixels. Uses Pillow if available, else a
    minimal PNG/JPEG header parser so --dims works with no dependencies."""
    try:
        from PIL import Image
        with Image.open(path) as im:
            return im.size
    except ImportError:
        pass
    with open(path, "rb") as f:
        head = f.read(26)
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")
    if head[:2] == b"\xff\xd8":
        with open(path, "rb") as f:
            f.read(2)
            while True:
                b = f.read(1)
                if not b:
                    break
                if b != b"\xff":
                    continue
                marker = f.read(1)
                while marker == b"\xff":
                    marker = f.read(1)
                if marker[0] in (0xC0, 0xC1, 0xC2, 0xC3):
                    f.read(3)
                    h = int.from_bytes(f.read(2), "big")
                    w = int.from_bytes(f.read(2), "big")
                    return w, h
                seg_len = int.from_bytes(f.read(2), "big")
                f.seek(seg_len - 2, os.SEEK_CUR)
    die(f"could not read image dimensions from {path} (install Pillow for more formats)")


def clean_areas(doc):
    """Validate + normalise an areas document IN PLACE, preserving every field.
    Returns the (possibly wrapped) document. die()s on unrecoverable problems."""
    if isinstance(doc, list):
        doc = {"areas": doc}
    if not isinstance(doc, dict) or not isinstance(doc.get("areas"), list):
        die("areas file must be a JSON array or an object with an 'areas' key")
    areas = doc["areas"]
    if not areas:
        die("areas file contains no areas")
    doc.setdefault("name", "panel")

    seen = set()
    fell_back = 0
    for i, a in enumerate(areas):
        if not isinstance(a, dict):
            die(f"area #{i} is not an object")

        title = a.get("title")
        if title is None or str(title).strip() == "":
            for alt in ("label", "name", "id"):     # tolerate common variations
                if a.get(alt) not in (None, ""):
                    title = a.get(alt)
                    fell_back += 1
                    break
        title = str(title or "").strip()
        if not title:
            die(f"area #{i} has no usable label (need 'title', or a text id/name/label)")

        shape = str(a.get("shape", "")).strip().lower()
        if shape not in ("rect", "circle"):
            die(f"area '{title}': shape must be 'rect' or 'circle', got '{shape}'")

        coords = a.get("coords", [])
        if not isinstance(coords, list) or not all(isinstance(c, (int, float)) for c in coords):
            die(f"area '{title}': coords must be a list of numbers")
        need = 3 if shape == "circle" else 4
        if len(coords) != need:
            die(f"area '{title}': {shape} needs {need} coords, got {len(coords)}")
        coords = [int(round(c)) for c in coords]
        if shape == "rect":
            x0, y0, x1, y1 = coords
            coords = [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]

        a["title"], a["shape"], a["coords"] = title, shape, coords   # preserve other keys

        key = title.lower()
        if key in seen:
            print(f"warning: duplicate title '{title}' — the toolchain keys on "
                  f"title, so this will collide", file=sys.stderr)
        seen.add(key)

    if fell_back:
        print(f"warning: {fell_back} area(s) had no 'title' — used label/name/id "
              f"instead. Give each area a proper 'title' (the toolchain keys on it).",
              file=sys.stderr)
    if not doc.get("image"):
        print("note: no top-level 'image' — set it to the panel photo "
              "(e.g. images/panel.jpg) for the runtime app.", file=sys.stderr)
    return doc


def bounds_check(areas, w, h):
    for a in areas:
        c = a["coords"]
        if a["shape"] == "circle":
            x0, y0, x1, y1 = c[0] - c[2], c[1] - c[2], c[0] + c[2], c[1] + c[2]
        else:
            x0, y0, x1, y1 = c
        if x0 < 0 or y0 < 0 or x1 > w or y1 > h:
            print(f"warning: area '{a['title']}' extends outside the {w}x{h} image: {c}",
                  file=sys.stderr)


def render_overlay(image_path, areas, out_path):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("note: Pillow not installed — skipping overlay "
              "(`pip3 install pillow` to enable)", file=sys.stderr)
        return False
    img = Image.open(image_path).convert("RGB")
    d = ImageDraw.Draw(img)
    fs = max(11, img.width // 110)
    font = None
    for fp in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            font = ImageFont.truetype(fp, fs)
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default()
    green, black, label = (0, 255, 60), (0, 0, 0), (0, 255, 120)
    for a in areas:
        c = a["coords"]
        if a["shape"] == "rect":
            d.rectangle(c, outline=green, width=3)
            tx, ty = c[0] + 3, c[1] + 2
        else:
            cx, cy, r = c
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=green, width=3)
            tx, ty = cx - r + 3, cy - r + 2
        b = d.textbbox((tx, ty), a["title"], font=font)
        d.rectangle([b[0] - 2, b[1] - 1, b[2] + 2, b[3] + 1], fill=black)
        d.text((tx, ty), a["title"], fill=label, font=font)
    img.save(out_path)
    return True


def main():
    p = argparse.ArgumentParser(description="Validate and clean an areas.json panel map.")
    p.add_argument("--areas", help="areas.json to validate and clean")
    p.add_argument("--out", help="where to write the cleaned areas.json (default: overwrite --areas)")
    p.add_argument("--image", help="cockpit photo, for --dims / --overlay / bounds-check "
                                   "(defaults to the areas file's 'image')")
    p.add_argument("--dims", action="store_true", help="print the image's WIDTHxHEIGHT and exit")
    p.add_argument("--overlay", nargs="?", const="overlay.png", default=None,
                   help="also render a verification overlay PNG (optional path; default overlay.png)")
    args = p.parse_args()

    doc = None
    if args.areas:
        if not os.path.isfile(args.areas):
            die(f"areas file not found: {args.areas}")
        with open(args.areas) as f:
            doc = json.load(f)

    # resolve the image (only needed for --dims / --overlay / bounds-check)
    image = args.image
    manifest_image = doc.get("image") if isinstance(doc, dict) else None
    if not image and manifest_image and args.areas:
        image = manifest_image if os.path.isabs(manifest_image) else \
            os.path.join(os.path.dirname(os.path.abspath(args.areas)), manifest_image)

    if args.dims:
        if not image:
            die("no image given: pass --image or set 'image' in the areas file")
        if not os.path.isfile(image):
            die(f"image not found: {image}")
        w, h = image_size(image)
        print(f"{w}x{h}")
        return

    if not args.areas:
        die("--areas is required (unless --dims is given)")

    doc = clean_areas(doc)
    areas = doc["areas"]

    if image and os.path.isfile(image):
        w, h = image_size(image)
        bounds_check(areas, w, h)

    out = args.out or args.areas
    with open(out, "w") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"wrote {out}  ({len(areas)} areas)")

    if args.overlay is not None:
        if not image or not os.path.isfile(image):
            print("note: --overlay needs an image (pass --image or set 'image') — skipping.",
                  file=sys.stderr)
        elif render_overlay(image, areas, args.overlay):
            print(f"wrote {args.overlay}")


if __name__ == "__main__":
    main()
