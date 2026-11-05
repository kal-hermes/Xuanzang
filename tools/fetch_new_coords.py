#!/usr/bin/env python3
"""Fetch exact P625 for the new stop QIDs."""
import json, time, urllib.request, urllib.parse

UA = {"User-Agent": "xuanzang-lesson-gen/1.0"}
QIDS = ["Q108155", "Q156093", "Q176767", "Q863683", "Q324394", "Q2594448",
        "Q9213", "Q825673", "Q36796", "Q212332", "Q200119", "Q979927"]

url = ("https://www.wikidata.org/w/api.php?action=wbgetentities&ids="
       + "|".join(QIDS) + "&props=labels|claims&languages=en&format=json")
req = urllib.request.Request(url, headers=UA)
with urllib.request.urlopen(req, timeout=30) as r:
    data = json.load(r)
for qid, ent in data.get("entities", {}).items():
    label = ent.get("labels", {}).get("en", {}).get("value", "")
    for snak in ent.get("claims", {}).get("P625", []):
        v = snak.get("mainsnak", {}).get("datavalue", {}).get("value")
        if v:
            print(f'{qid:9s} [lon {v["longitude"]!r}, lat {v["latitude"]!r}]  {label}')
            break
