#!/usr/bin/env python3
"""Verify harden: keyboard access to sidebar entries, stop dots,
popover; localized svg aria-label; focus styles render."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = Path("/workspace/projects/history-geography-learning-app/index.html").resolve().as_uri() + "?v=243harden"
OUT = {}

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1280, "height": 900})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(4000)

    # --- learn mode: tab to sidebar entries ---
    pg.evaluate("() => document.getElementById('lesson-select').focus()")
    n_tab = 0
    reached_li = None
    for _ in range(12):
        pg.keyboard.press("Tab")
        n_tab += 1
        tag = pg.evaluate("() => document.activeElement.tagName + '#' + document.activeElement.id")
        if document_li := pg.evaluate("() => document.activeElement.id === 'country-list' ? 'ul' : (document.activeElement.closest && document.activeElement.closest('#country-list') ? 'li' : null)"):
            reached_li = tag
            break
    OUT["learn_tab_to_li"] = {"tabs": n_tab, "at": reached_li}

    # focus a li and press Enter -> infobox opens
    pg.evaluate("() => { const li = document.querySelector('#country-list li'); li.focus(); }")
    pg.keyboard.press("Enter")
    pg.wait_for_timeout(800)
    OUT["learn_enter_opens_infobox"] = pg.evaluate(
        "() => !document.getElementById('info-panel').hidden && (document.getElementById('info-name').textContent || '')")

    # li role/tabindex
    OUT["li_attrs"] = pg.evaluate("""() => {
        const li = document.querySelector('#country-list li');
        return {tabindex: li.tabIndex, role: li.getAttribute('role')};
    }""")

    # --- journey lesson ---
    pg.select_option("#lesson-select", "lessons/xuanzang/journey.json")
    pg.wait_for_timeout(5000)
    OUT["journey_li_focusable"] = pg.evaluate(
        "() => document.querySelectorAll('#country-list li[tabindex=\"0\"]').length")
    pg.evaluate("() => { document.querySelector('#country-list li').focus(); }")
    pg.keyboard.press("Enter")
    pg.wait_for_timeout(800)
    OUT["journey_enter_selects"] = pg.evaluate(
        "() => !document.getElementById('info-panel').hidden")

    # stop dots focusable?
    OUT["dots_total"] = pg.evaluate("() => document.querySelectorAll('#map .stop-dot').length")
    OUT["dots_focusable"] = pg.evaluate(
        "() => document.querySelectorAll('#map .stop-dot[tabindex=\"0\"]').length")
    OUT["dot_aria"] = pg.evaluate(
        "() => document.querySelector('#map .stop-dot') && document.querySelector('#map .stop-dot').getAttribute('aria-label')")

    # Enter on a single-visit dot selects it
    pg.evaluate("""() => {
        const dots = [...document.querySelectorAll('#map .stop-dot')]
            .filter(d => d.dataset.visits.split(',').length === 1);
        dots[Math.min(3, dots.length - 1)].focus();
    }""")
    pg.keyboard.press("Enter")
    pg.wait_for_timeout(800)
    OUT["dot_enter_selects"] = pg.evaluate(
        "() => !document.getElementById('info-panel').hidden")

    # multi-visit dot: Enter opens popover, focus inside, Enter picks, Esc closes
    multi = pg.evaluate("""() => {
        const d = [...document.querySelectorAll('#map .stop-dot')]
            .find(d => d.dataset.visits.split(',').length > 1);
        if (!d) return null;
        return {visits: d.dataset.visits, label: d.getAttribute('aria-label')};
    }""")
    OUT["multi_dot"] = multi
    if multi:
        pg.evaluate("() => [...document.querySelectorAll('#map .stop-dot')].find(d => d.dataset.visits.split(',').length > 1).focus()")
        pg.keyboard.press("Enter")
        pg.wait_for_timeout(500)
        OUT["popover_open_focus"] = pg.evaluate(
            "() => { const pop = document.getElementById('stop-popover'); return pop ? {items: pop.querySelectorAll('.stop-pop-item').length, focused: document.activeElement.className} : null; }")
        pg.keyboard.press("Enter")
        pg.wait_for_timeout(700)
        OUT["popover_enter_picks"] = pg.evaluate(
            "() => !document.getElementById('stop-popover') && !document.getElementById('info-panel').hidden")
        # esc path
        pg.evaluate("() => [...document.querySelectorAll('#map .stop-dot')].find(d => d.dataset.visits.split(',').length > 1).focus()")
        pg.keyboard.press("Enter")
        pg.wait_for_timeout(400)
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(400)
        OUT["popover_esc"] = pg.evaluate(
            "() => ({closed: !document.getElementById('stop-popover'), refocused: document.activeElement.classList.contains('stop-dot')})")

    # --- localized svg aria-label ---
    pg.select_option("#locale-select", "ja")
    pg.wait_for_timeout(1500)
    OUT["svg_aria_ja"] = pg.evaluate(
        "() => document.getElementById('map').getAttribute('aria-label')")
    pg.select_option("#locale-select", "en-GB")
    pg.wait_for_timeout(1000)
    OUT["svg_aria_en"] = pg.evaluate(
        "() => document.getElementById('map').getAttribute('aria-label')")

    # --- focus ring screenshot ---
    pg.evaluate("() => { document.querySelector('#country-list li').focus(); }")
    pg.wait_for_timeout(300)
    pg.screenshot(path="tools/scratch/harden-focus-li.png",
                  clip={"x": 0, "y": 60, "width": 340, "height": 420})
    pg.evaluate("() => { document.querySelector('#map .stop-dot').focus(); }")
    pg.wait_for_timeout(400)
    pg.screenshot(path="tools/scratch/harden-focus-dot.png",
                  clip={"x": 380, "y": 60, "width": 900, "height": 840})

    OUT["js_errors"] = errs
    b.close()

print(json.dumps(OUT, indent=1, ensure_ascii=False))
Path("tools/scratch/harden_results.json").write_text(
    json.dumps(OUT, indent=1, ensure_ascii=False), encoding="utf-8")
