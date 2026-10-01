#!/usr/bin/env python3
"""One-time: add properties.iso3 to a world-atlas TopoJSON file using
tools/iso3166.csv (UN M49 numeric code -> alpha-3).

Usage: enrich_topojson.py [filename]   (default: countries-110m.json)
Idempotent: rewrites the file with iso3 added; safe to re-run.
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "tools" / "iso3166.csv"

def main():
    fname = sys.argv[1] if len(sys.argv) > 1 else "countries-110m.json"
    topo_path = ROOT / "geo" / fname

    code_to_iso3 = {}
    with open(CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            num = row["country-code"].strip()
            if num:
                code_to_iso3[num] = row["alpha-3"].strip()

    topo = json.loads(topo_path.read_text(encoding="utf-8"))
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
        "Vatican": "VAT",
        "Tuvalu": "TUV",
        "Gibraltar": "GIB",
    }
    for g in geoms:
        name = g["properties"].get("name", "")
        if not g["properties"].get("iso3") and name in overrides:
            g["properties"]["iso3"] = overrides[name]
            mapped += 1
            unmapped = [(n, m) for n, m in unmapped if m != name]

    # Special territories with no ISO country code / no lesson value:
    # drop them so they never render (even as context).
    drop_names = {
        "Akrotiri", "Dhekelia", "Cyprus U.N. Buffer Zone",
        "Baikonur", "USNB Guantanamo Bay", "U.S. Minor Outlying Is.",
        "Bajo Nuevo Bank", "Serranilla Bank", "Scarborough Reef",
        "Spratly Is.", "Coral Sea Is.", "Clipperton I.",
        "Siachen Glacier", "Indian Ocean Ter.",
        "Ashmore and Cartier Is.",   # Australian external territory, not a separate feature
    }
    before = len(geoms)
    geoms[:] = [g for g in geoms if g["properties"].get("name") not in drop_names]
    dropped = before - len(geoms)

    topo_path.write_text(json.dumps(topo, separators=(",", ":")), encoding="utf-8")
    print(f"{fname}: mapped {mapped}/{len(geoms)} to iso3, dropped {dropped} special territories")
    if unmapped:
        print("still unmapped:", unmapped)
    return 0

if __name__ == "__main__":
    sys.exit(main())
