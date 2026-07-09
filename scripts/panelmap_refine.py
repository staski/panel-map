#!/usr/bin/env python3
"""
panelmap_refine.py — snap eyeballed circle areas to the instrument bezel.

Vision is good at *locating* a round instrument but bad at pixel-precise center
and radius (hence the drift/mis-sizing you get from hand-estimated coords). This
tool fixes that geometrically: it takes each `circle` area in an areas.json as a
*seed*, then uses the panel's grayscale contrast — dark instrument bezel against
the lighter-gray panel — to find the true outer bezel edge and snap the center
and radius to it.

Method (per circle):
  1. Cast rays outward from the seed center at many angles.
  2. On each ray, find the radius of the strongest dark->light step within a band
     around the seed radius — that's the bezel/panel edge for that angle.
  3. Robustly fit a circle (algebraic Kasa fit + iterative outlier rejection) to
     the collected edge points. Rays spoiled by markings, screws, adjacent
     instruments, or yoke occlusion fall out as outliers.
  4. Sanity-clamp: if the fit wanders too far from the seed, keep the seed and
     flag it (better an honest un-refined circle than a confidently wrong one).

Only `circle` areas are refined; `rect` areas are copied through unchanged.

Known limitations (v1) — always eyeball the overlay:
  * Gauges with strong concentric inner rings (e.g. a CDI's compass card /
    glideslope scale) *and* weak bezel/panel contrast can snap to an inner ring
    and come out too small.
  * Partial occlusion (a control yoke covering part of a gauge) can pull the
    center toward the visible side; the coverage guard only catches gaps > 150°.
  For those, override the refined value with the seed by hand.

Usage:
  python3 scripts/panelmap_refine.py --image panel.png --areas areas.json --outdir ./out

Outputs:
  <outdir>/areas.refined.json   the areas.json with refined circle coords
  <outdir>/refine_overlay.png   seeds (yellow) vs refined (green), for eyeballing

Requires Pillow. This is a refinement pass — always eyeball the overlay; it does
not replace human verification.
"""

import argparse
import json
import math
import os
import sys


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


class Gray:
    """Grayscale image with clamped bilinear sampling."""
    def __init__(self, path):
        try:
            from PIL import Image
        except ImportError:
            die("Pillow is required (`pip3 install pillow`)")
        self.im = Image.open(path).convert("L")
        self.W, self.H = self.im.size
        self.px = self.im.load()

    def at(self, x, y):
        # clamp + bilinear
        if x < 0: x = 0.0
        if y < 0: y = 0.0
        if x > self.W - 1: x = self.W - 1.0
        if y > self.H - 1: y = self.H - 1.0
        x0, y0 = int(x), int(y)
        x1, y1 = min(x0 + 1, self.W - 1), min(y0 + 1, self.H - 1)
        fx, fy = x - x0, y - y0
        p = self.px
        top = p[x0, y0] * (1 - fx) + p[x1, y0] * fx
        bot = p[x0, y1] * (1 - fx) + p[x1, y1] * fx
        return top * (1 - fy) + bot * fy


def edge_radius(img, cx, cy, ang, r, rlo, rhi, min_step):
    """Along a ray at angle `ang`, return the radius of the bezel->panel edge
    within [rlo, rhi], or None if too weak. The edge is a dark inner side (bezel)
    followed by a *sustained* lighter region (panel). Requiring the outside to
    stay light over a longer span rejects inner rings (compass card, glideslope
    scale) whose 'outside' quickly runs back into more dark bezel."""
    ca, sa = math.cos(ang), math.sin(ang)
    step = 0.5
    inside_win = 4          # ~2px just inside
    outside_win = 14        # ~7px outside must stay panel-light
    # sample far enough past rhi that the outside window is always available
    n = int((rhi - rlo) / step) + 1 + outside_win + 2
    prof = [img.at(cx + (rlo + i * step) * ca, cy + (rlo + i * step) * sa)
            for i in range(n)]
    last_edge_i = int((rhi - rlo) / step)
    best_score, best_rad = -1e9, None
    for i in range(inside_win, last_edge_i + 1):
        inside = sum(prof[i - inside_win:i]) / inside_win
        outside = sum(prof[i + 1:i + 1 + outside_win]) / outside_win
        score = outside - inside
        if score > best_score:
            best_score, best_rad = score, rlo + i * step
    if best_score < min_step:
        return None
    return best_rad


