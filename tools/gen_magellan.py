# -*- coding: utf-8 -*-
"""Generate lessons/magellan/voyage.json (+ .js twin) — the
Magellan-Elcano circumnavigation (1519-1522), same lesson schema as the
Xuanzang journey, plus voyage:true (sea-route Bezier rendering) and
route waypoints offshore. Merges GLM translations (narratives per
locale, meta i18n, quiz sights/places) when present."""
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from magellan_data import STOPS  # noqa: E402
# Route from Albo's derrotero + whalesite KML; 12 waypoints that fell
# inside 10m land polygons were nudged offshore in-browser
# (tools/nudge_waypoints.py) -> tools/albo_route_fixed.json overrides.
from magellan_route_albo import ROUTE_OUT as _RO, ROUTE_BACK as _RB  # noqa: E402
import json as _json  # noqa: E402

_fx = ROOT / "tools" / "albo_route_fixed.json"
if _fx.exists():
    _d = _json.loads(_fx.read_text(encoding="utf-8"))
    ROUTE_OUT = _d["out"]
    ROUTE_BACK = _d["back"]
else:
    ROUTE_OUT, ROUTE_BACK = _RO, _RB


def _load(name):
    ns = {}
    exec((ROOT / "tools" / name).read_text(encoding="utf-8"), ns)
    return ns


def fetch_all_coords(qids):
    """One batched wbgetentities call (chunks of 40) -> {qid: [lon,lat]}."""
    out = {}
    allq = [q for q in qids if q]
    for i in range(0, len(allq), 40):
        chunk = allq[i:i + 40]
        url = ("https://www.wikidata.org/w/api.php?action=wbgetentities&format=json"
               "&props=claims&ids=" + "|".join(chunk))
        req = urllib.request.Request(url, headers={"User-Agent": "xuanzang-lesson/1.0"})
        for attempt in range(6):
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    ents = json.loads(r.read())["entities"]
                break
            except Exception as e:
                print("retry", e)
                time.sleep(5 * (attempt + 1))
        else:
            raise SystemExit("rate limited")
        for q in chunk:
            p625 = ents.get(q, {}).get("claims", {}).get("P625", [])
            if not p625:
                raise SystemExit(f"FAIL {q}: no P625")
            v = p625[0]["mainsnak"]["datavalue"]["value"]
            out[q] = [v["longitude"], v["latitude"]]
    return out


