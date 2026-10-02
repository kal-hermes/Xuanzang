#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parameterize prompt_sights with {traveler} in all 5 locales."""
src = open("js/i18n.js", encoding="utf-8").read()
subs = [
    ('"At {name} ({year}) — what did Xuanzang see or do there?"',
     '"At {name} ({year}) — what did {traveler} see or do there?"'),
    ("\"À {name} ({year}) — qu'a vu ou fait Xuanzang là-bas ?\"",
     "\"À {name} ({year}) — qu'a vu ou fait {traveler} là-bas ?\""),
    ('"在{name}（{year}年）——玄奘在这里的见闻或活动是什么？"',
     '"在{name}（{year}年）——{traveler}在这里的见闻或活动是什么？"'),
    ('"在{name}（{year}年）——玄奘在這裡的見聞或活動是什麼？"',
     '"在{name}（{year}年）——{traveler}在這裡的見聞或活動是什麼？"'),
    ('"{name}（{year}年）で——玄奘はそこで何を見し、何をした？"',
     '"{name}（{year}年）で——{traveler}はそこで何を見し、何をした？"'),
]
for old, new in subs:
    assert old in src, old
    src = src.replace(old, new)
open("js/i18n.js", "w", encoding="utf-8").write(src)
print("prompt_sights parameterized x5")
