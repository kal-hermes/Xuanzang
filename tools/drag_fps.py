#!/usr/bin/env python3
"""Globe drag frame-rate test: measure rAF-callback fps while dragging
via CDP input events, and long-frame count."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = Path("/workspace/projects/history-geography-learning-app/index.html").resolve().as_uri() + "?v=137"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1600, "height": 1000})
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(6000)
    pg.select_option("#lesson-select", "lessons/magellan/voyage.json")
    pg.wait_for_timeout(4000)
    pg.select_option("#projection-select", "globe")
    pg.wait_for_timeout(3000)
    # instrument: count _reproject(quick) calls and total time
    pg.evaluate("""(() => {
      window.__fps = {frames: 0, t0: performance.now(), rep: 0, repMs: 0, longFrames: 0};
      const orig = window.AtlasMap._reproject.bind(window.AtlasMap);
      window.AtlasMap._reproject = function (q) {
        const t = performance.now();
        orig(q);
        const dt = performance.now() - t;
        window.__fps.rep++; window.__fps.repMs += dt;
        if (dt > 33) window.__fps.longFrames++;
      };
    })()""")
    pg.mouse.move(800, 500)
    pg.mouse.down()
    t0 = time.time()
    for i in range(60):
        pg.mouse.move(800 - i * 4, 500 - i * 2, steps=2)
    dur = time.time() - t0
    pg.mouse.up()
    pg.wait_for_timeout(800)
    st = pg.evaluate("window.__fps")
    print(f"drag duration: {dur:.2f}s, reprojects: {st['rep']}, "
          f"avg reproject: {st['repMs']/max(1,st['rep']):.1f}ms, "
          f"long frames (>33ms): {st['longFrames']}")
    b.close()
