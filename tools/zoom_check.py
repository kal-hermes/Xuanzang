#!/usr/bin/env python3
"""Zoom visual check of the remaining land-hit clusters (strait,
Patagonia, Philippines, Canaries) — screenshots to tools/scratch/."""
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = Path("/workspace/projects/history-geography-learning-app/index.html").resolve().as_uri() + "?v=174"
SHOTS = Path("tools/scratch")
SHOTS.mkdir(exist_ok=True)

CROPS = {
    "strait": ([-70.5, -53.5], 9),
    "patagonia": ([-67.5, -48.5], 7),
    "phl": ([124.5, 10.0], 9),
    "canoaries": ([-16.5, 28.2], 10),
    "brz": ([-42.8, -22.9], 8),
}

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1600, "height": 1000})
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(4000)
    pg.select_option("#lesson-select", "lessons/magellan/voyage.json")
    pg.wait_for_timeout(6000)
    for name, ((lon, lat), f) in CROPS.items():
        pg.evaluate("""(([lon, lat, f]) => {
          const svg = document.querySelector('#map');
          const vb = svg.viewBox.baseVal;
          const c = window.AtlasMap.project([lon, lat]);
          svg.setAttribute('viewBox', `${c[0] - vb.width / f / 2} ${c[1] - vb.height / f / 2} ${vb.width / f} ${vb.height / f}`);
        })""", [lon, lat, f])
        pg.wait_for_timeout(400)
        pg.screenshot(path=str(SHOTS / f"chk-{name}.png"))
    b.close()
print("shots saved to tools/scratch/")
