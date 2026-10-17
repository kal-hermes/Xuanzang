#!/usr/bin/env python3
"""Resolve remaining QIDs (with 429 backoff)."""
import json, time, urllib.request, urllib.parse

UA = {"User-Agent": "xuanzang-lesson-gen/1.0 (kal-hermes repo)"}

CANDIDATES = {
    "vulture_peak":  ["Gridhakuta", "Gridhakuta hill", "Rajgir"],
    "vaishali":      ["Vaishali ancient city", "Vaishali Bihar"],
    "hiranyaparvata":["Munger"],
    "kanchipuram":   ["Kanchipuram"],
    "ujjain":        ["Ujjain"],
    "tashkurgan":    ["Tashkurgan", "Taxkurgan"],
}

def api(params, tries=6):
    url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    for t in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429 and t < tries - 1:
                time.sleep(10 * (t + 1)); continue
            raise
    return {}

for key, terms in CANDIDATES.items():
    done = False
    for term in terms:
        d = api({"action": "wbsearchentities", "search": term, "language": "en",
                 "limit": 6, "format": "json"})
        results = d.get("search", [])
        print(f"== {key}  ('{term}')")
        for r in results[:6]:
            print(f"   {r['id']:10s} {r.get('label','')!r:34s} {r.get('description','')!r}")
        time.sleep(3)
        if results:
            done = True
            break
    if not done:
        print(f"!! {key}: no results")
