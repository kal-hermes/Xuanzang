#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Add journey-quiz i18n keys (mode_route, mode_sights, prompt_route,
prompt_sights, wrong_route, sights_answer) to all 5 locales in js/i18n.js."""
import re

SRC = "js/i18n.js"
src = open(SRC, encoding="utf-8").read()

KEYS = {
    "en-GB": {
        "mode_route": "Guess the route",
        "mode_sights": "Guess the sights",
        "prompt_route": "From {name} ({year}) — where did he go next, and when?",
        "prompt_sights": "At {name} ({year}) — what did Xuanzang see or do there?",
        "wrong_route": "Not quite — watch the map to see the right answer.",
        "sights_answer": "In fact: {fact}",
    },
    "fr-CA": {
        "mode_route": "Devinez l'itinéraire",
        "mode_sights": "Devinez les observations",
        "prompt_route": "De {name} ({year}) — où est-il allé ensuite, et quand ?",
        "prompt_sights": "À {name} ({year}) — qu'a vu ou fait Xuanzang là-bas ?",
        "wrong_route": "Pas tout à fait — observez la carte pour voir la bonne réponse.",
        "sights_answer": "En réalité : {fact}",
    },
    "zh-Hans": {
        "mode_route": "猜路线",
        "mode_sights": "猜见闻",
        "prompt_route": "从{name}（{year}年）出发——下一站是哪里，何时到达？",
        "prompt_sights": "在{name}（{year}年）——玄奘在这里的见闻或活动是什么？",
        "wrong_route": "不太对——看地图上的正确答案。",
        "sights_answer": "事实上：{fact}",
    },
    "zh-HK": {
        "mode_route": "猜路線",
        "mode_sights": "猜見聞",
        "prompt_route": "從{name}（{year}年）出發——下一站是哪裡，何時到達？",
        "prompt_sights": "在{name}（{year}年）——玄奘在這裡的見聞或活動是什麼？",
        "wrong_route": "不太對——看地圖上的正確答案。",
        "sights_answer": "事實上：{fact}",
    },
    "ja": {
        "mode_route": "順路を当てる",
        "mode_sights": "見聞を当てる",
        "prompt_route": "{name}（{year}年）から——次はどこへ、いつ向かった？",
        "prompt_sights": "{name}（{year}年）で——玄奘はそこで何を見し、何をした？",
        "wrong_route": "違います——地図の正解を確認してください。",
        "sights_answer": "実際には：{fact}",
    },
}

anchor = re.compile(r'^(\s*)"?stops"?\s*:', re.M)
for loc_, kvs in KEYS.items():
    m = re.search(r'"%s": \{([\s\S]*?)\n    \},' % re.escape(loc_), src)
    assert m, loc_
    block = m.group(1)
    assert '"mode_route"' not in block, f"{loc_} already has keys"
    am = anchor.search(block)
    assert am, loc_
    add = "\n".join(f'{am.group(1)}"{k}": "{v}",' for k, v in kvs.items())
    nb = block[:am.end()] + "\n" + add + block[am.end():]
    src = src[:m.start(1)] + nb + src[m.end(1):]

open(SRC, "w", encoding="utf-8").write(src)
print("journey-quiz i18n keys added to all 5 locales")
