#!/usr/bin/env python3
"""Offline sanity check for generated lessons: every lesson country must
exist in the enriched 10m topo (so it renders + is clickable) and have
names in all 4 locales."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
topo = json.loads((ROOT / "geo/countries-10m.json").read_text())
topo_iso3 = {g["properties"]["iso3"] for g in topo["objects"]["countries"]["geometries"]}
LOCALES = ["en-GB", "fr-CA", "zh-Hans", "zh-HK", "ja"]

fail = 0
lessons = sorted((ROOT / "lessons/examples").glob("*-countries.json"))
lessons += sorted((ROOT / "lessons").glob("*/journey.json"))
lessons += sorted((ROOT / "lessons").glob("*/voyage.json"))
for f in lessons:
    lesson = json.loads(f.read_text())
    n = len(lesson.get("countries", []))
    problems = []
    for c in lesson.get("countries", []):
        if c["iso3"] not in topo_iso3:
            problems.append(f"{c['iso3']} NOT IN TOPO")
        for loc in LOCALES:
            if loc not in c["names"]:
                problems.append(f"{c['iso3']} missing {loc}")
    if lesson.get("type") == "journey":
        for s in lesson.get("stops", []):
            if not s.get("coords") or len(s["coords"]) != 2:
                problems.append(f"stop {s.get('id')} bad coords")
            for locname in LOCALES:
                if locname not in (s.get("names") or {}):
                    problems.append(f"stop {s.get('id')} missing name {locname}")
            # voyage lessons may legitimately lack some narrative locales
            # until GLM translations land; require en-GB at minimum
            if "en-GB" not in (s.get("narrative") or {}):
                problems.append(f"stop {s.get('id')} missing en-GB narrative")
            if s.get("iso3") and s["iso3"] not in topo_iso3:
                problems.append(f"stop {s.get('id')} iso3 {s.get('iso3')} NOT IN TOPO")
        if not lesson.get("route_out"):
            problems.append("missing route_out")
        if not lesson.get("voyage") and not lesson.get("route_back"):
            problems.append("missing route_back")
    status = "OK" if not problems else "FAIL " + "; ".join(problems[:5])
    if problems:
        fail += 1
    print(f"{f.name:35s} {n:3d} countries  {status}")
raise SystemExit(1 if fail else 0)
