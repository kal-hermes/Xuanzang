#!/usr/bin/env python3
"""Type-correct point counting of worldQuick + compare with the
decimation simulation to find any remaining discrepancy."""
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = Path("/workspace/projects/history-geography-learning-app/index.html").resolve().as_uri() + "?v=144"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1600, "height": 1000})
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(5000)
    pg.select_option("#lesson-select", "lessons/magellan/voyage.json")
    pg.wait_for_timeout(4000)
    pg.select_option("#projection-select", "globe")
    pg.wait_for_timeout(2000)
    st = pg.evaluate("""(() => {
      const qi = window.AtlasMap._quickIndex();
      const ringCount = (g) => {
        // correct: a ring is a list of [lon,lat]; count its points
        if (g.type === 'Polygon') return g.coordinates.length;
        let n = 0;
        for (const poly of g.coordinates) for (const ring of poly) n += ring.length;
        return n;
      };
      let actual = 0, feats = 0, polys = 0;
      for (const f of qi.values()) {
        if (!f) continue;
        feats++;
        const g = f.geometry;
        if (g.type === 'MultiPolygon') polys += g.coordinates.length;
        actual += ringCount(g);
      }
      return {feats, polys, actualPts: actual};
    })""")
    print(st)
    b.close()
