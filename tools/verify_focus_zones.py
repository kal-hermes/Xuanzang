#!/usr/bin/env python3
"""Focus check: land hits in the regions k_sze called out —
Philippines/Brunei (lon 115-129, lat 0-11) and the Strait (lon -77..
-64, lat -56..-45), plus the Banda leg (back, lon 124-129 lat -10..1).
Sample the RENDERED curves via the browser at fine resolution."""
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = Path("/workspace/projects/history-geography-learning-app/index.html").resolve().as_uri() + "?v=208"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1600, "height": 1000})
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(4000)
    pg.select_option("#lesson-select", "lessons/magellan/voyage.json")
    pg.wait_for_timeout(6000)
    res = pg.evaluate("""(() => {
      const routes = [...document.querySelectorAll('path.searoute')];
      const svgPt = document.querySelector('#map').createSVGPoint();
      const countries = [...document.querySelectorAll('#countries path')];
      const landAt = (x, y) => {
        svgPt.x = x; svgPt.y = y;
        for (const c of countries) if (c.isPointInFill(svgPt)) return c.dataset.iso3;
        return null;
      };
      const zones = {
        phl: (lo, la) => lo >= 115 && lo <= 129.5 && la >= 0 && la <= 11,
        strait: (lo, la) => lo >= -77 && lo <= -64 && la >= -56 && la <= -45,
        banda: (lo, la) => lo >= 124 && lo <= 129.5 && la >= -10.5 && la <= 1,
      };
      const out = { phl: 0, strait: 0, banda: 0 };
      const total = { phl: 0, strait: 0, banda: 0 };
      const samples = { phl: [], strait: [], banda: [] };
      routes.forEach((r) => {
        const len = r.getTotalLength();
        for (let d = 0; d <= len; d += 1.5) {
          const q = r.getPointAtLength(d);
          const lo = (q.x - 500) / 2.72222, la = (500 - q.y) / 2.72222;
          for (const z of Object.keys(zones)) {
            if (zones[z](lo, la)) {
              total[z]++;
              const iso = landAt(q.x, q.y);
              if (iso) { out[z]++; if (samples[z].length < 5) samples[z].push([Math.round(lo * 10) / 10, Math.round(la * 10) / 10, iso]); }
            }
          }
        }
      });
      return { landHits: out, samples, total };
    })""")
    print(res)
    pg.screenshot(path="tools/scratch/focus-check.png")
    b.close()
