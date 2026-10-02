#!/usr/bin/env python3
"""Translate the Xuanzang rich narratives into fr-CA, zh-Hans, zh-HK, ja
via GLM. Chunks one stop (3 paragraphs) per request; retries on failure.
Writes tools/xuanzang_text_<loc>.py as Python dict source."""
import importlib.util
import json
import os
import re
import sys
import time
import urllib.request

BASE = os.environ["GLM_BASE_URL"].rstrip("/")
KEY = os.environ["GLM_API_KEY"]

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

en = load("en", "tools/xuanzang_text_en.py")
STOPS = list(en.NARRATIVE_RICH.keys())

LOCALES = {
    "fr-CA": "French as used in Canada (fr-CA). Use proper French typographic conventions (espaces insécables before : ; ! ?, guillemets « »).",
    "zh-Hans": "Simplified Chinese (zh-Hans), as used in mainland China.",
    "zh-HK": "Traditional Chinese (zh-Hant) as used in Hong Kong (zh-HK). Use Hong Kong vocabulary and traditional characters.",
    "ja": "Japanese (ja). Natural scholarly Japanese.",
}

PROMPT = """You are translating historical-geographical educational content about the 7th-century Buddhist monk Xuanzang's pilgrimage from Chang'an to India and back (629-645 CE).

Translate each numbered paragraph into {lang_desc}

Rules:
- Faithful, fluent, readable prose for a general audience; keep historical terms accurate (e.g. keep proper nouns like Nalanda, Sarvastivada, Yogacara appropriately rendered as customary in the target language).
- Keep the paragraph count and order exactly: 3 paragraphs in, 3 paragraphs out.
- Return a JSON array of EXACTLY 3 strings — one per paragraph. Do NOT merge them into a single string.
- Do not add commentary, headers, or numbering. Output ONLY the JSON array.

Paragraphs:
{payload}
"""

def call_glm(prompt, max_tokens=16000):
    body = json.dumps({
        "model": os.environ.get("GLM_MODEL", "glm-4.6"),
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.2,
        "thinking": {"type": "disabled"},
    }).encode()
    req = urllib.request.Request(
        BASE + "/chat/completions",
        data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + KEY})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)["choices"][0]["message"]["content"]

def extract_json(text):
    # strip markdown fences if any
    t = text.strip()
    m = re.search(r"\[.*\]", t, re.S)
    if m:
        try:
            arr = json.loads(m.group(0))
            if isinstance(arr, list):
                return arr
        except json.JSONDecodeError:
            pass  # truncated array — try repairing below
    # repair truncated JSON array: keep complete string items, drop the tail
    m2 = re.search(r"\[[\s\S]*", t)
    if m2:
        frag = m2.group(0)
        try:
            items = re.findall(r'"((?:[^"\\]|\\.)*)"', frag)
            items = [json.loads('"' + it + '"') for it in items]
            if len(items) >= 3:
                return items[:3]
            if len(items) >= 1:
                return items  # maybe a merged single string — caller may split
        except Exception:
            pass
    # model merged all paragraphs into one string: split on blank lines
    if t and "[" not in t[:2]:
        parts = [p.strip() for p in re.split(r"\n\s*\n", t) if len(p.strip()) > 40]
        if len(parts) >= 3:
            return parts[:3]
    raise ValueError(f"unrecoverable response: {t[:150]}")

def split_merged(text, en_paras):
    """Split a single merged translation back into len(en_paras) chunks,
    cutting at sentence boundaries proportionally to the EN paragraph
    lengths (by character count)."""
    sentences = [s for s in re.split(r"(?<=[。！？；.!?;])\s*", text) if s.strip()]
    n = len(en_paras)
    if len(sentences) < n:
        return [text]
    total_en = sum(len(p) for p in en_paras)
    total = sum(len(s) for s in sentences)
    cuts = []
    acc = 0
    for p in en_paras[:-1]:
        acc += len(p)
        cuts.append(acc / total_en * total)
    out = []
    i = 0
    for ci, cut in enumerate(cuts):
        need = n - ci - 1  # chunks after this one, each needing >= 1 sentence
        chunk = []
        while i < len(sentences):
            chunk.append(sentences[i])
            i += 1
            rem = len(sentences) - i
            pos = sum(len(s) for s in chunk)
            if pos >= cut and rem >= need:
                break
            if rem == need:  # must close now to leave enough sentences
                break
        out.append("".join(chunk))
    out.append("".join(sentences[i:]))
    return out

