#!/usr/bin/env python3
"""Localize WHEN (date phrases) and PRESENT (present-day place strings)
into fr-CA, zh-Hans, zh-HK, ja via GLM. One call per field per locale
(smaller payloads -> no truncation). Writes tools/xuanzang_meta_i18n.json."""
import importlib.util
import json
import os
import re
import sys
import time
import urllib.request

BASE = os.environ["GLM_BASE_URL"].rstrip("/")
KEY = os.environ["GLM_API_KEY"]

def load(path, attr):
    spec = importlib.util.spec_from_file_location("m", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return getattr(m, attr)

WHEN = load("tools/xuanzang_meta.py", "WHEN")
PRESENT = {k: v["en"] for k, v in load("tools/xuanzang_meta.py", "PRESENT").items()}

LOCALES = {
    "fr-CA": "French as used in Canada (fr-CA)",
    "zh-Hans": "Simplified Chinese (zh-Hans)",
    "zh-HK": "Traditional Chinese as used in Hong Kong (zh-HK)",
    "ja": "Japanese (ja)",
}

def call(prompt, max_tokens=8000):
    body = json.dumps({
        "model": os.environ.get("GLM_MODEL", "glm-4.6"),
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens, "temperature": 0.2,
        "thinking": {"type": "disabled"},
    }).encode()
    req = urllib.request.Request(BASE + "/chat/completions", data=body,
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + KEY})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)["choices"][0]["message"]["content"]

def extract(raw, expected_keys):
    m = re.search(r"\{[\s\S]*\}", raw)
    data = json.loads(m.group(0))
    # tolerate wrapped {"present": {...}} nesting
    if "present" in data and isinstance(data["present"], dict) and set(data) == {"present"}:
        data = data["present"]
    if set(data) != set(expected_keys):
        raise ValueError(f"keys mismatch: {sorted(set(data) ^ set(expected_keys))[:6]}")
    return data

def main():
    out = {}
    for loc, desc in LOCALES.items():
        out[loc] = {"when": {}, "present": {}}
        for field, payload, instr in [
            ("present", PRESENT,
             "Translate each present-day place name. Keep proper nouns in their customary target-language form. Output ONLY a JSON object with the same keys."),
            ("when", WHEN,
             "Translate each date phrase naturally; keep numerals and CE years as digits. Output ONLY a JSON object with the same keys."),
        ]:
            prompt = (f"Translate the values of this JSON object into {desc}. {instr}\n"
                      f"Input: {json.dumps(payload, ensure_ascii=False)}")
            for attempt in range(4):
                try:
                    raw = call(prompt)
                    out[loc][field] = extract(raw, payload)
                    print(f"  {loc}/{field} OK")
                    break
                except Exception as e:
                    print(f"  {loc}/{field} retry {attempt}: {str(e)[:120]}")
                    time.sleep(3 * (attempt + 1))
            else:
                print(f"{loc}/{field} FAILED")
                return 1
            time.sleep(1)
    with open("tools/xuanzang_meta_i18n.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("wrote tools/xuanzang_meta_i18n.json")
    return 0

if __name__ == "__main__":
    sys.exit(main())
