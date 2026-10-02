#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Translate ALL Magellan lesson content into fr-CA, zh-Hans, zh-HK, ja
via GLM: narratives (3 paras per stop), when/present meta, sights
facts, quiz place names. Reuses the proven pipeline patterns from
translate_narratives.py / translate_meta.py / translate_sights.py.

Outputs:
  tools/magellan_text_<loc>.py      NARRATIVE_RICH per locale
  tools/magellan_meta_i18n.json     when/present
  tools/magellan_i18n.json          sights + quiz place names (fr/ja)
Checkpointed at /tmp/magellan_ckpt.json; resumable.
"""
import importlib.util
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

BASE = os.environ["GLM_BASE_URL"].rstrip("/")
KEY = os.environ["GLM_API_KEY"]
MODEL = os.environ.get("GLM_MODEL", "glm-4.6")

def load(path, attr):
    spec = importlib.util.spec_from_file_location("m", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return getattr(m, attr)

TEXT = load("tools/magellan_text_en.py", "NARRATIVE_RICH")
META = load("tools/magellan_meta.py", "WHEN")
PRESENT = {k: v["en"] for k, v in
           load("tools/magellan_meta.py", "PRESENT").items()}
SIGHTS = load("tools/magellan_meta.py", "SIGHTS")
QUIZ_PLACES = load("tools/magellan_meta.py", "QUIZ_PLACES")

LOCALES = {
    "fr-CA": "French as used in Canada (fr-CA). Use proper French typographic conventions.",
    "zh-Hans": "Simplified Chinese (zh-Hans), as used in mainland China.",
    "zh-HK": "Traditional Chinese (zh-Hant) as used in Hong Kong (zh-HK). Use Hong Kong vocabulary and traditional characters.",
    "ja": "Japanese (ja). Natural scholarly Japanese.",
}

NARR_PROMPT = """You are translating historical-geographical educational content about the Magellan-Elcano circumnavigation (1519-1522), the first voyage around the world.

Translate each numbered paragraph into {lang}.

Rules:
- Faithful, fluent, readable prose for a general audience; render proper nouns (Magellan, Elcano, Pigafetta, Trinidad, Victoria, Cebu, Tidore...) in their customary target-language form.
- Keep the paragraph count and order exactly: 3 paragraphs in, 3 paragraphs out.
- Return a JSON array of EXACTLY 3 strings — one per paragraph.
- Output ONLY the JSON array.

