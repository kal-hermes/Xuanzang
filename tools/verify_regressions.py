#!/usr/bin/env python3
"""Verify the user-reported route regressions are fixed:
1. gold line present Sanlucar -> Tenerife
2. Atlantic track does NOT divert toward Cape of Good Hope
3. no stray gold segment near 0N 126W
4. gold line continuous up to Guam across the antimeridian
Plus regression: stops on route, strait monotone, JS errors."""
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = Path("/workspace/projects/history-geography-learning-app/index.html").resolve().as_uri() + "?v=188"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1600, "height": 1000})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(4000)
    pg.select_option("#lesson-select", "lessons/magellan/voyage.json")
    pg.wait_for_timeout(6000)

    res = pg.evaluate("""(() => {
      const r = [...document.querySelectorAll('path.searoute')][0];
      const len = r.getTotalLength();
      const P = window.AtlasMap.project;
      const L = window.ATLAS_LESSONS['lessons/magellan/voyage.json'];
      const svgPt = document.querySelector('#map').createSVGPoint();
      const countries = [...document.querySelectorAll('#countries path')];
      const landAt = (x, y) => {
        svgPt.x = x; svgPt.y = y;
        for (const c of countries) if (c.isPointInFill(svgPt)) return true;
        return false;
      };
      // sample the rendered curve into lon/lat
      const pts = [];
      for (let d = 0; d <= len; d += 2) {
        const q = r.getPointAtLength(d);
        pts.push([(q.x - 500) / 2.72222, (500 - q.y) / 2.72222]);
      }
      const hasBetween = (lo1, la1, lo2, la2, tol = 1.2) =>
        pts.some((q) => q[0] > Math.min(lo1, lo2) - tol && q[0] < Math.max(lo1, lo2) + tol &&
                        q[1] > Math.min(la1, la2) - tol && q[1] < Math.max(la1, la2) + tol);
      // 1. sanlucar->tenerife coverage: line passes mid-Canary channel
      const canaryLeg = pts.filter((q) => q[0] > -14 && q[0] < -7 && q[1] > 29 && q[1] < 36);
      // 2. no line toward Cape of Good Hope during Atlantic S track:
      // any curve point in Africa south tip box while in west Atlantic?
      const capeBox = pts.filter((q) => q[0] > 12 && q[0] < 24 && q[1] > -38 && q[1] < -30);
      // 3. stray segment near 0N 126W (Pacific)
      const stray = pts.filter((q) => q[0] > -131 && q[0] < -121 && Math.abs(q[1]) < 6);
      // 4. continuity to Guam: points between 150E..170E at 8..14N
      const westPacific = pts.filter((q) => q[0] > 147 && q[0] < 180 && q[1] > 7 && q[1] < 15);
      // stops on route
      const far = [];
      for (const s of L.stops) {
        const c = P(s.coords);
        let best = 1e9;
        for (let d = 0; d <= len; d += 4) {
          const q = r.getPointAtLength(d);
          best = Math.min(best, Math.hypot(q.x - c[0], q.y - c[1]));
        }
        if (best > 6) far.push([s.id, Math.round(best * 10) / 10]);
      }
      // strait monotone
      const lons = pts.filter((q) => q[0] >= -78 && q[0] <= -62).map((q) => q[0]);
      let rev = 0;
      for (let i = 1; i < lons.length; i++) if (lons[i] > lons[i - 1] + 0.7) rev++;
      // land hits
      let land = 0, sea = 0;
      for (let d = 0; d <= len; d += 3) {
        const q = r.getPointAtLength(d);
        sea++;
        if (landAt(q.x, q.y)) land++;
      }
      return {
        canaryPts: canaryLeg.length,
        capeDivertPts: capeBox.length,
        stray0N126W: stray.length,
        westPacificPts: westPacific.length,
        stopsFar: far,
        straitReversals: rev,
        landHits: [land, sea],
      };
    })""")
    for k, v in res.items():
        print(f"{k}: {v}")
    print("JS errors:", errs)
    pg.screenshot(path="tools/scratch/regression-fixed.png")
    b.close()
