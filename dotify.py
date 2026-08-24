"""
dotify.py  –  Convert a photo to a coloured dot-matrix SVG
Crops to portrait, focuses on subject, suppresses busy backgrounds
"""
import argparse
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
import numpy as np


def dotify(src: Path, dst: Path, cols: int = 80, dot_r: float = 3.0,
           equalize: bool = True, detail: float = 0.7,
           crop_top: float = 0.0, crop_left: float = 0.25,
           crop_right: float = 0.75, crop_bottom: float = 1.0):
    img = Image.open(src).convert("RGB")
    w, h = img.size

    # Crop to region of interest (focus on face/subject)
    left   = int(w * crop_left)
    right  = int(w * crop_right)
    top    = int(h * crop_top)
    bottom = int(h * crop_bottom)
    img = img.crop((left, top, right, bottom))

    # Force portrait aspect 4:5
    cw, ch = img.size
    target_h = int(cw * 1.4)
    if ch > target_h:
        top_crop = int(ch * 0.05)   # small top trim
        img = img.crop((0, top_crop, cw, top_crop + target_h))

    if equalize:
        r, g, b = img.split()
        img = Image.merge("RGB", (
            ImageOps.equalize(r),
            ImageOps.equalize(g),
            ImageOps.equalize(b)
        ))

    # Boost contrast and saturation so dots pop
    img = ImageEnhance.Contrast(img).enhance(1.4)
    img = ImageEnhance.Color(img).enhance(1.6)
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=int(detail * 160), threshold=2))

    # Downsample to grid
    cell = img.width / cols
    rows = int(img.height / cell)
    small = img.resize((cols, rows), Image.LANCZOS)
    pixels = np.array(small)
    gray   = np.array(small.convert("L"))

    spacing = dot_r * 2.8
    svg_w   = cols * spacing
    svg_h   = rows * spacing

    # Background colour from corners — suppress dots that match it
    corner_samples = [gray[0,0], gray[0,-1], gray[-1,0], gray[-1,-1]]
    bg_brightness = float(np.mean(corner_samples)) / 255.0

    circles = []
    for row in range(rows):
        for col in range(cols):
            bright = gray[row, col] / 255.0

            # Skip very dark dots (black background)
            if bright < 0.06:
                continue

            # If background is light, skip near-background dots
            if bg_brightness > 0.5 and bright > 0.88:
                continue

            r_val, g_val, b_val = pixels[row, col]
            r_dot = dot_r * (0.25 + 0.75 * bright)
            cx = (col + 0.5) * spacing
            cy = (row + 0.5) * spacing
            circles.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r_dot:.2f}" '
                f'fill="rgb({r_val},{g_val},{b_val})"/>'
            )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {svg_w:.0f} {svg_h:.0f}" '
        f'width="{svg_w:.0f}" height="{svg_h:.0f}">\n'
        f'<rect width="100%" height="100%" fill="#0d1117"/>\n'
        + "\n".join(circles)
        + "\n</svg>"
    )

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(svg, encoding="utf-8")
    print(f"Done → {dst}  ({len(circles)} dots, {cols}x{rows} grid)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--cols",        type=int,   default=80)
    ap.add_argument("--dot-r",       type=float, default=3.0)
    ap.add_argument("--detail",      type=float, default=0.7)
    ap.add_argument("--crop-left",   type=float, default=0.25)
    ap.add_argument("--crop-right",  type=float, default=0.75)
    ap.add_argument("--crop-top",    type=float, default=0.0)
    ap.add_argument("--crop-bottom", type=float, default=1.0)
    ap.add_argument("--equalize",    action="store_true", default=True)
    args = ap.parse_args()
    dotify(
        Path(args.src), Path(args.output),
        cols=args.cols, dot_r=args.dot_r,
        detail=args.detail, equalize=args.equalize,
        crop_left=args.crop_left, crop_right=args.crop_right,
        crop_top=args.crop_top,   crop_bottom=args.crop_bottom,
    )
