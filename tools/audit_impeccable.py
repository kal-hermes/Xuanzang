#!/usr/bin/env python3
"""Impeccable audit — mechanical evidence for the Xuanzang SPA.
Measures contrast, focus indicators, tap targets, overflow, keyboard
tabbability, ARIA/semantics, reduced-motion, animation properties."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = Path("/workspace/projects/history-geography-learning-app/index.html").resolve().as_uri() + "?v=236audit"
OUT = {}

def lum(c):
    def f(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])

def ratio(fg, bg):
    l1, l2 = lum(fg), lum(bg)
    if l1 < l2: l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)

def parse(c):
    import re
    m = re.findall(r"[\d.]+", c)
    if len(m) >= 3:
        return [float(m[0]), float(m[1]), float(m[2])]
    return None

def bg_of(pg, el):
    return pg.evaluate("""(el) => {
      let n = el;
      while (n) {
        const bg = getComputedStyle(n).backgroundColor;
        if (bg && !bg.includes('0, 0, 0, 0') && bg !== 'transparent') return bg;
        n = n.parentElement;
      }
      return 'rgb(13, 20, 32)';
    }""", el)

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1280, "height": 900})
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(4000)

    # ---------- 1. contrast of text ----------
    texts = pg.evaluate("""() => {
      const out = [];
      const sel = 'h1, h2, h3, th, label, p, dd, dt, li, option, button, a, .narrative';
      for (const el of document.querySelectorAll(sel)) {
        const cs = getComputedStyle(el);
        if (cs.visibility === 'hidden' || cs.display === 'none') continue;
        const txt = (el.textContent || '').trim();
        if (!txt) continue;
        out.push({tag: el.tagName.toLowerCase(), cls: el.className && String(el.className).slice(0,40),
                  color: cs.color, size: cs.fontSize, weight: cs.fontWeight, text: txt.slice(0,30)});
        if (out.length > 120) break;
      }
      return out;
    }""")
    fails, checked = [], 0
    seen = set()
    for t in texts:
        key = (t["tag"], t["cls"], t["color"], t["size"])
        if key in seen: continue
        seen.add(key)
        el = pg.locator(f'{t["tag"]}' + (f'.{t["cls"].split()[0]}' if t["cls"] else "")).first
        try:
            bg = parse(bg_of(pg, el.element_handle()))
        except Exception:
            continue
        fg = parse(t["color"])
        if not fg or not bg: continue
        checked += 1
        r = ratio(fg, bg)
        large = float(t["size"].replace("px", "")) >= 24 or (float(t["size"].replace("px","")) >= 18.66 and int(t["weight"]) >= 700)
        need = 3.0 if large else 4.5
        if r < need:
            fails.append({**t, "ratio": round(r, 2), "need": need})
    OUT["contrast"] = {"checked": checked, "fails": fails}

    # ---------- 2. focus indicators ----------
    focus = pg.evaluate("""() => {
      const res = [];
      const els = [...document.querySelectorAll('select, button, a, [tabindex]')];
      for (const el of els.slice(0, 40)) {
        el.focus();
        const cs = getComputedStyle(el);
        res.push({tag: el.tagName, id: el.id || el.textContent.trim().slice(0,20),
                  outline: cs.outlineStyle + ' ' + cs.outlineWidth,
                  shadow: cs.boxShadow !== 'none',
                  tabindex: el.tabIndex});
      }
      return res;
    }""")
    nofocus = [f for f in focus if f["outline"].startswith("none") and not f["shadow"]]
    OUT["focus"] = {"total": len(focus), "no_indicator": nofocus}

    # ---------- 3. tap targets ----------
    taps = pg.evaluate("""() => {
      const res = [];
      for (const el of document.querySelectorAll('select, button, a')) {
        const r = el.getBoundingClientRect();
        if (r.width === 0) continue;
        res.push({tag: el.tagName, id: el.id || el.textContent.trim().slice(0,16),
                  w: Math.round(r.width), h: Math.round(r.height)});
      }
      return res;
    }""")
    small = [t for t in taps if t["w"] < 24 or t["h"] < 24]
    OUT["tap_targets"] = {"total": len(taps), "under24": small, "smallest": sorted(taps, key=lambda t: t["w"]*t["h"])[:5]}

    # ---------- 4. tab order / keyboard ----------
    tab = pg.evaluate("""() => {
      const t = [...document.querySelectorAll('select, button, a, [tabindex]:not([tabindex="-1"])')];
      return {tabbables: t.length, svgDots: document.querySelectorAll('.stop-dot').length,
              dotsFocusable: document.querySelectorAll('.stop-dot[tabindex], .stop-dot[role]').length};
    }""")
    OUT["keyboard"] = tab

    # ---------- 5. semantics / ARIA ----------
    sem = pg.evaluate("""() => {
      const sels = document.querySelectorAll('select');
      const unlabeled = [...sels].filter(s => !s.labels || !s.labels.length).map(s => s.id);
      const svg = document.querySelectorAll('svg');
      const svgNoName = [...svg].filter(s => !s.querySelector('title') && !s.getAttribute('aria-label') && !s.getAttribute('aria-hidden')).length;
      return {landmarks: [...document.querySelectorAll('header, nav, main, aside, footer')].map(e => e.tagName),
              selectsWithoutLabel: unlabeled,
              svgs: svg.length, svgsUnlabeled: svgNoName,
              h1s: document.querySelectorAll('h1').length, h2s: document.querySelectorAll('h2').length,
              divButtons: [...document.querySelectorAll('div')].filter(d => d.onclick && !d.getAttribute('role')).length};
    }""")
    OUT["semantics"] = sem

    # ---------- 6. overflow at widths ----------
    for w in (1280, 500, 390):
        pg.set_viewport_size({"width": w, "height": 900})
        pg.wait_for_timeout(600)
        ov = pg.evaluate("""() => ({
          docOverflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
          bodyOverflow: document.body.scrollWidth - document.body.clientWidth})""")
        OUT[f"overflow_{w}"] = ov

    # ---------- 7. reduced motion + animation properties ----------
    css = Path("/workspace/projects/history-geography-learning-app/css/app.css").read_text()
    OUT["reduced_motion_media_query"] = "prefers-reduced-motion" in css
    anim = pg.evaluate("""() => {
      const animated = [];
      for (const sheet of document.styleSheets) {
        try { for (const r of sheet.cssRules) {
          if (r.type === CSSRule.KEYFRAMES_RULE) animated.push(r.name);
        }} catch(e) {}
      }
      return animated;
    }""")
    OUT["keyframes"] = anim

    # ---------- 8. theming: hard-coded colors ----------
    import re as _re
    hexes = _re.findall(r"#[0-9a-fA-F]{3,8}\\b", css)
    OUT["theming"] = {"css_vars_defined": len(_re.findall(r"--[a-z-]+\s*:", css)),
                      "css_vars_used": len(_re.findall(r"var\(--", css)),
                      "hardcoded_hex": len(hexes)}

    b.close()

OUT["flat_type"] = {"body": 15.2, "h2": 16, "h1": 19.2, "note": "detector rendered finding"}
print(json.dumps(OUT, indent=1))
Path("tools/scratch/audit_results.json").write_text(json.dumps(OUT, indent=1))