def kasa_fit(points):
    """Algebraic circle fit. Returns (cx, cy, r) or None."""
    n = len(points)
    if n < 3:
        return None
    # solve A [D E F]^T = b for x^2+y^2 + D x + E y + F = 0
    Sxx = Sxy = Syy = Sx = Sy = Sxz = Syz = Sz = 0.0
    for x, y in points:
        z = x * x + y * y
        Sxx += x * x; Sxy += x * y; Syy += y * y
        Sx += x; Sy += y
        Sxz += x * z; Syz += y * z; Sz += z
    # normal equations matrix M [D E F] = rhs
    M = [[Sxx, Sxy, Sx],
         [Sxy, Syy, Sy],
         [Sx,  Sy,  float(n)]]
    rhs = [-Sxz, -Syz, -Sz]
    sol = solve3(M, rhs)
    if sol is None:
        return None
    D, E, F = sol
    cx, cy = -D / 2.0, -E / 2.0
    val = cx * cx + cy * cy - F
    if val <= 0:
        return None
    return cx, cy, math.sqrt(val)


def solve3(M, b):
    """Solve a 3x3 linear system by Gaussian elimination with partial pivoting."""
    a = [row[:] + [b[i]] for i, row in enumerate(M)]
    for col in range(3):
        piv = max(range(col, 3), key=lambda r: abs(a[r][col]))
        if abs(a[piv][col]) < 1e-9:
            return None
        a[col], a[piv] = a[piv], a[col]
        for r in range(3):
            if r != col:
                f = a[r][col] / a[col][col]
                for k in range(col, 4):
                    a[r][k] -= f * a[col][k]
    return [a[i][3] / a[i][i] for i in range(3)]


