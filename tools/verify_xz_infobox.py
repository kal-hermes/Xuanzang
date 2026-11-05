#!/usr/bin/env python3
"""Spot-check infobox content for new stops via sidebar clicks (2 locales)."""
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = Path("/workspace/projects/history-geography-learning-app/index.html").resolve().as_uri() + "?v=235"

def grab(pg):
    return pg.evaluate("""() => {
      const name = document.querySelector('#info-name')?.textContent || '';
      const dds = [...document.querySelectorAll('#info-facts dd.narrative')].map(e => e.textContent);
      const rows = [...document.querySelectorAll('#info-facts dd')].filter(e => e.className !== 'narrative')
        .map(e => e.textContent);
      return {name, rows, narrN: dds.length, narr1: (dds[0] || '').slice(0, 70)};
    }""")

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1600, "height": 1000})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(3500)
    pg.select_option("#lesson-select", "lessons/xuanzang/journey.json")
    pg.wait_for_timeout(5000)
    for label in ["Lumbini", "Kanchipuram", "Pomilo", "Huoguo"]:
        pg.locator("#country-list-panel li", has_text=label).first.click()
        pg.wait_for_timeout(900)
        i = grab(pg)
        print(f"{label:12s} name={i['name']!r:30s} rows={i['rows'][:3]} paras={i['narrN']} :: {i['narr1']}")
    pg.select_option("#locale-select", "ja")
    pg.wait_for_timeout(2000)
    pg.locator("#country-list-panel li", has_text="ルンビニー").first.click()
    pg.wait_for_timeout(900)
    i = grab(pg)
    print(f"ja Lumbini    name={i['name']!r} paras={i['narrN']} :: {i['narr1']}")
    pg.select_option("#locale-select", "fr-CA")
    pg.wait_for_timeout(2000)
    pg.locator("#country-list-panel li", has_text="Kanchipuram").first.click()
    pg.wait_for_timeout(900)
    i = grab(pg)
    print(f"fr Kanchi     name={i['name']!r} paras={i['narrN']} :: {i['narr1']}")
    print("errors:", errs)
    b.close()
