#!/usr/bin/env python3
"""Zoom behavior matrix: repeated up/down wheels, pinch (ctrl+wheel),
and whether the zoom center follows the mouse or map center."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = Path("/workspace/projects/history-geography-learning-app/index.html").resolve().as_uri() + "?v=110"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(2500)
    pg.select_option("#lesson-select", "lessons/magellan/voyage.json")
    pg.wait_for_timeout(2000)

    def vb():
        v = pg.evaluate("(() => { const v = document.querySelector('#map').viewBox.baseVal; return [Math.round(v.x), Math.round(v.y), Math.round(v.width), Math.round(v.height)]; })()")
        return v

    out = {}
    out["start"] = vb()
    pg.mouse.move(720, 450)
    for i in range(4):
        pg.mouse.wheel(0, 400)   # DOWN = expect zoom OUT
        pg.wait_for_timeout(250)
    out["after_4_down"] = vb()
    for i in range(8):
        pg.mouse.wheel(0, -400)  # UP = expect zoom IN
        pg.wait_for_timeout(250)
    out["after_8_up"] = vb()
    # pinch gesture
    pg.keyboard.down("Control")
    pg.mouse.wheel(0, -100)
    pg.wait_for_timeout(250)
    pg.keyboard.up("Control")
    out["after_ctrl_wheel"] = vb()
    # zoom center test: put mouse at top-left corner of the map, zoom in,
    # see which point stays fixed
    r = pg.evaluate("(() => document.querySelector('#map').getBoundingClientRect().toJSON())()")
    pg.evaluate("window.AtlasMap.resetView()")
    pg.wait_for_timeout(300)
    mouse_pt = pg.evaluate("""(() => {
      const svg = document.querySelector('#map');
      const v = svg.viewBox.baseVal;
      const r = svg.getBoundingClientRect();
      const s = Math.min(r.width / v.width, r.height / v.height);
      const ox = (r.width - v.width * s) / 2, oy = (r.height - v.height * s) / 2;
      // user-space point under cursor (300, 250):
      return [v.x + (300 - r.left - ox) / s, v.y + (250 - r.top - oy) / s];
    })()""")
    out["user_pt_before"] = mouse_pt
    pg.mouse.move(300, 250)
    pg.mouse.wheel(0, -400)
    pg.wait_for_timeout(300)
    after = vb()
    # map user_pt through new viewBox to screen
    scr_after = pg.evaluate("""(([pt]) => {
      const svg = document.querySelector('#map');
      const v = svg.viewBox.baseVal;
      const r = svg.getBoundingClientRect();
      const s = Math.min(r.width / v.width, r.height / v.height);
      const ox = (r.width - v.width * s) / 2, oy = (r.height - v.height * s) / 2;
      return [Math.round(r.left + ox + (pt[0] - v.x) * s),
              Math.round(r.top + oy + (pt[1] - v.y) * s)];
    })""", [mouse_pt])
    out["same_geo_point_screen_after_zoom"] = scr_after  # (300,250) if mouse-anchored
    out["errors"] = errs
    b.close()

print(json.dumps(out, indent=1))