def refine_circle(img, cx, cy, r, angles=120, max_center_shift=0.45, radius_tol=0.45):
    """Return (ncx, ncy, nr, inliers) or None if the fit is untrustworthy."""
    rlo, rhi = r * 0.72, r * 1.40
    min_step = 18  # minimum dark->light contrast to accept an edge
    pts = []
    for k in range(angles):
        ang = 2 * math.pi * k / angles
        er = edge_radius(img, cx, cy, ang, r, rlo, rhi, min_step)
        if er is not None:
            pts.append((cx + er * math.cos(ang), cy + er * math.sin(ang)))
    if len(pts) < 12:
        return None
    fit = kasa_fit(pts)
    if fit is None:
        return None
    # iterative outlier rejection: drop points far from the fitted circle, refit
    for _ in range(3):
        fcx, fcy, fr = fit
        res = [abs(math.hypot(x - fcx, y - fcy) - fr) for x, y in pts]
        med = sorted(res)[len(res) // 2]
        thresh = max(2.0, 2.5 * med)
        keep = [p for p, e in zip(pts, res) if e <= thresh]
        if len(keep) < 12 or len(keep) == len(pts):
            pts = keep or pts
            break
        pts = keep
        fit = kasa_fit(pts)
        if fit is None:
            return None
    fcx, fcy, fr = fit
    # sanity clamp: distrust fits that wander far from the seed
    if math.hypot(fcx - cx, fcy - cy) > max_center_shift * r:
        return None
    if abs(fr - r) > radius_tol * r:
        return None
    # angular-coverage guard: an under-covered circle (e.g. a gauge whose edge is
    # occluded by a yoke) is under-constrained. If the inliers leave a big gap,
    # the center/radius are unreliable — keep the seed instead.
    angs = sorted(math.atan2(y - fcy, x - fcx) for x, y in pts)
    max_gap = max([angs[0] + 2 * math.pi - angs[-1]] +
                  [angs[i + 1] - angs[i] for i in range(len(angs) - 1)])
    if max_gap > math.radians(150):
        return None
    return fcx, fcy, fr, len(pts)


def main():
    p = argparse.ArgumentParser(description="Snap circle areas to the instrument bezel.")
    p.add_argument("--image", help="panel photo (defaults to the areas file's 'image')")
    p.add_argument("--areas", required=True, help="areas.json to refine")
    p.add_argument("--outdir", default=".", help="where to write refined json + overlay")
    p.add_argument("--angles", type=int, default=120, help="rays per circle (default 120)")
    args = p.parse_args()

    if not os.path.isfile(args.areas):
        die(f"areas file not found: {args.areas}")
    with open(args.areas) as f:
        data = json.load(f)
    areas = data["areas"] if isinstance(data, dict) else data

    image = args.image
    if not image and isinstance(data, dict) and data.get("image"):
        mi = data["image"]
        image = mi if os.path.isabs(mi) else \
            os.path.join(os.path.dirname(os.path.abspath(args.areas)), mi)
    if not image or not os.path.isfile(image):
        die("no readable image: pass --image or set 'image' in the areas file")

    img = Gray(image)
    os.makedirs(args.outdir, exist_ok=True)

    report = []
    for a in areas:
        if str(a.get("shape", "")).lower() != "circle":
            continue
        cx, cy, r = a["coords"]
        res = refine_circle(img, cx, cy, r, angles=args.angles)
        title = a.get("title", "?")
        if res is None:
            report.append((title, (cx, cy, r), None, 0))
            continue
        ncx, ncy, nr, inl = res
        a["coords"] = [round(ncx), round(ncy), round(nr)]
        report.append((title, (cx, cy, r), (round(ncx), round(ncy), round(nr)), inl))

    out_json = os.path.join(args.outdir, "areas.refined.json")
    with open(out_json, "w") as f:
        json.dump(data, f, indent=2)
    print(f"wrote {out_json}")

    render_overlay(image, report, areas, os.path.join(args.outdir, "refine_overlay.png"))

    print("\ncircle refinements (seed -> refined, Δcenter, Δr, inliers):")
    for title, seed, ref, inl in report:
        if ref is None:
            print(f"  {title:28s} seed {seed}  ->  KEPT SEED (no confident fit)")
        else:
            dc = math.hypot(ref[0] - seed[0], ref[1] - seed[1])
            dr = ref[2] - seed[2]
            print(f"  {title:28s} {tuple(seed)} -> {tuple(ref)}  "
                  f"Δc={dc:.1f}px Δr={dr:+d}px  ({inl} pts)")


def render_overlay(image_path, report, areas, out_path):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("note: Pillow missing — skipping overlay", file=sys.stderr)
        return
    img = Image.open(image_path).convert("RGB")
    d = ImageDraw.Draw(img)
    font = None
    for fp in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            font = ImageFont.truetype(fp, 13); break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default()
    yellow, green = (255, 210, 0), (0, 255, 60)
    # seeds (yellow) then refined (green) on top
    for title, seed, ref, inl in report:
        cx, cy, r = seed
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=yellow, width=2)
    for title, seed, ref, inl in report:
        if ref is None:
            continue
        cx, cy, r = ref
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=green, width=3)
        b = d.textbbox((cx - r + 3, cy - r + 2), title, font=font)
        d.rectangle([b[0] - 2, b[1] - 1, b[2] + 2, b[3] + 1], fill=(0, 0, 0))
        d.text((cx - r + 3, cy - r + 2), title, fill=green, font=font)
    img.save(out_path)
    print(f"wrote {out_path}  (yellow = seed, green = refined)")


if __name__ == "__main__":
    main()
