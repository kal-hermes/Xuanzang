#!/usr/bin/env python3
"""Verify animate: reduced-motion path vs normal motion.
Emulates prefers-reduced-motion via Playwright's reduced_motion option."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = Path("/workspace/projects/history-geography-learning-app/index.html").resolve().as_uri() + "?v=245anim"

def load_journey(pg):
    pg.select_option("#lesson-select", "lessons/xuanzang/journey.json")
    pg.wait_for_timeout(5000)
    pg.select_option("#journey-view-select", "step")
    pg.wait_for_timeout(500)
    # step to stop 2 so a segment exists
    pg.click("#journey-next")
    pg.wait_for_timeout(300)
    pg.click("#journey-next")
    pg.wait_for_timeout(1200)

def probe(pg):
    out = {}
    out["focused_pulse_anim"] = pg.evaluate("""() => {
        const el = document.querySelector('#map .stop-dot.focused .dot-core');
        return el ? getComputedStyle(el).animationName : 'no-focused-dot';
    }""")
    out["segments"] = pg.evaluate(
        "() => document.querySelectorAll('#map path.segment').length")
    out["last_seg_dash"] = pg.evaluate("""() => {
        const segs = [...document.querySelectorAll('#map path.segment')];
        const s = segs[segs.length - 1];
        return s ? {arr: s.style.strokeDasharray, off: s.style.strokeDashoffset,
                    trans: s.style.transition} : null;
    }""")
    return out

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    results = {}
    for mode in ("normal", "reduce"):
        ctx = b.new_context(viewport={"width": 1280, "height": 900},
                            reduced_motion=("reduce" if mode == "reduce" else "no-preference"))
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(URL, wait_until="load")
        pg.wait_for_timeout(4000)
        load_journey(pg)
        r = probe(pg)
        # mid-animation sampling in normal mode: the new segment should
        # still be transitioning right after the click
        if mode == "normal":
            pg.click("#journey-next")
            pg.wait_for_timeout(120)
            r["mid_draw_transition"] = pg.evaluate("""() => {
                const segs = [...document.querySelectorAll('#map path.segment')];
                const s = segs[segs.length - 1];
                return s ? s.style.transition || '(none yet)' : 'no seg';
            }""")
            pg.wait_for_timeout(1000)
        # learn mode target dot (locate) check
        r["js_errors"] = errs
        results[mode] = r
        ctx.close()
    b.close()

print(json.dumps(results, indent=1))
Path("tools/scratch/animate_results.json").write_text(json.dumps(results, indent=1))
