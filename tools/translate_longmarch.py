#!/usr/bin/env python3
"""Translate the Long March lesson narratives + quizSights from zh-Hans into
en-GB, fr-CA, zh-HK, ja via GLM. One stop (3 paragraphs) per request; one
quizSights batch (35 one-liners) per request. Writes results back into
lessons/longmarch/journey.json and regenerates the journey.js twin.
Resumable: keeps a checkpoint file in tools/scratch/longmarch_i18n.json.
"""
import json
import os
import re
import time
import urllib.request

BASE = "http://10.255.255.254:9001/v1"   # Bifrost router (WSL2 host via socat)
KEY = ""                                  # no credentials needed
MODEL = os.environ.get("LLM_MODEL", "GLM/glm-5.3-flash")
LESSON = "lessons/longmarch/journey.json"
CKPT = "tools/scratch/longmarch_i18n.json"

LOCALES = {
    "en-GB": "British English (en-GB).",
    "fr-CA": "French as used in Canada (fr-CA). Use proper French typographic conventions.",
    "zh-HK": "Traditional Chinese (zh-Hant) as used in Hong Kong. Use Hong Kong vocabulary and traditional characters.",
    "ja": "Japanese (ja). Natural scholarly Japanese.",
}

PROMPT = """You are translating historical-geographical educational content about the Central Red Army's Long March (1934-1935) across China, from the Jiangxi soviet to northern Shaanxi.

Translate each numbered paragraph into {lang_desc}

Rules:
- Faithful, fluent, readable prose for a general audience; keep historical terms accurate (place names: Zunyi, Luding Bridge, Chishui River, Songpan grasslands etc. rendered as customary in the target language).
- Keep the paragraph count and order exactly: {n} paragraphs in, {n} paragraphs out.
- Return a JSON array of EXACTLY {n} strings — one per paragraph. Do NOT merge them.
- Do not add commentary, headers, or numbering. Output ONLY the JSON array.

Paragraphs:
{payload}
"""

def call_glm(prompt, max_tokens=8000):
    # reasoning models can burn the whole budget on reasoning (finish_reason
    # "length", empty content): scale the budget up and retry
    for _ in range(3):
        body = json.dumps({
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.2,
        }).encode()
        req = urllib.request.Request(
            BASE + "/chat/completions", data=body,
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as r:
            choice = json.load(r)["choices"][0]
            content = choice["message"].get("content")
            if content and content.strip():
                return content
            max_tokens *= 3
            print(f"    empty content (finish={choice.get('finish_reason')}), retrying with max_tokens={max_tokens}")
    return ""

def extract_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
    start = text.find("[")
    end = text.rfind("]")
    if start >= 0 and end > start:
        return json.loads(text[start:end + 1])
    return json.loads(text)

def translate_batch(paras, lang_desc):
    payload = "\n".join(f"{i+1}. {p}" for i, p in enumerate(paras))
    prompt = PROMPT.format(lang_desc=lang_desc, n=len(paras), payload=payload)
    for attempt in range(3):
        try:
            out = extract_json(call_glm(prompt))
            if isinstance(out, list) and len(out) == len(paras) and all(isinstance(x, str) and x.strip() for x in out):
                return out
        except Exception as e:
            print(f"    attempt {attempt+1} failed: {str(e)[:80]}")
        time.sleep(3)
    raise RuntimeError("translation failed after retries")

def main():
    lesson = json.load(open(LESSON, encoding="utf-8"))
    ckpt = {}
    if os.path.exists(CKPT):
        ckpt = json.load(open(CKPT, encoding="utf-8"))
    for loc, desc in LOCALES.items():
        for s in lesson["stops"]:
            key = f"narr:{loc}:{s['id']}"
            if loc in s["narrative"]:
                continue
            if key in ckpt:
                s["narrative"][loc] = ckpt[key]
                continue
            print(f"[{loc}] {s['id']} …")
            out = translate_batch(s["narrative"]["zh-Hans"], desc)
            s["narrative"][loc] = out
            ckpt[key] = out
            json.dump(ckpt, open(CKPT, "w", encoding="utf-8"), ensure_ascii=False)
            time.sleep(1)
        # quizSights: batch 35 one-liners in one request
        key = f"sights:{loc}"
        qs = lesson["quizSights"]
        if all(loc in v for v in qs.values()):
            continue
        if key in ckpt:
            for sid, v in ckpt[key].items():
                qs[sid][loc] = v
        else:
            print(f"[{loc}] quizSights batch …")
            ids = list(qs.keys())
            paras = [qs[sid]["zh-Hans"] for sid in ids]
            out = translate_batch(paras, desc)
            for sid, v in zip(ids, out):
                qs[sid][loc] = v
                ckpt.setdefault(key, {})[sid] = v
            json.dump(ckpt, open(CKPT, "w", encoding="utf-8"), ensure_ascii=False)
        time.sleep(1)
    json.dump(lesson, open(LESSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open("lessons/longmarch/journey.js", "w", encoding="utf-8") as f:
        f.write('window.ATLAS_LESSONS = window.ATLAS_LESSONS || {};\n')
        f.write('window.ATLAS_LESSONS["lessons/longmarch/journey.json"] = ')
        f.write(json.dumps(lesson, ensure_ascii=False))
        f.write(';\n')
    missing = [(s["id"], loc) for s in lesson["stops"] for loc in LOCALES if loc not in s["narrative"]]
    print("done. missing:", missing if missing else "none")

if __name__ == "__main__":
    main()
