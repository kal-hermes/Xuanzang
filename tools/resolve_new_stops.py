#!/usr/bin/env python3
"""Resolve QIDs for new Xuanzang stops via wbsearchentities + P625."""
import json, time, urllib.request, urllib.parse, sys

UA = {"User-Agent": "xuanzang-lesson-gen/1.0 (kal-hermes repo)"}

CANDIDATES = {
    "huoguo":        ["Kunduz"],
    "taxila":        ["Taxila"],
    "bodhgaya":      ["Bodh Gaya"],
    "vulture_peak":  ["Griddhakuta", "Vulture Peak Rajgir"],
    "sarnath":       ["Sarnath"],
    "sravasti":      ["Shravasti", "Sravasti"],
    "lumbini":       ["Lumbini"],
    "kushinagar":    ["Kushinagar"],
    "vaishali":      ["Vaishali"],
    "hiranyaparvata":["Munger"],
    "kanchipuram":   ["Kanchipuram"],
    "ujjain":        ["Ujjain"],
    "tashkurgan":    ["Tashkurgan", "Taxkurgan"],
}

def api(params):
    url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

out = {}
for key, terms in CANDIDATES.items():
    for term in terms:
        d = api({"action": "wbsearchentities", "search": term, "language": "en",
                 "limit": 5, "format": "json"})
        results = d.get("search", [])
        print(f"== {key}  ('{term}')")
        for r in results[:5]:
            print(f"   {r['id']:10s} {r.get('label','')!r:32s} {r.get('description','')!r}")
        if results:
            out[key] = [(r["id"], r.get("label", ""), r.get("description", "")) for r in results[:5]]
        time.sleep(0.8)
        if results:
            break

json.dump(out, open("tools/scratch/xz_new_qid_search.json", "w"), ensure_ascii=False, indent=1)
