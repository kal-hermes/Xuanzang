#!/usr/bin/env python3
"""Full verification of the Magellan lesson: registration, render,
sea-route curves, quiz modes, all 5 locales, file:// protocol."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = Path("/workspace/projects/history-geography-learning-app/index.html").resolve().as_uri()

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1600, "height": 1000})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL + "?v=101", wait_until="load")
    pg.wait_for_timeout(2500)

    # lesson registered + selectable
    out = {}
    opt = pg.locator("#lesson-select option[value='lessons/magellan/voyage.json']")
    out["registered"] = opt.count() == 1
    pg.select_option("#lesson-select", "lessons/magellan/voyage.json")
    pg.wait_for_timeout(4500)

    out["dots"] = pg.locator("#map .stop-dot").count()
    out["searoutes"] = pg.evaluate(
        "document.querySelectorAll('#map path.searoute').length")
    # mode visibility: journey modes only
    out["modes"] = pg.evaluate("""() => {
      const vis = {};
      for (const o of document.querySelector('#mode-select').options)
        vis[o.value] = !o.hidden;
      return vis;
    }""")

    # sidebar shows 20 stops
    out["sidebar_stops"] = pg.locator("#country-list li").count()

    # land-crossing check (viewBox-bounded)
    out["land"] = pg.evaluate("""() => {
      const svg = document.querySelector('#map');
      const routes = [...svg.querySelectorAll('path.searoute')];
      const countries = [...svg.querySelectorAll('#countries path')];
      const svgPt = svg.createSVGPoint();
      const vb = svg.viewBox.baseVal;
      let land = 0, sea = 0;
      for (const r of routes) {
        const len = r.getTotalLength();
        for (let d = 0; d <= len; d += 15) {
          const pt = r.getPointAtLength(d);
          if (pt.x < vb.x || pt.x > vb.x + vb.width ||
              pt.y < vb.y || pt.y > vb.y + vb.height) continue;
          svgPt.x = pt.x; svgPt.y = pt.y;
          for (const c of countries) {
            if (c.isPointInFill(svgPt)) { land++; break; }
          }
          sea++;
        }
      }
      return {samples: sea, landHits: land};
    }""")

    # stop info: verify via lesson data (UI info panel covered by the
    # Xuanzang lesson tests; here check the data the panel would show)
    out["stop0_narrative_paras"] = pg.evaluate(
        "() => window.ATLAS_LESSONS['lessons/magellan/voyage.json'].stops[0].narrative['en-GB'].length")
    out["stop0_when"] = pg.evaluate(
        "() => window.ATLAS_LESSONS['lessons/magellan/voyage.json'].stops[0].when['en-GB']")

    # route quiz: first question (depart Sanlúcar 1519 -> next Tenerife)
    pg.select_option("#mode-select", "route")
    pg.wait_for_timeout(1500)
    out["route_prompt"] = pg.locator("#prompt-text").inner_text()
    out["route_choices"] = pg.evaluate("""() => [...document.querySelectorAll('#choices button')].map(b => ({
      place: b.querySelector('.quiz-place')?.textContent,
      year: b.querySelector('.quiz-year')?.textContent,
      correct: b.dataset.correct === '1'}))""")
    ci = next(i for i, b in enumerate(
        pg.locator("#choices button").all()) if b.get_attribute("data-correct") == "1")
    pg.locator("#choices button").nth(ci).click()
    pg.wait_for_timeout(600)
    out["route_after_correct"] = pg.locator("#choices button").nth(ci).get_attribute("class")
    out["score"] = pg.locator("#score-display").inner_text()

    # sights quiz
    pg.select_option("#mode-select", "sights")
    pg.wait_for_timeout(1500)
    out["sights_prompt"] = pg.locator("#prompt-text").inner_text()[:70]
    out["sights_choice0"] = pg.locator("#choices button").first.inner_text()[:60]

    # all 5 locales render prompt + sidebar
    pg.select_option("#mode-select", "route")
    pg.wait_for_timeout(1200)
    loc_names = []
    for loc in ["en-GB", "fr-CA", "zh-Hans", "zh-HK", "ja"]:
        pg.select_option("#locale-select", loc)
        pg.wait_for_timeout(600)
        loc_names.append(pg.locator("#prompt-text").inner_text()[:34])
    out["locales"] = loc_names

    # narrative localized: check zh-Hans narrative exists for stop 1
    pg.select_option("#mode-select", "learn")
    pg.wait_for_timeout(1200)
    out["narrative_zh"] = pg.evaluate("""() => {
      const L = window.ATLAS_LESSONS['lessons/magellan/voyage.json'];
      const s = L.stops[0];
      return {zh: !!s.narrative['zh-Hans'], fr: !!s.narrative['fr-CA'],
              ja: !!s.narrative['ja'], zhHK: !!s.narrative['zh-HK']};
    }""")

    out["js_errors"] = errs
    b.close()

print(json.dumps(out, ensure_ascii=False, indent=1))
