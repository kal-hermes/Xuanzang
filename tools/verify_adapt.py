#!/usr/bin/env python3
"""Verify the adapt changes: touch drag on globe + flat, mouse drag
regression, overflow at 3 widths."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = Path("/workspace/projects/history-geography-learning-app/index.html").resolve().as_uri() + "?v=240adapt"
OUT = {}

def pointer_seq(pg, x0, y0, x1, y1, ptype="touch", steps=12):
    pg.evaluate("""([x0, y0, x1, y1, ptype, steps]) => {
        const svg = document.getElementById("map");
        const r = svg.getBoundingClientRect();
        const px = x0 * r.width, py = y0 * r.height;
        const qx = x1 * r.width, qy = y1 * r.height;
        const opts = (x, y, type, extra={}) => ({
            bubbles: true, cancelable: true, composed: true, pointerId: 7,
            pointerType: type, isPrimary: true, button: 0, buttons: type === "pointerup" ? 0 : 1,
            clientX: x + r.left, clientY: y + r.top, ...extra});
        svg.dispatchEvent(new PointerEvent("pointerdown", opts(px, py, ptype)));
        for (let i = 1; i <= steps; i++) {
            svg.dispatchEvent(new PointerEvent("pointermove", opts(
                px + (qx - px) * i / steps, py + (qy - py) * i / steps, ptype)));
        }
        svg.dispatchEvent(new PointerEvent("pointerup", opts(qx, qy, ptype)));
    }""", [x0, y0, x1, y1, ptype, steps])

def rot(pg):
    return pg.evaluate("() => { const m = window.ATLAS_MAP_DEBUG_ROTATE; return m ? m() : null; }")

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1280, "height": 900}, has_touch=True)
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(4000)

    pg.evaluate("""() => {
        // expose the projection rotate for drag assertions
        const app = window.atlas || window.ATLAS;
        const svg = document.getElementById("map");
        window.__rot = () => {
            const p = svg && svg.__projection;
            return p && p.rotate ? p.rotate() : null;
        };
    }""")

    # globe default view? The app boots with globe (view select). Determine current view.
    OUT["view_default"] = pg.evaluate("() => document.getElementById('journey-view-select') ? 'has' : 'none'")
    view = pg.evaluate("() => (document.querySelector('#view-select, #journey-view-select')||{}).value || null")
    OUT["view_value"] = view

    # Find the projection via d3 instance stored anywhere? Use behavior instead:
    # record a visual pixel signature before/after drag.
    def sig():
        return pg.evaluate("""() => {
            const svg = document.getElementById('map');
            const p = svg.querySelector('#countries path, path.country');
            const g = svg.querySelector('#countries');
            return {d0: p ? (p.getAttribute('d') || '').slice(0, 80) : '',
                    pan: g ? (g.getAttribute('transform') || '') : '',
                    n: svg.querySelectorAll('path').length};
        }""")

    before = sig()
    pointer_seq(pg, 0.7, 0.5, 0.4, 0.5, ptype="touch")
    pg.wait_for_timeout(900)
    after_touch = sig()
    OUT["globe_touch_drag"] = {"before": before, "after": after_touch,
                               "changed": before != after_touch}

    # mouse drag regression (flat projection: switch to equirectangular)
    pg.select_option("#projection-select", "equirectangular")
    pg.wait_for_timeout(1500)
    flat_before = sig()
    pointer_seq(pg, 0.5, 0.5, 0.7, 0.5, ptype="mouse")
    pg.wait_for_timeout(900)
    flat_after_mouse = sig()
    OUT["flat_mouse_pan"] = {"changed": flat_before != flat_after_mouse}
    pointer_seq(pg, 0.5, 0.5, 0.7, 0.5, ptype="touch")
    pg.wait_for_timeout(900)
    OUT["flat_touch_pan"] = {"changed": flat_after_mouse != sig()}

    # overflow at widths
    for w in (1280, 500, 390):
        pg.set_viewport_size({"width": w, "height": 900})
        pg.wait_for_timeout(500)
        OUT[f"overflow_{w}"] = pg.evaluate(
            "() => document.documentElement.scrollWidth - document.documentElement.clientWidth")

    pg.set_viewport_size({"width": 1280, "height": 900})
    pg.wait_for_timeout(800)
    pg.screenshot(path="tools/scratch/adapt-1280.png")
    pg.set_viewport_size({"width": 390, "height": 844})
    pg.wait_for_timeout(800)
    pg.screenshot(path="tools/scratch/adapt-390.png")

    # lesson select not clipped at 390
    pg.wait_for_timeout(300)
    OUT["lesson_select_390"] = pg.evaluate("""() => {
        const r = document.getElementById('lesson-select').getBoundingClientRect();
        return {right: Math.round(r.right), vw: window.innerWidth, chevron_room: Math.round(window.innerWidth - r.right)};
    }""")
    OUT["js_errors"] = errs
    b.close()

print(json.dumps(OUT, indent=1))
Path("tools/scratch/adapt_results.json").write_text(json.dumps(OUT, indent=1))
