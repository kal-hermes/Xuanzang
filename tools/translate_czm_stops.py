#!/usr/bin/env python3
"""Generate 5-locale lesson content for the changzhengmap-imported stops.

One LLM call per stop produces: EN/JA names + present-day strings, dates,
three-paragraph narratives in all five locales, and a one-line sights fact
in all five locales. zh-Hans paragraph 1 preserves the changzhengmap `desc`
verbatim (factual accuracy); paragraphs 2-3 add context and significance.
Checkpointed in tools/scratch/czm_i18n.json — resumable.
"""
import json
import os
import re
import time
import urllib.request
import urllib.error

BASE = "http://10.255.255.254:9001/v1"
MODEL = os.environ.get("LLM_MODEL", "GLM/glm-5.3-flash")
STOPS = "tools/changzhengmap_stops.json"
CKPT = "tools/scratch/czm_i18n.json"

PROMPT = """你是历史地理教材编辑。根据以下长征事件资料，产出多语言课程内容。

事件：{name}（{type_}）
日期：{date}
现址：{present}
资料描述：{desc}
史料引语：{quote}

要求：
1. zh-Hans 三段叙事：第一段忠实改写资料描述（保留全部史实、数字、人名，不得杜撰）；第二段补充背景或过程细节（只能基于资料合理展开，不得编造具体史实）；第三段写历史意义或后续影响。
2. 其余四种语言（en-GB 英式英语 / fr-CA 加拿大法语 / zh-HK 香港繁体 / ja 日语）为 zh-Hans 三段的忠实翻译。
3. name_en / name_ja：事件名的英文、日文译名（如"血战湘江"→"Battle of the Xiang River"）。
4. present_en / present_ja：现址的译名；若现址为空，用地名拼音 + 省份（如 "Xupu County, Hunan"）。
5. date_en：日期的英文写法（如 "27 Nov – 1 Dec 1934"）；date_zh_norm：规范化中文日期。
6. sight：一句话见闻事实（各语言），取资料中最具体、最可考的一个细节。

只输出 JSON（不要 markdown 代码块）：
{{"name_en": "...", "name_ja": "...", "present_en": "...", "present_ja": "...",
 "date_en": "...", "date_zh_norm": "...",
 "paras": {{"zh-Hans": ["","",""], "en-GB": ["","",""], "fr-CA": ["","",""], "zh-HK": ["","",""], "ja": ["","",""]}},
 "sight": {{"zh-Hans": "...", "en-GB": "...", "fr-CA": "...", "zh-HK": "...", "ja": "..."}}}}"""

LOCALES = ("zh-Hans", "en-GB", "fr-CA", "zh-HK", "ja")

def call_glm(prompt, max_tokens=32000):
    for _ in range(3):
        body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                           "max_tokens": max_tokens, "temperature": 0.2}).encode()
        req = urllib.request.Request(BASE + "/chat/completions", data=body,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                choice = json.load(r)["choices"][0]
            content = choice["message"].get("content")
            if content and content.strip() and choice.get("finish_reason") != "length":
                return content
            max_tokens *= 3  # truncated or empty: retry with more headroom
        except urllib.error.HTTPError as e:
            if e.code == 400:
                # GLM content filter occasionally rejects benign military
                # history text; fall back to the other routed model
                body = json.dumps({"model": "deepseek/deepseek-flash",
                                   "messages": [{"role": "user", "content": prompt}],
                                   "max_tokens": max_tokens, "temperature": 0.2}).encode()
                req = urllib.request.Request(BASE + "/chat/completions", data=body,
                                             headers={"Content-Type": "application/json"})
                try:
                    with urllib.request.urlopen(req, timeout=300) as r:
                        content = json.load(r)["choices"][0]["message"].get("content")
                        if content and content.strip():
                            return content
                except Exception as e2:
                    print("    fallback error:", str(e2)[:80])
            else:
                print("    http error:", str(e)[:80])
        time.sleep(3)
    return ""

def extract_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
    i, j = text.find("{"), text.rfind("}")
    if i >= 0 and j > i:
        return json.loads(text[i:j + 1])
    return json.loads(text)

def valid(out, sid):
    try:
        for loc in LOCALES:
            assert len(out["paras"][loc]) == 3
            assert all(isinstance(p, str) and p.strip() for p in out["paras"][loc])
            assert out["sight"][loc].strip()
        assert out["name_en"].strip() and out["name_ja"].strip()
        return True
    except Exception as e:
        print(f"    invalid ({sid}): {str(e)[:60]}")
        return False

def main():
    stops = json.load(open(STOPS, encoding="utf-8"))
    ckpt = {}
    if os.path.exists(CKPT):
        ckpt = json.load(open(CKPT, encoding="utf-8"))
    for i, s in enumerate(stops):
        if s["id"] in ckpt:
            continue
        print(f"[{i+1}/{len(stops)}] {s['id']} {s['name_zh']} …")
        prompt = PROMPT.format(name=s["name_zh"], type_=s["type"], date=s["date_zh"],
                               present=s["present_zh"], desc=s["desc_zh"],
                               quote=s["quote_zh"] or "（无）")
        out = None
        for attempt in range(3):
            try:
                parsed = extract_json(call_glm(prompt))
                if valid(parsed, s["id"]):
                    out = parsed
                    break
            except Exception as e:
                print(f"    parse fail: {str(e)[:60]}")
            time.sleep(3)
        if out is None:
            print(f"  !! giving up on {s['id']} this run (will retry next run)")
            continue
        ckpt[s["id"]] = out
        json.dump(ckpt, open(CKPT, "w", encoding="utf-8"), ensure_ascii=False)
        time.sleep(1)
    print(f"done: {len(ckpt)}/{len(stops)} stops generated")

if __name__ == "__main__":
    main()
