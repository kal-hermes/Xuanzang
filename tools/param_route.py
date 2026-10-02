#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parameterize prompt_route with {traveler} (en/fr had 'he')."""
src = open("js/i18n.js", encoding="utf-8").read()
subs = [
    ('"From {name} ({year}) — where did he go next, and when?"',
     '"From {name} ({year}) — where did {traveler} go next, and when?"'),
    ('"De {name} ({year}) — où est-il allé ensuite, et quand ?"',
     '"De {name} ({year}) — où {traveler} est-{traveler} allé ensuite, et quand ?"'),
]
for old, new in subs:
    assert old in src, old
    src = src.replace(old, new)
open("js/i18n.js", "w", encoding="utf-8").write(src)
print("prompt_route parameterized")
