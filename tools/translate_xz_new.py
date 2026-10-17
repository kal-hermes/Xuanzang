#!/usr/bin/env python3
"""Translate the new Xuanzang stops (xuanzang_new_stops.json) into
fr-CA, zh-Hans, zh-HK, ja via GLM. Discipline: thinking disabled,
max_tokens 16k, JSON reply, proportional-length validation, retries.
Output: tools/xuanzang_new_i18n.json"""
import json, os, sys, time, urllib.request

BASE = os.environ["GLM_BASE_URL"].rstrip("/")
KEY = os.environ["GLM_API_KEY"]
SRC = json.load(open("tools/xuanzang_new_stops.json", encoding="utf-8"))

LOCALES = {
    "fr-CA": "French as used in Canada (fr-CA). Keep proper nouns as-is.",
    "zh-Hans": "Simplified Chinese (简体中文). Buddhist/historical terms follow the 大唐西域记 translation conventions already used in this app (e.g. 那烂陀, 戒贤, 曲女城).",
    "zh-HK": "Traditional Chinese as used in Hong Kong (繁體中文, 香港用語). Same terminology conventions as zh-Hans but in traditional characters.",
    "ja": "Japanese (日本語). Use established Japanese Buddhist and historical terms (那爛陀, 戒賢, 曲女城, 玄奘).",
}

def call(key, loc, desc, payload):
    sysprompt = f"You are a professional literary translator. Translate from English into {desc} Reply with ONLY a JSON object, no markdown fences, no commentary."
    body = json.dumps({
        "model": "glm-4.6",
        "messages": [
            {"role": "system", "content": sysprompt},
            {"role": "user", "content": "Translate the values of this JSON object (keep the keys unchanged) into " + loc + ":\n" + json.dumps(payload, ensure_ascii=False)},
        ],
        "thinking": {"type": "disabled"},
        "temperature": 0.3,
        "max_tokens": 16000,
    }, ensure_ascii=False).encode()
    req = urllib.request.Request(BASE + "/chat/completions", data=body, headers={
        "Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        data = json.load(r)
    txt = data["choices"][0]["message"]["content"].strip()
    if txt.startswith("```"):
        txt = txt.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(txt)

def ok_len(src, dst, loc, field=None):
    if not dst or not isinstance(dst, str):
        return False
    if field in ("when", "present") or len(src) <= 6:
        return len(dst) >= 2        # years & place names: non-empty suffices
    floor = 15 if loc != "fr-CA" else 40
    ratio = 0.10 if loc != "fr-CA" else 0.45
    if len(src) < 60:               # short narrative blurbs
        floor = min(floor, 8 if loc != "fr-CA" else 15)
        ratio = min(ratio, 0.30)
    return len(dst) >= max(floor, ratio * len(src))

out = {}
keys = [k for k in SRC if not k.startswith("_")]
if len(sys.argv) > 1:
    keys = [k for k in keys if k in sys.argv[1].split(",")]

for key in keys:
    s = SRC[key]
    out[key] = {}
    for loc, desc in LOCALES.items():
        payload = {
            "short": s["short"],
            "p1": s["rich"][0], "p2": s["rich"][1], "p3": s["rich"][2],
            "when": s["when"],
            "present": s["present"]["en"],
        }
        for attempt in range(4):
            try:
                r = call(key, loc, desc, payload)
                bad = [f for f in ("short", "p1", "p2", "p3", "when", "present")
                       if not ok_len(payload[f], r.get(f), loc, f)]
                if bad:
                    print(f"  {key}/{loc} short/failed fields {bad}, retry", file=sys.stderr)
                    continue
                out[key][loc] = {
                    "short": r["short"],
                    "rich": [r["p1"], r["p2"], r["p3"]],
                    "when": r["when"],
                    "present": r["present"],
                }
                print(f"  {key:16s} {loc:8s} ok ({len(r['p1'])+len(r['p2'])+len(r['p3'])} chars)")
                break
            except Exception as e:
                print(f"  {key}/{loc} error: {e}; retry", file=sys.stderr)
                time.sleep(5 * (attempt + 1))
        else:
            print(f"FAILED {key}/{loc}", file=sys.stderr)
            sys.exit(1)
        time.sleep(1)

# merge with any existing partial output
dest = "tools/xuanzang_new_i18n.json"
try:
    old = json.load(open(dest, encoding="utf-8"))
except FileNotFoundError:
    old = {}
old.update(out)
json.dump(old, open(dest, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", dest, "(", len(old), "stops )")
