#!/usr/bin/env python3
"""Pixel-audit the mid-drag globe screenshot: count land-fill colored
pixels (#2c3d4f) vs ocean (#0d1420) vs coast stroke (#6f8ca8)."""
from PIL import Image

for name in ("globe-drag-mid.png", "globe-drag-after.png"):
    im = Image.open(f"tools/scratch/{name}").convert("RGB")
    w, h = im.size
    px = im.load()
    counts = {"land": 0, "ocean": 0, "stroke": 0, "other": 0}
    def cls(c):
        r, g, b = c
        def near(t, tol=18):
            return abs(r - t[0]) <= tol and abs(g - t[1]) <= tol and abs(b - t[2]) <= tol
        if near((0x2c, 0x3d, 0x4f)): return "land"
        if near((0x0d, 0x14, 0x20), 10): return "ocean"
        if near((0x6f, 0x8c, 0xa8), 40): return "stroke"
        return "other"
    for y in range(0, h, 4):
        for x in range(0, w, 4):
            counts[cls(px[x, y])] += 1
    print(name, counts)
