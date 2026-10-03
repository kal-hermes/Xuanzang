#!/usr/bin/env python3
"""The quantise regex has $2 but only one capture group — collapse the
number to its integer part + .1 decimal digit properly."""
from pathlib import Path

p = Path("js/map.js")
s = p.read_text(encoding="utf-8")
old = 'd.replace(/(-?\\d+)\\.\\d/g, "$1.$2")'
# keep one decimal digit: capture int and first decimal digit
new = 'd.replace(/(-?\\d+)(\\.\\d)\\d+/g, "$1$2")'
if old in s:
    s = s.replace(old, new)
    p.write_text(s, encoding="utf-8")
    print("patched:", new)
else:
    print("not found; current line:")
    for line in s.splitlines():
        if "d.replace" in line:
            print(line.strip())
