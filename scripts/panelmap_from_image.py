#!/usr/bin/env python3
"""
panelmap_from_image.py — scaffold a cockpit-panel image-map from a photo.

The hard part of building a panel map is authoring panelmap.html: measuring
every instrument's pixel box by hand. This tool removes the mechanical toil
around that:

  * reads the image's real pixel dimensions automatically,
  * turns a simple list of instrument regions into a valid panelmap.html in
    the exact <area title shape coords> format that scripts/crtall.js consumes,
  * renders an overlay PNG (boxes + labels drawn on the photo) so the regions
    can be eyeballed and corrected before crtall.js runs.

The instrument *detection* itself (which box is what) is expected to come from
a vision pass (e.g. Claude looking at the photo) and is supplied as a small
JSON areas file. This script is the deterministic scaffolding around it.

Usage
-----
  # print the image's pixel dimensions (handy when hand-writing coords)
  python3 scripts/panelmap_from_image.py --image panel.jpg --dims

  # generate panelmap.html + overlay.png from an areas file
  python3 scripts/panelmap_from_image.py \
      --image panel.jpg --areas areas.json --outdir ./out

areas.json format
-----------------
  {
    "name": "panel",                # optional, defaults to "panel"
    "areas": [
      {"title": "Clock",            "shape": "circle", "coords": [102, 95, 54]},
      {"title": "Airspeed Indicator","shape": "rect",  "coords": [175, 45, 290, 160]}
    ]
  }

  - "circle" coords are [cx, cy, r]
  - "rect"   coords are [x1, y1, x2, y2]
  A bare list (no wrapping object) is also accepted; the map name defaults to "panel".

Overlay rendering requires Pillow (`pip3 install pillow`). Everything else,
including panelmap.html generation and validation, works without it.
"""

import argparse
import json
import os
import sys
import xml.sax.saxutils as sax


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
    # PNG: width/height are big-endian uint32 at bytes 16..24
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        w = int.from_bytes(head[16:20], "big")
        h = int.from_bytes(head[20:24], "big")
        return w, h
    # JPEG: walk the segment markers to the SOF frame
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
                    f.read(3)  # length(2) + precision(1)
                    h = int.from_bytes(f.read(2), "big")
                    w = int.from_bytes(f.read(2), "big")
                    return w, h
                seg_len = int.from_bytes(f.read(2), "big")
                f.seek(seg_len - 2, os.SEEK_CUR)
    die(f"could not read image dimensions from {path} (install Pillow for more formats)")


def load_areas(path):
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, list):
        return "panel", data
    if isinstance(data, dict):
        return data.get("name", "panel"), data.get("areas", [])
    die("areas file must be a JSON list or an object with an 'areas' key")


def validate(areas):
    """Return a cleaned list; raise on structural problems so a bad map never
    silently flows into crtall.js."""
    cleaned = []
    seen = set()
    for i, a in enumerate(areas):
        title = str(a.get("title", "")).strip()
        shape = str(a.get("shape", "")).strip().lower()
        coords = a.get("coords", [])
        if not title:
            die(f"area #{i} has no title")
        if shape not in ("rect", "circle"):
            die(f"area '{title}': shape must be 'rect' or 'circle', got '{shape}'")
        if not all(isinstance(c, (int, float)) for c in coords):
            die(f"area '{title}': coords must all be numbers")
        need = 3 if shape == "circle" else 4
        if len(coords) != need:
            die(f"area '{title}': {shape} needs {need} coords, got {len(coords)}")
        key = title.lower()
        if key in seen:
            print(f"warning: duplicate title '{title}' — crtall.js keys by title, "
                  f"so this will collide", file=sys.stderr)
        seen.add(key)
        cleaned.append({"title": title, "shape": shape,
                        "coords": [int(round(c)) for c in coords]})
    return cleaned


def render_html(map_name, img_basename, w, h, areas):
    lines = [
        "<!DOCTYPE html>",
        "<html>",
        "<body>",
        f'<img src="images/{sax.quoteattr(img_basename)[1:-1]}" '
        f'usemap="#{map_name}" width="{w}" height="{h}">',
        f'<map name="{map_name}">',
    ]
    for a in areas:
        coords = ",".join(str(c) for c in a["coords"])
        lines.append(
            f'  <area title={sax.quoteattr(a["title"])} '
            f'shape="{a["shape"]}" coords="{coords}">'
        )
    lines += ["</map>", "</body>", "</html>", ""]
    return "\n".join(lines)


def render_overlay(image_path, areas, out_path):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("note: Pillow not installed — skipping overlay.png "
              "(`pip3 install pillow` to enable)", file=sys.stderr)
        return False
    img = Image.open(image_path).convert("RGB")
    d = ImageDraw.Draw(img)
    font = None
    for fp in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            font = ImageFont.truetype(fp, 13)
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
    p = argparse.ArgumentParser(description="Scaffold a panel image-map from a photo.")
    p.add_argument("--image", required=True, help="path to the cockpit panel photo")
    p.add_argument("--areas", help="JSON file describing the instrument regions")
    p.add_argument("--dims", action="store_true", help="just print WIDTHxHEIGHT and exit")
    p.add_argument("--outdir", default=".", help="where to write panelmap.html / overlay.png")
    p.add_argument("--no-overlay", action="store_true", help="skip rendering the overlay PNG")
    args = p.parse_args()

    if not os.path.isfile(args.image):
        die(f"image not found: {args.image}")

    w, h = image_size(args.image)
    if args.dims:
        print(f"{w}x{h}")
        return
    if not args.areas:
        die("--areas is required unless --dims is given")
    if not os.path.isfile(args.areas):
        die(f"areas file not found: {args.areas}")

    map_name, raw = load_areas(args.areas)
    if not raw:
        die("areas file contains no areas")
    areas = validate(raw)

    os.makedirs(args.outdir, exist_ok=True)
    html_path = os.path.join(args.outdir, "panelmap.html")
    with open(html_path, "w") as f:
        f.write(render_html(map_name, os.path.basename(args.image), w, h, areas))
    print(f"wrote {html_path}  ({len(areas)} areas, image {w}x{h})")

    if not args.no_overlay:
        overlay_path = os.path.join(args.outdir, "overlay.png")
        if render_overlay(args.image, areas, overlay_path):
            print(f"wrote {overlay_path}")


if __name__ == "__main__":
    main()
