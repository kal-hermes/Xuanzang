#!/usr/bin/env python3
"""Verify zoom-invariant rendering: country strokes, route strokes and
stop dots keep a constant SCREEN size (px) across zoom levels."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = Path("/workspace/projects/history-geography-learning-app/index.html").resolve().as_uri() + "?v=104"

MEASURE = """() => {
  const svg = document.querySelector('#map');
  const r = svg.getBoundingClientRect();
  const vb = svg.viewBox.baseVal;
  // viewBox -> screen scale
  const s = Math.min(r.width / vb.width, r.height / vb.height);
  const cs = (el, prop) => parseFloat(getComputedStyle(el)[prop]);
  const country = svg.querySelector('#countries path');
  const route = svg.querySelector('path.searoute');
  const dotCore = svg.querySelector('.stop-dot .dot-core');
  const dotHalo = svg.querySelector('.stop-dot .dot-halo');
  // vector-effect: computed stroke-width is already in screen px;
  // check the attribute value equals computed (no viewBox scaling)
  return {
    vbW: vb.width,
    scale: s,
    countryStroke: cs(country, 'strokeWidth'),
    routeStroke: cs(route, 'strokeWidth'),
    dotCoreW: cs(dotCore, 'strokeWidth'),
    dotHaloW: cs(dotHalo, 'strokeWidth'),
    countryVE: getComputedStyle(country).vectorEffect,
    dotVE: getComputedStyle(dotCore).vectorEffect,
    nDots: svg.querySelectorAll('.stop-dot').length,
    dotHit: (() => {
      // clicking the dot must still work: elementFromPoint at the dot
      const el = dotCore.ownerSVGElement;
      const b = dotCore.getBoundingClientRect();
      const hit = document.elementFromPoint(b.left + b.width / 2, b.top + b.height / 2);
      return hit ? (hit.closest('.stop-dot') ? 'dot' : hit.tagName || 'x') : 'none';
    })(),
  };
}"""

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(2500)
    pg.select_option("#lesson-select", "lessons/magellan/voyage.json")
    pg.wait_for_timeout(4000)
    out = {"zoom1": pg.evaluate(MEASURE)}
    for factor, label in [(1.2, "zoom1.2"), (1.2, "zoom1.44"), (2.0, "zoom2.9")]:
        pg.mouse.move(700, 450)
        pg.mouse.wheel(0, -400)  # wheel up = zoom in
        pg.wait_for_timeout(500)
        out[label] = pg.evaluate(MEASURE)
    out["errors"] = errs
    pg.screenshot(path="/tmp/zoomtest.png")
    b.close()

print(json.dumps(out, indent=1))
