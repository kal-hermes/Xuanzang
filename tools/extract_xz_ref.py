#!/usr/bin/env python3
"""Extract STOPS (y/era/lat/lng/gu/jin/t) from the reference map."""
import re, json

src = open("tools/scratch/xz-ref/玄奘行迹图.html", encoding="utf-8").read()
m = re.search(r"const STOPS = \[(.*?)\n\];", src, re.S)
body = m.group(1)
out = []
for line in body.split("\n"):
    mm = re.match(r"\s*\{\s*y:\s*(\d+),\s*era:\s*'([^']*)',\s*lat:\s*(-?[\d.]+),\s*lng:\s*(-?[\d.]+),\s*gu:\s*'([^']*)',\s*jin:\s*'([^']*)'", line)
    if mm:
        y, era, lat, lng, gu, jin = mm.groups()
        t = re.search(r"\bt:\s*'([^']*)'", line)
        out.append({"y": int(y), "era": era, "lat": float(lat), "lng": float(lng),
                    "gu": gu, "jin": jin, "t": t.group(1) if t else ""})
print(len(out), "stops")
json.dump(out, open("tools/scratch/xz_ref_stops.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
for s in out:
    print(f'{s["y"]} {s["era"]:14s} {s["gu"]:22s} {s["lat"]:7.2f},{s["lng"]:8.2f}  {s["jin"]}  | {s["t"][:28]}')
