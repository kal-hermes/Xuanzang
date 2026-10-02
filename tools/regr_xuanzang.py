#!/usr/bin/env python3
"""Xuanzang regression after the routeYearVariants change."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = Path("/workspace/projects/history-geography-learning-app/index.html").resolve().as_uri() + "?v=101"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(2500)
    pg.select_option("#lesson-select", "lessons/xuanzang/journey.json")
    pg.wait_for_timeout(1500)
    out = {}
    pg.select_option("#mode-select", "route")
    pg.wait_for_timeout(1500)
    out["prompt"] = pg.locator("#prompt-text").inner_text()
    out["choices"] = pg.evaluate("""() => [...document.querySelectorAll('#choices button')].map(b => ({
      place: b.querySelector('.quiz-place')?.textContent,
      year: b.querySelector('.quiz-year')?.textContent,
      correct: b.dataset.correct === '1'}))""")
    ci = next(i for i, b in enumerate(
        pg.locator("#choices button").all()) if b.get_attribute("data-correct") == "1")
    pg.locator("#choices button").nth(ci).click()
    pg.wait_for_timeout(1600)
    out["dots_after_1"] = pg.locator("#map .stop-dot").count()
    # sights: traveler should say Xuanzang
    pg.select_option("#mode-select", "sights")
    pg.wait_for_timeout(1500)
    out["sights_prompt"] = pg.locator("#prompt-text").inner_text()
    out["errors"] = errs
    b.close()
print(json.dumps(out, ensure_ascii=False, indent=1))
