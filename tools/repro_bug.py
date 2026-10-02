#!/usr/bin/env python3
"""Reproduce reported bugs: 1) wheel zoom both directions -> in?
2) searoute final state disconnected (yellow Pacific, red Atlantic)."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = Path("/workspace/projects/history-geography-learning-app/index.html").resolve().as_uri() + "?v=110"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append("console:" + m.text) if m.type == "error" else None)
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(2500)
    pg.select_option("#lesson-select", "lessons/magellan/voyage.json")
    pg.wait_for_timeout(4500)  # animation done

    out = {}
    # --- zoom direction test ---
    vbw = pg.evaluate("document.querySelector('#map').viewBox.baseVal.width")
    pg.mouse.move(720, 450)
    pg.mouse.wheel(0, -400)   # up -> zoom in expected
    pg.wait_for_timeout(400)
    up = pg.evaluate("document.querySelector('#map').viewBox.baseVal.width")
    pg.mouse.wheel(0, 400)    # down -> zoom out expected
    pg.wait_for_timeout(400)
    down = pg.evaluate("document.querySelector('#map').viewBox.baseVal.width")
    out["zoom"] = {"start": vbw, "after_up": up, "after_down": down}

    # reset and inspect searoutes final state
    pg.evaluate("window.AtlasMap.resetView()")
    pg.wait_for_timeout(500)
    out["routes"] = pg.evaluate("""() => {
      const rs = [...document.querySelectorAll('#map path.searoute')];
      return rs.map(r => {
        const cs = getComputedStyle(r);
        const d = r.getAttribute('d');
        return {
          stroke: r.getAttribute('stroke'),
          nSubpaths: (d.match(/M/g) || []).length,
          dasharray: cs.strokeDasharray,
          dashoffset: cs.strokeDashoffset,
          transition: cs.transition,
          totalLen: Math.round(r.getTotalLength()),
        };
      });
    }""")
    pg.screenshot(path="/tmp/repro-full.png")
    b.close()

print(json.dumps(out, indent=1))
print("errors:", errs)
