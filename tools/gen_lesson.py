#!/usr/bin/env python3
"""Generate 'countries' lessons (schema v0) from vendored datasets.

Sources:
  - geo/countries-10m.json     — world-atlas TopoJSON (enriched with iso3)
  - tools/mledoze-countries.json — region, population, capital, demonym
  - tools/cldr-*.json         — localized territory display names

Output: lessons/examples/<id>.json

Notes:
  - A country is included only if its centroid (mledoze latlng) falls
    inside the lesson's view box — guarantees every lesson country
    renders (and is clickable) in flat projections. This mainly prunes
    Pacific islands east of the antimeridian from the Oceania lesson.
  - The Americas are split into two lessons via mledoze 'subregion'.
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

VIEWS = {
    "europe": {"lon0": -26, "lat0": 34, "lon1": 46, "lat1": 72},
    "asia": {"lon0": 25, "lat0": -12, "lon1": 150, "lat1": 60},
    "africa": {"lon0": -20, "lat0": -38, "lon1": 53, "lat1": 38},
    "north-america": {"lon0": -170, "lat0": 5, "lon1": -50, "lat1": 85},
    "south-america": {"lon0": -84, "lat0": -57, "lon1": -33, "lat1": 14},
    "oceania": {"lon0": 95, "lat0": -50, "lon1": 180, "lat1": 15},
}

TITLES = {
    "europe": {"en-GB": "Countries of Europe",
               "fr-CA": "Les pays d'Europe",
               "zh-Hans": "欧洲国家", "zh-HK": "歐洲國家"},
    "asia": {"en-GB": "Countries of Asia",
             "fr-CA": "Les pays d'Asie",
             "zh-Hans": "亚洲国家", "zh-HK": "亞洲國家"},
    "africa": {"en-GB": "Countries of Africa",
               "fr-CA": "Les pays d'Afrique",
               "zh-Hans": "非洲国家", "zh-HK": "非洲國家"},
    "north-america": {"en-GB": "Countries of North America",
                      "fr-CA": "Les pays d'Amérique du Nord",
                      "zh-Hans": "北美洲国家", "zh-HK": "北美洲國家"},
    "south-america": {"en-GB": "Countries of South America",
                      "fr-CA": "Les pays d'Amérique du Sud",
                      "zh-Hans": "南美洲国家", "zh-HK": "南美洲國家"},
    "oceania": {"en-GB": "Countries of Oceania",
                "fr-CA": "Les pays d'Océanie",
                "zh-Hans": "大洋洲国家", "zh-HK": "大洋洲國家"},
}

# mledoze region -> lesson; Americas split by subregion
REGION_TO_LESSON = {
    "Europe": "europe",
    "Asia": "asia",
    "Africa": "africa",
    "Oceania": "oceania",
}
SUBREGION_TO_LESSON = {
    "Northern America": "north-america",
    "Central America": "north-america",
    "Caribbean": "north-america",
    "South America": "south-america",
}

def in_view(view, latlng):
    if not latlng or len(latlng) != 2:
        return False
    lat, lon = latlng
    return (view["lon0"] <= lon <= view["lon1"]
            and view["lat0"] <= lat <= view["lat1"])

# Countries whose mledoze centroid falls outside their natural lesson's
# view: pinned explicitly so they stay in their proper lesson.
PLACEMENTS = {
    "RUS": "europe",   # centroid (61.5N, 105E) is in Siberia; Russia belongs in the Europe lesson
}

# mledoze cca3 codes that differ from the world-atlas/ISO codes we use
CODE_MAP = {
    "UNK": "XKX",      # Kosovo: mledoze uses the outdated UNK user-assigned code
}

def main():
    cldr = load_cldr()
    countries = json.loads((ROOT / "tools/mledoze-countries.json").read_text(encoding="utf-8"))
    topo = json.loads((ROOT / "geo/countries-10m.json").read_text(encoding="utf-8"))
    topo_iso3 = {g["properties"]["iso3"] for g in topo["objects"]["countries"]["geometries"]}

    lessons = {lid: {"id": f"{lid}-countries", "title": TITLES[lid],
                     "type": "countries", "view": VIEWS[lid], "countries": []}
               for lid in VIEWS}

    missing_name, out_of_view, not_in_topo = [], [], []
    for c in countries:
        region = c.get("region")
        lesson_id = REGION_TO_LESSON.get(region)
        if region == "Americas":
            lesson_id = SUBREGION_TO_LESSON.get(c.get("subregion"))
        iso3 = CODE_MAP.get(c["cca3"], c["cca3"])
        if iso3 in PLACEMENTS:
            lesson_id = PLACEMENTS[iso3]
        if not lesson_id:
            continue
        if iso3 not in topo_iso3:
            not_in_topo.append((iso3, c["name"], lesson_id))
            continue
        pinned = iso3 in PLACEMENTS
        if not pinned and not in_view(VIEWS[lesson_id], c.get("latlng")):
            out_of_view.append((iso3, c["name"], lesson_id))
            continue
        names = {}
        for locale in LOCALES:
            n = cldr.get(locale, {}).get(c["cca2"])
            if n:
                names[locale] = n
        if len(names) < len(LOCALES):
            missing_name.append((iso3, c["name"], lesson_id))
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
        entry["facts"] = {k: v for k, v in entry["facts"].items() if v}
        lessons[lesson_id]["countries"].append(entry)

    for lesson_id, lesson in lessons.items():
        out = ROOT / "lessons/examples" / f"{lesson['id']}.json"
        lesson["countries"].sort(key=lambda e: e["names"]["en-GB"])
        out.write_text(json.dumps(lesson, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"{out.relative_to(ROOT)}: {len(lesson['countries'])} countries")

    for label, items in [("not in topo (skipped)", not_in_topo),
                         ("centroid outside view (skipped)", out_of_view),
                         ("missing localized names (skipped)", missing_name)]:
        if items:
            print(f"{label}: {items}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