Paragraphs:
{payload}
"""

CKPT = str(Path(__file__).resolve().parent / "magellan_ckpt.json")
ck = {}
if os.path.exists(CKPT):
    ck = json.load(open(CKPT, encoding="utf-8"))

def save_ck():
    json.dump(ck, open(CKPT, "w", encoding="utf-8"), ensure_ascii=False)

def call(prompt, max_tokens=16000):
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.2,
        "thinking": {"type": "disabled"},
    }).encode()
    req = urllib.request.Request(
        BASE + "/chat/completions", data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + KEY})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)["choices"][0]["message"]["content"]

def extract_array(text):
    t = text.strip()
    m = re.search(r"\[.*\]", t, re.S)
    if m:
        try:
            arr = json.loads(m.group(0))
            if isinstance(arr, list) and len(arr) == 3:
                return arr
        except json.JSONDecodeError:
            pass
    items = re.findall(r'"((?:[^"\\]|\\.)*)"', t)
    if len(items) >= 3:
        return [json.loads('"' + it + '"') for it in items[:3]]
    raise ValueError(f"bad array: {t[:120]}")

def extract_obj(raw, expected_keys):
    m = re.search(r"\{[\s\S]*\}", raw)
    data = json.loads(m.group(0))
    if set(data) != set(expected_keys):
        raise ValueError(f"keys mismatch: {sorted(set(data) ^ set(expected_keys))[:6]}")
    return data

def sane(s, src, lo=0.15, hi=3.0):
    return lo * len(src) <= len(s) <= hi * len(src) + 40

def retry(fn, cid, attempts=5):
    if cid in ck:
        return ck[cid]
    last = None
    for a in range(attempts):
        try:
            val = fn()
            ck[cid] = val
            save_ck()
            return val
        except Exception as e:
            last = e
            print(f"  {cid} retry {a}: {str(e)[:120]}", flush=True)
            time.sleep(3 * (a + 1))
    raise SystemExit(f"FAILED {cid}: {last}")

def main():
    # 1) narratives: one stop per call, per locale
    for loc, desc in LOCALES.items():
        for sid, paras in TEXT.items():
            def go(paras=paras, desc=desc):
                payload = "\n".join(f"{i+1}. {p}" for i, p in enumerate(paras))
                out = extract_array(call(NARR_PROMPT.format(
                    lang=desc, payload=payload)))
                for tr, en in zip(out, paras):
                    if not sane(tr, en, 0.1, 3.5):
                        raise ValueError(f"length sanity failed ({sid})")
                return out
            ck_key = f"narr|{sid}|{loc}"
            retry(go, ck_key)
            print(f"narr {sid}/{loc} ok", flush=True)

    # write per-locale narrative py files
    for loc in LOCALES:
        d = {sid: ck[f"narr|{sid}|{loc}"] for sid in TEXT}
        safe = loc.replace("-", "_") if "-" not in loc else loc
        body = ("# -*- coding: utf-8 -*-\n"
                f"# GLM translation ({MODEL}), {loc}\n\n"
                "NARRATIVE_RICH = " + json.dumps(d, ensure_ascii=False, indent=1) + "\n")
        open(f"tools/magellan_text_{loc}.py", "w", encoding="utf-8").write(body)

    # 2) when/present per locale (whole-dict calls, small payload)
    meta_out = {}
    for loc, desc in LOCALES.items():
        meta_out[loc] = {"when": {}, "present": {}}
        for field, payload, instr in [
            ("when", META,
             "Translate each date phrase naturally; keep numerals and years as digits. Output ONLY a JSON object with the same keys."),
            ("present", PRESENT,
             "Translate each present-day place name. Keep proper nouns in their customary target-language form. Output ONLY a JSON object with the same keys."),
        ]:
            def go(payload=payload, desc=desc, instr=instr):
                prompt = (f"Translate the values of this JSON object into {desc}. {instr}\n"
                          f"Input: {json.dumps(payload, ensure_ascii=False)}")
                return extract_obj(call(prompt, 8000), payload)
            meta_out[loc][field] = retry(go, f"meta|{field}|{loc}")
            print(f"meta {loc}/{field} ok", flush=True)
    json.dump(meta_out, open("tools/magellan_meta_i18n.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # 3) stop NAMES for locales missing them (fr-CA, zh-HK; en/zh-Hans/
    # ja already in magellan_meta.py)
    NAMES = load("tools/magellan_meta.py", "NAMES")
    names_out = {}
    for loc in ["fr-CA", "zh-HK"]:
        names_out[loc] = {}
        for sid, names in NAMES.items():
            src = names["en-GB"]
            def go(src=src, loc=loc):
                p = ("Traduis ce nom de lieu en français. Réponds UNIQUEMENT avec le nom traduit."
                     if loc == "fr-CA" else "將這個地名翻譯成繁體中文（香港用字）。只輸出譯名。")
                out = call(f"{p}\n\n{src}", 2000).strip().strip('"')
                if not (0.1 * len(src) <= len(out) <= 6 * len(src) + 30):
                    raise ValueError("length sanity")
                return out
            names_out[loc][sid] = retry(go, f"name|{sid}|{loc}")
        print(f"names {loc} ok", flush=True)

    # 4) sights facts (per fact per locale)
    sights_out = {loc: {} for loc in LOCALES}
    for loc, desc in LOCALES.items():
        for sid, fact in SIGHTS.items():
            def go(fact=fact, desc=desc):
                p = {"fr-CA": "Traduis en français. Réponds UNIQUEMENT avec la traduction.",
                     "zh-Hans": "翻译成简体中文。只输出译文。",
                     "zh-HK": "翻譯成繁體中文（香港用字）。只輸出譯文。",
                     "ja": "日本語に訳してください。訳文のみ出力。"}[loc]
                out = call(f"{p}\n\n{fact}", 4000).strip().strip('"')
                if not sane(out, fact, 0.15, 3.0):
                    raise ValueError("length sanity")
                return out
            sights_out[loc][sid] = retry(go, f"sight|{sid}|{loc}")
        print(f"sights {loc} ok", flush=True)

    # 4) quiz place names: fr-CA + ja only (zh uses native forms in
    # magellan_meta.py already)
    place_out = {"place_names": {}, "sights": sights_out, "stop_names": names_out}
    for loc in ["fr-CA", "ja"]:
        place_out["place_names"][loc] = {}
        for pid, info in QUIZ_PLACES.items():
            src = info["names"]["en-GB"]
            def go(src=src, loc=loc):
                p = ("Traduis en français (nom de lieu). Réponds UNIQUEMENT avec la traduction."
                     if loc == "fr-CA" else "地名を日本語に訳してください。訳語のみ出力。")
                out = call(f"{p}\n\n{src}", 2000).strip().strip('"')
                if not (0.1 * len(src) <= len(out) <= 6 * len(src) + 30):
                    raise ValueError("length sanity")
                return out
            place_out["place_names"][loc][pid] = retry(go, f"place|{pid}|{loc}")
        print(f"places {loc} ok", flush=True)

    json.dump(place_out, open("tools/magellan_i18n.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("ALL DONE:", len(ck), "checkpoint entries")
    return 0

if __name__ == "__main__":
    sys.exit(main())
