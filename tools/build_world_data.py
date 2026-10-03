#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build geo/world-data.js (the file:// embedded world topology) from
the UNSIMPLIFIED countries-10m.json, keeping the quantized TopoJSON
encoding as-is."""
import json
from pathlib import Path

src = json.loads(Path("geo/countries-10m.json").read_text(encoding="utf-8"))
out = "window.ATLAS_WORLD_DATA = " + json.dumps(src, separators=(",", ":"))
Path("geo/world-data.js").write_text(out, encoding="utf-8")
print(f"wrote geo/world-data.js ({len(out):,} bytes)")
