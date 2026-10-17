#!/usr/bin/env python3
"""Verify: (1) all flat projections show ALL countries (no culling);
(2) flat-projection pan swaps in the decimated quick layer and restores
on mouseup. Run: uv run --with playwright python tools/verify_projection_full.py"""
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = Path("/workspace/projects/history-geography-learning-app/index.html").resolve().as_uri() + "?v=233"

CHECK = r"""() => {
  const svg = document.querySelector('#map');
  const paths = [...document.querySelectorAll('#countries path.country')];
  const empty = paths.filter(p => !p.getAttribute('d')).length;
  const vb = svg.viewBox.baseVal;
  return {
    n: paths.length,
    emptyD: empty,
    vb: [vb.x, vb.y, vb.width, vb.height].map(v => Math.round(v)),
  };
}"""

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1400, "height": 900})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(3500)

    for proj in ["equirectangular", "mercator", "naturalEarth", "robinson"]:
        pg.select_option("#projection-select", proj)
        pg.wait_for_timeout(1800)
        r = pg.evaluate(CHECK)
        print(f"{proj:15s} countries={r['n']} emptyD={r['emptyD']} viewBox={r['vb']}")

    # pan test on robinson
    pg.select_option("#projection-select", "robinson")
    pg.wait_for_timeout(1500)
    box = pg.locator("#map").bounding_box()
    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    before = pg.evaluate("() => { const v = document.querySelector('#map').viewBox.baseVal; return [v.x, v.y]; }")
    pg.mouse.move(cx, cy)
    pg.mouse.down()
    pg.mouse.move(cx - 250, cy - 100, steps=8)
    mid = pg.evaluate("""() => ({
      quick: getComputedStyle(document.querySelector('#countries-quick')).display,
      group: getComputedStyle(document.querySelector('#countries')).display,
      quickD: document.querySelector('#countries-quick').getAttribute('d').length,
    })""")
    pg.wait_for_timeout(80)
    pg.mouse.up()
    pg.wait_for_timeout(300)
    after = pg.evaluate("""() => ({
      quick: getComputedStyle(document.querySelector('#countries-quick')).display,
      group: getComputedStyle(document.querySelector('#countries')).display,
      vb: (() => { const v = document.querySelector('#map').viewBox.baseVal; return [v.x, v.y]; })(),
    })""")
    print("mid-drag  quick=%s group=%s quickDlen=%s" % (mid["quick"], mid["group"], mid["quickD"]))
    print("after-up  quick=%s group=%s panned=%s" % (
        after["quick"], after["group"],
        abs(after["vb"][0] - before[0]) > 1 or abs(after["vb"][1] - before[1]) > 1))
    pg.screenshot(path="tools/scratch/robinson-full.png")
    print("errors:", errs)
    b.close()
