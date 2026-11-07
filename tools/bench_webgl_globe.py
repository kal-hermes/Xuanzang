#!/usr/bin/env python
"""A/B benchmark: SVG globe vs experimental WebGL texture globe.

Drives a remote (CDP) Chrome on the host's real GPU. For each renderer
mode it loads the app (globe projection, Xuanzang journey), patches
AtlasMap._reproject with a wall-clock wrapper, performs an identical
scripted drag (trusted CDP mouse events), and reports:

  - frames:            rAF callbacks fired during the drag
  - reproject_ms:      mean / p95 / max per-call cost of _reproject
  - long_tasks / 50ms: frames slower than 50 ms
  - drag_wall_ms:      total wall time of the scripted drag
  - dots_after:        sanity check that the overlay kept tracking

Usage:
  uv run --with playwright python tools/bench_webgl_globe.py \
      --cdp http://10.255.255.254:9223 --url http://127.0.0.1:8931/index.html \
      [--frames 90] [--out tools/scratch/bench-webgl-globe.json]
"""
import argparse
import json
import statistics
import time

from playwright.sync_api import sync_playwright

INSTRUMENT = r"""
(() => {
  const M = window.AtlasMap;
  const orig = M._reproject.bind(M);
  window.__perf = { calls: [], raf: [], drag: null };
  M._reproject = function (...a) {
    const t0 = performance.now();
    const r = orig(...a);
    window.__perf.calls.push(performance.now() - t0);
    return r;
  };
  const oRaf = window.requestAnimationFrame.bind(window);
  window.__oRaf = oRaf;
  let last = null;
  window.requestAnimationFrame = (cb) => oRaf((t) => {
    if (last !== null && window.__perf.drag) window.__perf.raf.push(t - last);
    last = t;
    cb(t);
  });
})();
"""

RUN_DRAG = r"""
(async (steps) => {
  const M = window.AtlasMap;
  window.__perf.calls = [];
  window.__perf.raf = [];
  window.__perf.drag = true;
  const t0 = performance.now();
  const svg = document.getElementById("map");
  const r = svg.getBoundingClientRect();
  const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
  const oRaf = window.__oRaf;
  svg.dispatchEvent(new PointerEvent("pointerdown", { bubbles: true, cancelable: true,
    pointerId: 5, pointerType: "mouse", isPrimary: true, button: 0, buttons: 1,
    clientX: cx, clientY: cy }));
  for (let i = 1; i <= steps; i++) {
    svg.dispatchEvent(new PointerEvent("pointermove", { bubbles: true, cancelable: true,
      pointerId: 5, pointerType: "mouse", isPrimary: true, button: 0, buttons: 1,
      clientX: cx + i * 9, clientY: cy + Math.sin(i / 3) * 6 }));
    await new Promise((res) => oRaf(res));   // pace like a real pointer stream
  }
  svg.dispatchEvent(new PointerEvent("pointerup", { bubbles: true, cancelable: true,
    pointerId: 5, pointerType: "mouse", isPrimary: true, button: 0, buttons: 0,
    clientX: cx + steps * 9, clientY: cy + Math.sin(steps / 3) * 6 }));
  // include the drag-end full reprojection in the measurement window
  await new Promise((res) => oRaf(() => oRaf(res)));
  window.__perf.drag = false;
  return { wall: performance.now() - t0,
           dots: document.querySelectorAll("#map .stop-dot").length };
})
"""


def pct(values, q):
    if not values:
        return 0.0
    s = sorted(values)
    return s[min(len(s) - 1, int(q * len(s)))]


def run_mode(pg, url, steps, webgl):
    sep = "&" if "?" in url else "?"
    pg.goto(f"{url}{sep}renderer={'webgl' if webgl else 'svg'}&v={int(time.time())}",
            wait_until="load")
    pg.wait_for_timeout(3000)
    pg.select_option("#lesson-select", "lessons/xuanzang/journey.json")
    pg.wait_for_timeout(4000)
    pg.select_option("#projection-select", "globe")
    pg.wait_for_timeout(9000 if webgl else 5000)  # texture bake head-start
    pg.evaluate(INSTRUMENT)
    res = pg.evaluate(RUN_DRAG, steps)
    perf = pg.evaluate("() => window.__perf")
    calls = perf["calls"]
    raf = perf["raf"]
    return {
        "mode": "webgl" if webgl else "svg",
        "frames": len(raf),
        "drag_wall_ms": round(res["wall"], 1),
        "reproject_calls": len(calls),
        "reproject_mean_ms": round(statistics.mean(calls), 2) if calls else 0,
        "reproject_p95_ms": round(pct(calls, 0.95), 2),
        "reproject_max_ms": round(max(calls), 2) if calls else 0,
        "raf_interval_mean_ms": round(statistics.mean(raf), 2) if raf else 0,
        "raf_interval_p95_ms": round(pct(raf, 0.95), 2),
        "long_tasks_over_50ms": sum(1 for v in raf if v > 50),
        "dots_after": res["dots"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cdp", default="http://10.255.255.254:9223")
    ap.add_argument("--url", default="http://127.0.0.1:8931/index.html")
    ap.add_argument("--local", action="store_true",
                    help="use container-local Chromium (SwiftShader) instead of CDP")
    ap.add_argument("--frames", type=int, default=90, help="pointermove steps per drag")
    ap.add_argument("--out", default="tools/scratch/bench-webgl-globe.json")
    args = ap.parse_args()

    with sync_playwright() as p:
        if args.local:
            b = p.chromium.launch(headless=True)
            ctx = b.new_context(viewport={"width": 1280, "height": 900})
        else:
            b = p.chromium.connect_over_cdp(args.cdp)
            ctx = b.contexts[0]
        results = []
        for webgl in (False, True):
            pg = ctx.new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            r = run_mode(pg, args.url, args.frames, webgl)
            r["js_errors"] = len(errs)
            results.append(r)
            print(json.dumps(r, indent=1))
            pg.close()
        b.close()

    svg = next(r for r in results if r["mode"] == "svg")
    wgl = next(r for r in results if r["mode"] == "webgl")
    summary = {
        "gpu": "host Chrome (CDP)",
        "svg": svg,
        "webgl": wgl,
        "speedup_reproject_mean": round(svg["reproject_mean_ms"] / max(wgl["reproject_mean_ms"], 0.01), 1),
        "speedup_drag_wall": round(svg["drag_wall_ms"] / max(wgl["drag_wall_ms"], 0.01), 1),
        "svg_frames_over_50ms": svg["long_tasks_over_50ms"],
        "webgl_frames_over_50ms": wgl["long_tasks_over_50ms"],
    }
    with open(args.out, "w") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
