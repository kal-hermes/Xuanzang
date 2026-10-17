#!/usr/bin/env python3
"""Render the completed Xuanzang route; check stops, sidebar, locales."""
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = Path("/workspace/projects/history-geography-learning-app/index.html").resolve().as_uri() + "?v=234"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1600, "height": 1000})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(3500)
    pg.select_option("#lesson-select", "lessons/xuanzang/journey.json")
    pg.wait_for_timeout(5000)
    n = pg.evaluate("() => document.querySelectorAll('#map .stop-dot').length")
    side = pg.evaluate("() => document.querySelectorAll('#sidebar li, #stop-list li').length")
    print("stop dots:", n, "| sidebar entries:", side, "| errors:", errs)
    pg.screenshot(path="tools/scratch/xz-full-route.png")
    # click a new stop (kanchipuram is far south, distinctive) via its dot?
    # simpler: verify a new stop infobox via step mode navigation is heavy;
    # use the sidebar if present
    b.close()
