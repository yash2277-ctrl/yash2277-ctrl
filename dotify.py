"""
dotify.py  –  Convert a photo to a coloured dot-matrix SVG
Usage: python dotify.py <input_image> -o <output_svg> [--cols 80] [--dot-r 3.2]
"""
import argparse, sys
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter
import numpy as np

def dotify(src: Path, dst: Path, cols: int = 80, dot_r: float = 3.2,
           equalize: bool = True, detail: float = 0.6):
    img = Image.open(src).convert("RGB")

    # Crop to portrait aspect (4:5)
    w, h = img.size
    target_h = int(w * 1.25)
    if h > target_h:
        top = (h - target_h) // 2
        img = img.crop((0, top, w, top + target_h))

    # Resize to working resolution
    cell = img.width / cols
    rows = int(img.height / cell)
    img = img.resize((cols * 4, rows * 4), Image.LANCZOS)

    if equalize:
        r, g, b = img.split()
        r = ImageOps.equalize(r)
        g = ImageOps.equalize(g)
        b = ImageOps.equalize(b)
        img = Image.merge("RGB", (r, g, b))

    # Edge-enhance for better detail
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=int(detail*150), threshold=3))

    # Downsample to dot grid
    small = img.resize((cols, rows), Image.LANCZOS)
    pixels = np.array(small)          # shape (rows, cols, 3)
    gray   = np.array(small.convert("L"))  # brightness

    # SVG dimensions
    spacing = dot_r * 2.8
    svg_w   = cols * spacing
    svg_h   = rows * spacing

    circles = []
    for row in range(rows):
        for col in range(cols):
            bright = gray[row, col] / 255.0
            if bright < 0.04:          # skip nearly-black dots (background)
                continue
            r_val, g_val, b_val = pixels[row, col]
            # Scale dot radius by brightness so bright areas are bigger
            r_dot = dot_r * (0.3 + 0.7 * bright)
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
    print(f"Done → {dst}  ({len(circles)} dots, {cols}×{rows} grid)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--cols",   type=int,   default=80)
    ap.add_argument("--dot-r",  type=float, default=3.2)
    ap.add_argument("--detail", type=float, default=0.6)
    ap.add_argument("--equalize", action="store_true", default=True)
    args = ap.parse_args()
    dotify(Path(args.src), Path(args.output),
           cols=args.cols, dot_r=args.dot_r,
           equalize=args.equalize, detail=args.detail)
