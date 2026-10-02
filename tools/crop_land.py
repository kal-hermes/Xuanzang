#!/usr/bin/env python3
"""Zoomed crops of every land-touch region for visual inspection."""
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = Path("/workspace/projects/history-geography-learning-app/index.html").resolve().as_uri() + "?v=122"

# regions with reported land hits: [name, lon, lat, zoom]
REGIONS = [
    ("cpv", -23.6, 15.0, 8),
    ("brazil-coast", -40.0, -21.5, 5),
    ("plata", -56.0, -35.2, 6),
    ("sanjulian", -67.7, -49.4, 7),
    ("strait", -72.5, -53.2, 9),
    ("cebu", 124.1, 10.4, 10),
    ("borneo", 116.5, 6.5, 7),
    ("palawan", 118.5, 9.3, 8),
]

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1600, "height": 1000})
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(2500)
    pg.select_option("#lesson-select", "lessons/magellan/voyage.json")
    pg.wait_for_timeout(5000)
    for name, lon, lat, f in REGIONS:
        pg.evaluate("""(([lon, lat, f]) => {
          const svg = document.querySelector('#map');
          const vb = svg.viewBox.baseVal;
          const c = window.AtlasMap.project([lon, lat]);
          svg.setAttribute('viewBox',
            `${c[0] - vb.width / f / 2} ${c[1] - vb.height / f / 2} ${vb.width / f} ${vb.height / f}`);
        })""", [lon, lat, f])
        pg.wait_for_timeout(400)
        pg.screenshot(path=f"/tmp/zoom-{name}.png")
    b.close()
print("crops saved")
