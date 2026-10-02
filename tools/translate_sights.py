# -*- coding: utf-8 -*-
"""Translate xuanzang_sights.py SIGHTS + PLACES into fr-CA, zh-Hans, zh-HK, ja.

GLM: thinking disabled, 16k max_tokens (learned the hard way — see
translate_narratives.py). Checkpointed per (kind, key, locale), resumable.
Output: tools/xuanzang_sights_i18n.json
"""
import json
import os
import time
import urllib.request

BASE = os.environ["GLM_BASE_URL"].rstrip("/")
KEY = os.environ["GLM_API_KEY"]
MODEL = "glm-4.6"
LOCALES = ["fr-CA", "zh-Hans", "zh-HK", "ja"]
OUT = "tools/xuanzang_sights_i18n.json"
CKPT = "/tmp/sights_ckpt.json"

PROMPTS = {
    "fr-CA": ("Traduis en français (registre soutenu mais naturel, français "
              "d'usage international). Réponds UNIQUEMENT avec la traduction, "
              "sans guillemets ni commentaire."),
    "zh-Hans": "翻译成简体中文。只输出译文，不要引号、不要解释。",
    "zh-HK": "翻譯成繁體中文（香港用字）。只輸出譯文，不要引號、不要解釋。",
    "ja": "日本語に訳してください（歴史解説向けの落ち着いた文体）。訳文のみを出力し、引用符や説明は不要です。",
}

def chat(prompt, user_text):
    body = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_text},
        ],
        "thinking": {"type": "disabled"},
        "max_tokens": 16000,
        "temperature": 0.2,
    }).encode()
    req = urllib.request.Request(
        BASE + "/chat/completions", data=body,
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + KEY})
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.loads(r.read())
    return d["choices"][0]["message"]["content"].strip()

def ok(trans, src):
    return 0.15 * len(src) <= len(trans) <= 3 * len(src) + 30

def main():
    ns = {}
    exec(open("tools/xuanzang_sights.py", encoding="utf-8").read(), ns)
    sights, places = ns["SIGHTS"], ns["PLACES"]

    ck = {}
    if os.path.exists(CKPT):
        ck = json.load(open(CKPT, encoding="utf-8"))

    jobs = []
    for k, text in sights.items():
        for loc_ in LOCALES:
            jobs.append(("sight", k, loc_, text))
    for k, info in places.items():
        for loc_ in ["fr-CA", "ja"]:
            jobs.append(("place_name", k, loc_, info["names"]["en-GB"]))
    # present-day descriptions only for the languages the meta module uses
    for k, info in places.items():
        for loc_ in ["fr-CA", "ja"]:
            jobs.append(("place_present", k, loc_, info["present"]))

    for i, (kind, key, loc_, src) in enumerate(jobs):
        cid = f"{kind}|{key}|{loc_}"
        if cid in ck:
            continue
        for attempt in range(4):
            try:
                t = chat(PROMPTS[loc_], src)
                if not ok(t, src):
                    raise ValueError(f"length sanity failed: {len(src)} -> {len(t)}")
                ck[cid] = t
                json.dump(ck, open(CKPT, "w", encoding="utf-8"), ensure_ascii=False)
                break
            except Exception as e:
                print(f"[{i+1}/{len(jobs)}] {cid} attempt {attempt+1}: {e}", flush=True)
                time.sleep(3 * (attempt + 1))
        else:
            raise SystemExit(f"FAILED {cid}")

    out = {"sights": {}, "place_names": {}, "place_presents": {}}
    for k in sights:
        out["sights"][k] = {loc_: ck[f"sight|{k}|{loc_}"] for loc_ in LOCALES}
    for k in places:
        out["place_names"][k] = {loc_: ck[f"place_name|{k}|{loc_}"] for loc_ in ["fr-CA", "ja"]}
        out["place_presents"][k] = {loc_: ck.get(f"place_present|{k}|{loc_}", "") for loc_ in ["fr-CA", "ja"]}
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"OK: wrote {OUT} ({len(ck)} translations)")

if __name__ == "__main__":
    main()
