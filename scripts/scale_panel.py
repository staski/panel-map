#!/usr/bin/env python3
"""
scale_panel.py — downscale a cockpit image AND its areas.json together.

Identify instruments on a high-res photo (better recognition), then shrink for
the web. areas.json coords are in the *served* image's pixel space — the
PanelMap component scales from that to the display — so the image and every
coordinate must shrink by the SAME factor to keep the boxes on the instruments.
This tool does both and updates the areas.json 'image' field to the new file.

Pick one target:
  --max-mb  X   shrink (by resolution) until the JPEG is <= X MB
  --max-dim N   longest side <= N pixels
  --scale   F   explicit factor, 0 < F <= 1

Usage:
  python3 scripts/scale_panel.py --image panel.jpg --areas areas.json --max-mb 1.5
  # writes panel_web.jpg + areas_web.json (coords scaled, 'image' updated)
  # override outputs with --out-image / --out-areas; JPEG quality with --quality

Requires Pillow.
"""

import argparse
import io
import json
import os
import sys


def die(msg):
    print("error: " + msg, file=sys.stderr)
    sys.exit(1)


def main():
    p = argparse.ArgumentParser(description="Downscale a cockpit image and its areas.json together.")
    p.add_argument("--image", required=True, help="source (high-res) cockpit photo")
    p.add_argument("--areas", required=True, help="areas.json whose coords match --image")
    p.add_argument("--max-mb", type=float, help="shrink until the output JPEG is <= this many MB")
    p.add_argument("--max-dim", type=int, help="scale so the longest side <= this many pixels")
    p.add_argument("--scale", type=float, help="explicit scale factor (0 < F <= 1)")
    p.add_argument("--quality", type=int, default=85, help="JPEG quality (default 85)")
    p.add_argument("--out-image", help="output image path (default: <image>_web.jpg)")
    p.add_argument("--out-areas", help="output areas.json path (default: <areas>_web.json)")
    args = p.parse_args()

    if args.max_mb is None and args.max_dim is None and args.scale is None:
        die("pick a target: --max-mb, --max-dim or --scale")
    try:
        from PIL import Image
    except ImportError:
        die("Pillow is required (`pip3 install pillow`)")
    for f in (args.image, args.areas):
        if not os.path.isfile(f):
            die("not found: " + f)

    im = Image.open(args.image)
    if im.mode != "RGB":
        im = im.convert("RGB")
    W, H = im.size

    # base scale from --scale / --max-dim (1.0 if only --max-mb is given)
    scale = 1.0
    if args.scale is not None:
        if not (0 < args.scale <= 1):
            die("--scale must be in (0, 1]")
        scale = args.scale
    if args.max_dim is not None:
        scale = min(scale, args.max_dim / max(W, H))

    def encode(sc):
        w, h = max(1, round(W * sc)), max(1, round(H * sc))
        r = im.resize((w, h), Image.LANCZOS)
        buf = io.BytesIO()
        r.save(buf, format="JPEG", quality=args.quality, optimize=True)
        return r, buf.getvalue()

    if args.max_mb is not None:
        target = int(args.max_mb * 1024 * 1024)
        _, data = encode(scale)
        if len(data) > target:                 # binary-search the largest scale that fits
            lo, hi = 0.02, scale
            for _ in range(18):
                mid = (lo + hi) / 2
                _, data = encode(mid)
                if len(data) <= target:
                    lo = mid
                else:
                    hi = mid
            scale = lo

    resized, data = encode(scale)
    nw, nh = resized.size

    out_image = args.out_image or (os.path.splitext(args.image)[0] + "_web.jpg")
    out_areas = args.out_areas or (os.path.splitext(args.areas)[0] + "_web.json")

    ext = os.path.splitext(out_image)[1].lower()
    if ext in (".jpg", ".jpeg", ""):
        if ext == "":
            out_image += ".jpg"
        with open(out_image, "wb") as f:
            f.write(data)
    else:
        resized.save(out_image)

    # scale the areas.json coords by the same factor
    doc = json.load(open(args.areas))
    if isinstance(doc, list):
        doc = {"areas": doc}
    for a in doc.get("areas", []):
        c = a.get("coords")
        if isinstance(c, list):
            a["coords"] = [int(round(v * scale)) for v in c]
    # point 'image' at the new file, keeping any directory prefix
    old = doc.get("image")
    newbase = os.path.basename(out_image)
    doc["image"] = (old.rsplit("/", 1)[0] + "/" + newbase) if isinstance(old, str) and "/" in old \
        else "images/" + newbase
    with open(out_areas, "w") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
        f.write("\n")

    kb = os.path.getsize(out_image) / 1024
    print(f"scale {scale:.4f}:  {W}x{H} -> {nw}x{nh}")
    print(f"wrote {out_image}  ({kb:.0f} kB)")
    print(f"wrote {out_areas}  (coords scaled x{scale:.4f}, image -> {doc['image']})")


if __name__ == "__main__":
    main()
