#!/usr/bin/env python3
"""Emit script-tag-loadable .js versions of all fetched data, so the
SPA works from file:// (fetch() of local files is blocked there).

Outputs:
  geo/world-data.js        <- window.ATLAS_WORLD_DATA
  data/qid-map.js          <- window.ATLAS_QID_MAP
  data/capital-coords.js   <- window.ATLAS_CAPITAL_COORDS
  lessons/examples/<id>-countries.js  <- window.ATLAS_LESSONS["<file>.json"]
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def dump_js(path, var, data, extra_prefix=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        if extra_prefix:
            f.write(extra_prefix + "\n")
        f.write("window." + var + " = ")
        json.dump(data, f, separators=(",", ":"), ensure_ascii=False)
        f.write(";\n")


def main():
    # world topology
    topo = json.loads((ROOT / "geo/countries-10m-simple.json").read_text())
    dump_js(ROOT / "geo/world-data.js", "ATLAS_WORLD_DATA", topo)

    # iso3 -> wikidata QID
    qid = json.loads((ROOT / "data/iso3-to-qid.json").read_text())
    dump_js(ROOT / "data/qid-map.js", "ATLAS_QID_MAP", qid)

    # capital coordinates
    coords = json.loads((ROOT / "data/capital-coords.json").read_text())
    dump_js(ROOT / "data/capital-coords.js", "ATLAS_CAPITAL_COORDS", coords)

    # lessons — keyed by the exact value LESSONS uses in app.js
    n = 0
    for p in sorted((ROOT / "lessons/examples").glob("*-countries.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        dump_js(p.with_suffix(".js"),
                f'ATLAS_LESSONS["lessons/examples/{p.name}"]', d,
                extra_prefix="window.ATLAS_LESSONS = window.ATLAS_LESSONS || {};")
        n += 1
    print(f"wrote world-data.js, qid-map.js, capital-coords.js, {n} lesson .js files")


if __name__ == "__main__":
    main()
