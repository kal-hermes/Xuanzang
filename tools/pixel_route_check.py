#!/usr/bin/env python3
"""Pixel-level route continuity check: sample the projected route
path in screen coords and verify gold/red pixels exist along it."""
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = Path("/workspace/projects/history-geography-learning-app/index.html").resolve().as_uri() + "?v=112"
SHOT = "/tmp/final-routes2.png"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1600, "height": 1000})
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(2500)
    pg.select_option("#lesson-select", "lessons/magellan/voyage.json")
    pg.wait_for_timeout(5000)
    pg.screenshot(path=SHOT)
    # sample points along each searoute via getPointAtLength -> screen
    pts = pg.evaluate("""() => {
      const svg = document.querySelector('#map');
      const r = svg.getBoundingClientRect();
      const vb = svg.viewBox.baseVal;
      const s = Math.min(r.width / vb.width, r.height / vb.height);
      const ox = (r.width - vb.width * s) / 2, oy = (r.height - vb.height * s) / 2;
      const out = {};
      for (const route of svg.querySelectorAll('path.searoute')) {
        const col = route.getAttribute('stroke');
        const len = route.getTotalLength();
        const samples = [];
        for (let d = 0; d <= len; d += len / 60) {
          const pt = route.getPointAtLength(d);
          if (pt.x < vb.x || pt.x > vb.x + vb.width) continue; // offscreen antimeridian jump
          samples.push([Math.round(r.left + ox + (pt.x - vb.x) * s),
                        Math.round(r.top + oy + (pt.y - vb.y) * s)]);
        }
        out[col] = samples;
      }
      return out;
    }""")
    b.close()

from PIL import Image
img = Image.open(SHOT).convert("RGB")
W, H = img.size

def has_color_near(x, y, target, tol=60, radius=4):
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            xx, yy = x + dx, y + dy
            if 0 <= xx < W and 0 <= yy < H:
                r, g, b = img.getpixel((xx, yy))
                if abs(r - target[0]) < tol and abs(g - target[1]) < tol and abs(b - target[2]) < tol:
                    return True
    return False

for color, samples in pts.items():
    target = {"#ffd24a": (255, 210, 74), "#e05674": (224, 86, 116)}[color]
    missing = [s for s in samples if not has_color_near(s[0], s[1], target)]
    print(f"{color}: {len(samples)} samples, missing color at {len(missing)}")
    if missing:
        print("  first missing:", missing[:6], " last:", missing[-3:])