def translate_singles(paras, lang_desc):
    out = []
    for i, p in enumerate(paras):
        got = None
        # the model sometimes returns the wrong paragraph (e.g. the LAST
        # one); retry, collecting until we get a plausible translation of p
        for attempt in range(4):
            prompt = (f"Translate paragraph {i+1} of {len(paras)} into "
                      f"{lang_desc}. Faithful, fluent prose; proper nouns in "
                      f"customary target-language form. Output ONLY the "
                      f"translated paragraph text, nothing else.\n\n{p}")
            raw = call_glm(prompt, max_tokens=6000)
            t = raw.strip().lstrip("\ufeff")
            t = re.sub(r"^\[\d+\]\s*", "", t)  # strip [1]-style markers
            if (t.startswith("[") or t.startswith("{") or len(t) < 40):
                continue
            got = t
            # sanity: length within 0.25x-3x of source (CJK vs latin)
            if 0.15 * len(p) <= len(t) <= 3 * len(p):
                break
        if got is None:
            raise ValueError(f"no usable translation for paragraph {i+1}")
        out.append(got)
        time.sleep(0.5)
    return out

def translate_locale(loc, lang_desc):
    out_path = f"tools/xuanzang_text_{loc}.py"
    # resume support
    done = {}
    if os.path.exists(out_path):
        prev = load(loc, out_path)
        done = prev.NARRATIVE_RICH
        print(f"  resuming, {len(done)} stops already done")
    for stop in STOPS:
        if stop in done:
            continue
        paras = en.NARRATIVE_RICH[stop]
        payload = "\n\n".join(f"[{i+1}] {p}" for i, p in enumerate(paras))
        prompt = PROMPT.format(lang_desc=lang_desc, payload=payload)
        for attempt in range(4):
            try:
                raw = call_glm(prompt)
                arr = extract_json(raw)
                # model sometimes merges all paragraphs into one string
                # (or truncates): split a lone survivor proportionally
                if (isinstance(arr, list) and len(arr) == 1
                        and isinstance(arr[0], str)):
                    arr = split_merged(arr[0], paras)
                min_len = max(15, int(0.15 * min(len(p) for p in paras)))
                if not (isinstance(arr, list) and len(arr) == 3 and all(isinstance(x, str) and len(x) >= min_len for x in arr)):
                    raise ValueError(f"bad shape: {str(arr)[:100]}")
                done[stop] = arr
                break
            except Exception as e:
                print(f"    {stop} attempt {attempt+1} failed: {e}")
                time.sleep(3 * (attempt + 1))
        else:
            # last resort: translate paragraph-by-paragraph (tiny
            # responses, cannot truncate)
            try:
                done[stop] = translate_singles(paras, lang_desc)
                print(f"    {stop}: recovered via per-paragraph mode")
            except Exception as e:
                print(f"    {stop} per-paragraph also failed: {str(e)[:100]}")
                print(f"  GIVING UP on {loc}/{stop}")
                return False
        # persist after each stop
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("# Auto-translated by GLM; source tools/xuanzang_text_en.py\n")
            f.write(f"NARRATIVE_RICH = {repr(done)}\n")
        time.sleep(1)
    print(f"  {loc}: {len(done)}/28 stops written")
    return True

def main():
    ok = True
    for loc, desc in LOCALES.items():
        print(f"== {loc}")
        ok = translate_locale(loc, desc) and ok
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
