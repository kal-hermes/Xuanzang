#!/usr/bin/env python3
"""Generate 'countries' lessons (schema v0) from vendored datasets.

Sources (downloaded into tools/):
  - geo/countries-110m.json   — world-atlas TopoJSON (enriched with iso3)
  - tools/mledoze-countries.json — region, population, capital, demonym
  - tools/cldr-*.json         — localized territory display names

Output: lessons/examples/<id>.json
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LOCALES = {
    "en-GB": "tools/cldr-en.json",
    "fr-CA": "tools/cldr-fr-CA.json",
    "zh-Hans": "tools/cldr-zh-Hans.json",
    "zh-HK": "tools/cldr-zh-Hant-HK.json",
}

# CLDR territory keys are alpha-2 or numeric ("056"); we key by alpha-2.
def load_cldr():
    out = {}
    for locale, path in LOCALES.items():
        data = json.loads((ROOT / path).read_text(encoding="utf-8"))
        main_key = list(data["main"].keys())[0]
        terr = data["main"][main_key]["localeDisplayNames"]["territories"]
        out[locale] = terr
    return out

def cldr_name(terr, locale, cca2):
    d = terr[locale]
    return d.get(cca2)

VIEWS = {
    "europe": {"lon0": -26, "lat0": 34, "lon1": 46, "lat1": 72},
    "asia": {"lon0": 25, "lat0": -12, "lon1": 150, "lat1": 60},
}

REGION_TO_LESSON = {
    "Europe": "europe",
    "Asia": "asia",
}

# Territories in mledoze 'region' Europe/Asia that are NOT in the 110m
# world-atlas geometries or that we deliberately skip (dependencies).
SKIP_ISO3 = set()

def main():
    cldr = load_cldr()
    countries = json.loads((ROOT / "tools/mledoze-countries.json").read_text(encoding="utf-8"))
    topo = json.loads((ROOT / "geo/countries-110m.json").read_text(encoding="utf-8"))
    topo_iso3 = {g["properties"]["iso3"] for g in topo["objects"]["countries"]["geometries"]}

    lessons = {"europe": {"id": "europe-countries",
                          "title": {"en-GB": "Countries of Europe",
                                    "fr-CA": "Les pays d'Europe",
                                    "zh-Hans": "欧洲国家",
                                    "zh-HK": "歐洲國家"},
                          "type": "countries", "view": VIEWS["europe"], "countries": []},
               "asia": {"id": "asia-countries",
                        "title": {"en-GB": "Countries of Asia",
                                  "fr-CA": "Les pays d'Asie",
                                  "zh-Hans": "亚洲国家",
                                  "zh-HK": "亞洲國家"},
                        "type": "countries", "view": VIEWS["asia"], "countries": []}}

    missing_name = []
    for c in countries:
        region = c.get("region")
        lesson_id = REGION_TO_LESSON.get(region)
        if not lesson_id:
            continue
        iso3 = c["cca3"]
        if iso3 in SKIP_ISO3 or iso3 not in topo_iso3:
            continue
        names = {}
        for locale in LOCALES:
            n = cldr_name(cldr, locale, c["cca2"])
            if n:
                names[locale] = n
        if len(names) < len(LOCALES):
            missing_name.append((iso3, c["name"], sorted(set(LOCALES) - set(names))))
            continue
        capital = ""
        if c.get("capital"):
            capital = c["capital"][0] if isinstance(c["capital"], list) else c["capital"]
        entry = {
            "iso3": iso3,
            "names": names,
            "facts": {
                "population": c.get("population"),
                "capital": capital or None,
                "demonym": c.get("demonym") or None,
            },
        }
        # drop null fact values for compactness
        entry["facts"] = {k: v for k, v in entry["facts"].items() if v}
        lessons[lesson_id]["countries"].append(entry)

    for lesson_id, lesson in lessons.items():
        out = ROOT / "lessons/examples" / f"{lesson['id']}.json"
        lesson["countries"].sort(key=lambda e: e["names"]["en-GB"])
        out.write_text(json.dumps(lesson, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"{out.relative_to(ROOT)}: {len(lesson['countries'])} countries")

    if missing_name:
        print("skipped (missing localized names):", missing_name)
    return 0

if __name__ == "__main__":
    sys.exit(main())