def main():
    meta_ns = _load("magellan_meta.py")
    PRESENT, WHEN, YEAR, NAMES = (meta_ns["PRESENT"], meta_ns["WHEN"],
                                  meta_ns["YEAR"], meta_ns["NAMES"])
    SIGHTS_SRC, QUIZ_PLACES = meta_ns["SIGHTS"], meta_ns["QUIZ_PLACES"]

    NARRATIVE_RICH = _load("magellan_text_en.py")["NARRATIVE_RICH"]

    # localized narratives (per-locale py files, GLM-generated)
    NARR = {}
    for loc_ in ["fr-CA", "zh-Hans", "zh-HK", "ja"]:
        p = ROOT / "tools" / f"magellan_text_{loc_}.py"
        if p.exists():
            NARR[loc_] = _load(f"magellan_text_{loc_}.py")["NARRATIVE_RICH"]
        else:
            print(f"  (no magellan_text_{loc_}.py; narrative stays English)",
                  file=sys.stderr)
    # localized when/present
    META_I18N = {}
    mp = ROOT / "tools" / "magellan_meta_i18n.json"
    if mp.exists():
        META_I18N = json.loads(mp.read_text(encoding="utf-8"))
    else:
        print("  (no magellan_meta_i18n.json; when/present stay English)",
              file=sys.stderr)
    # quiz sights + place names
    sights_i18n = None
    sp = ROOT / "tools" / "magellan_i18n.json"
    if sp.exists():
        sights_i18n = json.loads(sp.read_text(encoding="utf-8"))
    else:
        print("  (no magellan_i18n.json; quiz content stays English)",
              file=sys.stderr)

    print("Geocoding stops from Wikidata…")
    coords = fetch_all_coords({q for q, _, _ in STOPS.values()})

    stops = []
    for sid, (qid, tokens, iso3) in STOPS.items():
        c = coords.get(qid) if qid else None
        if sid == "pacific_crossing":
            c = [-108.0, -21.0]  # on Albo's track: early Jan 1521 (22S)
        stop = {
            "id": sid,
            "coords": c,
            "year": YEAR[sid],
            "when": {"en-GB": WHEN[sid]},
            "present": {"en-GB": PRESENT[sid]["en"]},
            "iso3": iso3,
            "names": dict(NAMES[sid]),
            "narrative": {"en-GB": NARRATIVE_RICH[sid]},
        }
        # merge localized when/present/narrative
        for loc_ in ["fr-CA", "zh-Hans", "zh-HK", "ja"]:
            if loc_ in META_I18N:
                if sid in META_I18N[loc_].get("when", {}):
                    stop["when"][loc_] = META_I18N[loc_]["when"][sid]
                if sid in META_I18N[loc_].get("present", {}):
                    stop["present"][loc_] = META_I18N[loc_]["present"][sid]
            if loc_ in NARR and sid in NARR[loc_]:
                stop["narrative"][loc_] = NARR[loc_][sid]
            sn = (sights_i18n or {}).get("stop_names", {}).get(loc_, {})
            if sid in sn:
                stop["names"][loc_] = sn[sid]
        stops.append(stop)
        print(f"  {sid:18s} {c}  «{NAMES[sid]['en-GB']}»")

    lesson = {
        "id": "magellan",
        "type": "journey",
        "voyage": True,
        "title": {
            "en-GB": "Magellan–Elcano Circumnavigation (1519–1522)",
            "zh-Hans": "麦哲伦—埃尔卡诺环球航行（1519–1522）",
            "ja": "マゼラン＝エルカノ世界周航（1519–1522）",
        },
        "traveler": {
            "en-GB": "Magellan's fleet",
            "fr-CA": "la flotte de Magellan",
            "zh-Hans": "麦哲伦船队",
            "zh-HK": "麥哲倫船隊",
            "ja": "マゼランの船隊",
        },
        "stops": stops,
        "route_out": ROUTE_OUT,
        "route_back": ROUTE_BACK,
        "view": {"lon0": -170, "lat0": -60, "lon1": 190, "lat1": 84},
        "quizSights": {},
        "quizPlaces": [],
    }
    if sights_i18n:
        for sid, fact in SIGHTS_SRC.items():
            entry = {"en-GB": fact}
            for loc_ in ["fr-CA", "zh-Hans", "zh-HK", "ja"]:
                if (loc_ in sights_i18n.get("sights", {})
                        and sid in sights_i18n["sights"][loc_]):
                    entry[loc_] = sights_i18n["sights"][loc_][sid]
            lesson["quizSights"][sid] = entry
        lesson["quizPlaces"] = [
            {
                "id": pid,
                "names": {
                    "en-GB": info["names"]["en-GB"],
                    "zh-Hans": info["names"].get("zh-Hans", info["names"]["en-GB"]),
                    "zh-HK": info["names"].get("zh-Hans", info["names"]["en-GB"]),
                    "fr-CA": (sights_i18n.get("place_names", {}).get("fr-CA", {})
                              .get(pid, info["names"]["en-GB"])),
                    "ja": (sights_i18n.get("place_names", {}).get("ja", {})
                           .get(pid, info["names"]["en-GB"])),
                },
                "year": info["year"],
            }
            for pid, info in QUIZ_PLACES.items()
        ]

    out = ROOT / "lessons/magellan/voyage.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(lesson, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print(f"wrote {out} ({len(stops)} stops, "
          f"{len(ROUTE_OUT)}+{len(ROUTE_BACK)} route pts)")
    js = (f'window.ATLAS_LESSONS["lessons/magellan/voyage.json"] = '
          + json.dumps(lesson, ensure_ascii=False) + ";\n")
    (out.parent / "voyage.js").write_text(
        "window.ATLAS_LESSONS = window.ATLAS_LESSONS || {};\n" + js,
        encoding="utf-8")
    print("wrote lessons/magellan/voyage.js")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
