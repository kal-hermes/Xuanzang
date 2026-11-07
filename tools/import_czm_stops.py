#!/usr/bin/env python3
"""Import annotated locations from yizhimomo/changzhengmap into the Long
March lesson. Reads the extracted czm_*.json files, filters to the five
marching forces, dedupes against existing lesson stops (same army within
25 km), and writes tools/changzhengmap_stops.json for gen_longmarch.py.
"""
import json
import re

LOCS = json.load(open("tools/scratch/czm_locations.json", encoding="utf-8"))
DATA = json.load(open("tools/scratch/czm_data.json", encoding="utf-8"))

FORCE_MAP = {
    "红一方面军": "red1",
    "红二方面军": "red2",
    "红二、六军团": "red2",
    "红四方面军": "red4",
    "红二十五军": "red25",
    "北上抗日先遣队": "xianqiandui",
}
SKIP_FORCES = {"陕北红军"}

EXISTING = json.load(open("lessons/longmarch/journey.json", encoding="utf-8"))

def dist(a, b):
    import math
    dx = (b[0] - a[0]) * 111 * math.cos(math.radians(a[1]))
    dy = (b[1] - a[1]) * 111
    return (dx * dx + dy * dy) ** 0.5

def date_key(s):
    if not s:
        return (9999, 12, 31)
    m = re.search(r"(\d{4})年", s)
    y = int(m.group(1)) if m else 9999
    mm = re.search(r"(\d{4})年(\d{1,2})月", s)
    mo = int(mm.group(2)) if mm else 12
    dd = re.search(r"月(\d{1,2})日", s)
    d = int(dd.group(1)) if dd else 15
    return (y, mo, d)

out = []
seen_names = set()
for idx, loc in enumerate(LOCS):
    det = DATA.get(loc["id"])
    if not det or not det.get("desc"):
        continue
    force = det.get("force", "")
    army = FORCE_MAP.get(force)
    if army is None:
        continue  # 陕北红军 / pre-march sites without a mapped force
    date = det.get("date", "")
    if date_key(date)[0] < 1934:
        continue  # pre-Long-March context sites (e.g. Jinggangshan 1927)
    coords = [loc["lng"], loc["lat"]]
    # dedupe against existing lesson stops (same army, within 25 km)
    dup = any(s["army"] == army and dist(coords, s["coords"]) < 25
              for s in EXISTING["stops"])
    if dup:
        continue
    # dedupe within import set (same name+army, e.g. repeated crossings)
    key = (army, det.get("title") or loc["name"])
    if key in seen_names:
        continue
    seen_names.add(key)
    out.append({
        "id": "czm_" + loc["id"],
        "army": army,
        "name_zh": det.get("title") or loc["name"],
        "type": det.get("type", ""),
        "date_zh": date,
        "present_zh": det.get("now", ""),
        "desc_zh": det["desc"],
        "quote_zh": det.get("quote", ""),
        "source_zh": det.get("source", ""),
        "seq": idx,
        "coords": coords,
    })

out.sort(key=lambda s: (s["army"], date_key(s["date_zh"]), s["seq"]))
json.dump(out, open("tools/changzhengmap_stops.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
from collections import Counter
print("imported:", len(out), Counter(s["army"] for s in out))
print("skipped dupes against existing stops + intra-set dupes; dateless/other-force entries excluded")
