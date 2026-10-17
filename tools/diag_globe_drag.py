#!/usr/bin/env python3
"""Reproduce: globe drag -> whole globe disappears, only route visible."""
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = Path("/workspace/projects/history-geography-learning-app/index.html").resolve().as_uri() + "?v=232"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1400, "height": 900})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(3500)
    pg.select_option("#lesson-select", "lessons/xuanzang/journey.json")
    pg.wait_for_timeout(4000)
    pg.select_option("#projection-select", "globe")
    pg.wait_for_timeout(2500)

    def state(tag):
        s = pg.evaluate("""() => {
          const ql = document.querySelector('#countries-quick');
          const grp = document.querySelector('#countries');
          const sph = document.querySelector('.sphere');
          const grat = document.querySelector('.graticule');
          const vis = [...document.querySelectorAll('#countries path.country')]
            .filter(p => p.getAttribute('d')).length;
          return {
            qlD: ql ? (ql.getAttribute('d') || '').length : -1,
            qlDisp: ql ? getComputedStyle(ql).display : 'none?',
            grpDisp: grp ? getComputedStyle(grp).display : 'none?',
            sphD: sph ? (sph.getAttribute('d') || '').length : -1,
            gratD: grat ? (grat.getAttribute('d') || '').length : -1,
            vis,
          };
        }""")
        print(tag, s)

    state("before-drag:")
    box = pg.locator("#map").bounding_box()
    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    pg.mouse.move(cx, cy)
    pg.mouse.down()
    pg.mouse.move(cx - 200, cy - 80, steps=10)
    pg.wait_for_timeout(250)
    state("mid-drag:")
    pg.screenshot(path="tools/scratch/globe-drag-mid.png")
    pg.mouse.up()
    pg.wait_for_timeout(400)
    state("after-up:")
    pg.screenshot(path="tools/scratch/globe-drag-after.png")
    print("errors:", errs)
    b.close()
