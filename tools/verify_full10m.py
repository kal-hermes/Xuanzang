#!/usr/bin/env python3
"""Full verification of the full-10m + progressive-render change.
v2: dots-on-route check runs in equirectangular (flat) projection so
distances are meaningful; land-crossing check likewise."""
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = Path("/workspace/projects/history-geography-learning-app/index.html").resolve().as_uri() + "?v=151"
SHOTS = Path("tools/scratch")
SHOTS.mkdir(exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1600, "height": 1000})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(5000)

    for lesson in ["lessons/magellan/voyage.json", "lessons/xuanzang/journey.json"]:
        pg.select_option("#lesson-select", lesson)
        pg.wait_for_timeout(3500)
        for proj in ["equirectangular", "globe"]:
            pg.select_option("#projection-select", proj)
            pg.wait_for_timeout(2500)
    print("errors after all lesson/proj combos:", errs)

    # flat projection checks
    pg.select_option("#lesson-select", "lessons/magellan/voyage.json")
    pg.wait_for_timeout(3500)
    pg.select_option("#projection-select", "equirectangular")
    pg.wait_for_timeout(3000)

    res = pg.evaluate("""(() => {
      const svg = document.querySelector('#map');
      const routes = [...svg.querySelectorAll('path.searoute')];
      const countries = [...svg.querySelectorAll('#countries path')];
      const svgPt = svg.createSVGPoint();
      const vb = svg.viewBox.baseVal;
      // dots on route
      const m = window.AtlasMap;
      const L = window.ATLAS_LESSONS['lessons/magellan/voyage.json'];
      const P = m.project;
      const far = [];
      for (const s of L.stops) {
        const c = P(s.coords);
        let best = 1e9;
        for (const r of routes) {
          const len = r.getTotalLength();
          for (let d = 0; d <= len; d += 6) {
            const pt = r.getPointAtLength(d);
            best = Math.min(best, Math.hypot(pt.x - c[0], pt.y - c[1]));
          }
        }
        if (best > 6) far.push([s.id, Math.round(best * 10) / 10]);
      }
      // land crossings (FULL 10m polygons now)
      let land = 0, sea = 0;
      const hits = [];
      for (const r of routes) {
        const len = r.getTotalLength();
        for (let d = 0; d <= len; d += 3) {
          const pt = r.getPointAtLength(d);
          if (pt.x < vb.x || pt.x > vb.x + vb.width) continue;
          svgPt.x = pt.x; svgPt.y = pt.y;
          for (const c of countries) {
            if (c.isPointInFill(svgPt)) { land++; if (hits.length < 20) hits.push([Math.round(pt.x), Math.round(pt.y), c.dataset.iso3]); break; }
          }
          sea++;
        }
      }
      return {far, land, sea, hits};
    })""")
    print("stops far from route (flat):", res["far"])
    print("land hits:", res["land"], "/", res["sea"], res["hits"][:10])
    pg.screenshot(path=str(SHOTS / "full10m-flat.png"))

    # globe drag behaviour
    pg.select_option("#projection-select", "globe")
    pg.wait_for_timeout(2500)
    before = pg.evaluate("document.querySelectorAll('#countries path').length")
    pg.mouse.move(800, 500)
    pg.mouse.down()
    pg.mouse.move(720, 470, steps=10)
    mid = pg.evaluate("getComputedStyle(document.querySelector('#countries-quick')).display !== 'none'")
    pg.mouse.move(650, 450, steps=10)
    pg.mouse.up()
    pg.wait_for_timeout(1200)
    after = pg.evaluate("""(() => ({
      quickHidden: getComputedStyle(document.querySelector('#countries-quick')).display === 'none',
      nVisible: [...document.querySelectorAll('#countries path')].filter((e) => (e.getAttribute('d') || '').length > 2).length,
    }))()""")
    print(f"globe drag: countries={before} quickShownMidDrag={mid} afterMouseup={after}")
    pg.screenshot(path=str(SHOTS / "full10m-globe.png"))
    b.close()
print("done")
