#!/usr/bin/env python3
"""Offline sanity check for generated lessons: every lesson country must
exist in the enriched 10m topo (so it renders + is clickable) and have
names in all 4 locales."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
topo = json.loads((ROOT / "geo/countries-10m.json").read_text())
topo_iso3 = {g["properties"]["iso3"] for g in topo["objects"]["countries"]["geometries"]}
LOCALES = ["en-GB", "fr-CA", "zh-Hans", "zh-HK"]

fail = 0
for f in sorted((ROOT / "lessons/examples").glob("*-countries.json")):
    lesson = json.loads(f.read_text())
    n = len(lesson["countries"])
    problems = []
    for c in lesson["countries"]:
        if c["iso3"] not in topo_iso3:
            problems.append(f"{c['iso3']} NOT IN TOPO")
        for loc in LOCALES:
            if loc not in c["names"]:
                problems.append(f"{c['iso3']} missing {loc}")
    status = "OK" if not problems else "FAIL " + "; ".join(problems[:5])
    if problems:
        fail += 1
    print(f"{f.name:35s} {n:3d} countries  {status}")
raise SystemExit(1 if fail else 0)
