#!/usr/bin/env python3
"""One-time: add properties.iso3 to geo/countries-110m.json using
tools/iso3166.csv (UN M49 numeric code -> alpha-3).

Idempotent: rewrites the file with iso3 added; safe to re-run.
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOPO = ROOT / "geo" / "countries-110m.json"
CSV = ROOT / "tools" / "iso3166.csv"

def main():
    code_to_iso3 = {}
    with open(CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            num = row["country-code"].strip()
            if num:
                code_to_iso3[num] = row["alpha-3"].strip()

    topo = json.loads(TOPO.read_text(encoding="utf-8"))
    geoms = topo["objects"]["countries"]["geometries"]

    mapped, unmapped = 0, []
    for g in geoms:
        gid = str(g.get("id", "")).strip()
        iso3 = code_to_iso3.get(gid)
        if iso3:
            g["properties"]["iso3"] = iso3
            mapped += 1
        else:
            unmapped.append((gid, g["properties"].get("name")))

    # Manual overrides for entries world-atlas splits differently than ISO.
    overrides = {
        "Western Sahara": "ESH",
        "Somaliland": "SOM",      # not ISO; map to Somalia for learning purposes
        "N. Cyprus": "CYP",       # map to Cyprus
        "Kosovo": "XKX",          # user-assigned code
        "Taiwan": "TWN",
        "Palestine": "PSE",
        "eSwatini": "SWZ",
    }
    for g in geoms:
        name = g["properties"].get("name", "")
        if not g["properties"].get("iso3") and name in overrides:
            g["properties"]["iso3"] = overrides[name]
            mapped += 1
            unmapped = [(n, m) for n, m in unmapped if m != name]

    TOPO.write_text(json.dumps(topo, separators=(",", ":")), encoding="utf-8")
    print(f"mapped {mapped}/{len(geoms)} geometries to iso3")
    if unmapped:
        print("still unmapped:", unmapped)
    return 0

if __name__ == "__main__":
    sys.exit(main())
