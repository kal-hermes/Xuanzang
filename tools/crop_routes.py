#!/usr/bin/env python3
"""Crop screenshots of the Magellan routes: mid-Pacific (gold) and
eastern Atlantic (red) to see the reported gaps at pixel level."""
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = Path("/workspace/projects/history-geography-learning-app/index.html").resolve().as_uri() + "?v=110"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(2500)
    pg.select_option("#lesson-select", "lessons/magellan/voyage.json")
    pg.wait_for_timeout(4500)
    geo = pg.evaluate("""() => {
      const svg = document.querySelector('#map');
      const vb = svg.viewBox.baseVal;
      const r = svg.getBoundingClientRect();
      const s = Math.min(r.width / vb.width, r.height / vb.height);
      const ox = (r.width - vb.width * s) / 2, oy = (r.height - vb.height * s) / 2;
      // equirect sphere-fit linear mapping (viewBox 10,255 980x490)
      const scr = (lon, lat) => {
        const x = 10 + (lon + 180) / 360 * 980;
        const y = 255 + (90 - lat) / 180 * 490;
        return [r.left + ox + (x - vb.x) * s, r.top + oy + (y - vb.y) * s];
      };
      return scr([0, 0]);  // probe: should be map center
    }""")
    # verify probe maps to screen center of the svg
    svg_r = pg.evaluate("""() => {
      const r = document.querySelector('#map').getBoundingClientRect();
      return [r.left + r.width / 2, r.top + r.height / 2];
    }""")
    print("probe:", geo, "svg center:", svg_r)

    def scr_of(lon, lat):
        # linear: same math client-side via evaluate each time
        return pg.evaluate("""(([lon, lat]) => {
          const svg = document.querySelector('#map');
          const vb = svg.viewBox.baseVal;
          const r = svg.getBoundingClientRect();
          const s = Math.min(r.width / vb.width, r.height / vb.height);
          const ox = (r.width - vb.width * s) / 2, oy = (r.height - vb.height * s) / 2;
          const x = 10 + (lon + 180) / 360 * 980;
          const y = 255 + (90 - lat) / 180 * 490;
          return [r.left + ox + (x - vb.x) * s, r.top + oy + (y - vb.y) * s];
        })""", [lon, lat])

    mp = scr_of(-150, 5)
    pg.screenshot(path="/tmp/pac-clip.png",
                  clip={"x": mp[0] - 260, "y": mp[1] - 110, "width": 560, "height": 240})
    ea = scr_of(-30, 28)
    pg.screenshot(path="/tmp/atl-clip.png",
                  clip={"x": ea[0] - 100, "y": ea[1] - 110, "width": 340, "height": 340})
    b.close()
print("clips saved")
