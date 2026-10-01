#!/usr/bin/env python3
"""Build data/country-facts.json from Wikidata SPARQL.

One batched query for all countries: flag (P41), coat of arms (P94),
capital (P36 + capital coordinates P625), official+national languages
(P37 with qualifiers), religions (P30), demonym (P1549, several langs),
government type (P122), head of state (P35) & head of government (P6)
with their position titles, establishment (P571), area (P2046),
population (P1082), GDP nominal/PPP total (P2131/P2299) & per-capita
(P4010/P2299), currency (P38 with units), time zones (P421).

Output: { iso3: {...} } — English values; the SPA displays as-is.
Service args: --countries ' + ' — default: union of all lessons.
"""
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENDPOINT = "https://query.wikidata.org/sparql"

QUERY = """
SELECT ?iso3 ?flag ?arms ?capital ?capLabel ?capCoord ?officialLangs
       ?nationalLangs ?religions ?demonymEn ?demonymFr ?demonymZh ?demonymZhHant
       ?govType ?govTypeLabel ?hosEntity ?hosLabel ?hosTitle ?hosStart
       ?hogEntity ?hogLabel ?hogTitle ?hogStart
       ?established ?area ?population ?gdpTotal ?gdpPppTotal ?gdpPcNominal ?gdpPcPpp
       ?currency ?currencyLabel ?currencyUnit ?timezones
WHERE {
  VALUES ?iso3 { %s }
  ?c wdt:P298 ?iso3 .

  OPTIONAL { ?c wdt:P41 ?flag }
  OPTIONAL { ?c wdt:P94 ?arms }
  OPTIONAL {
    ?c p:P36 ?capSt .
    ?capSt ps:P36 ?capital .
    OPTIONAL { ?capSt pq:P580 ?capSince }
    ?capital rdfs:label ?capLabel FILTER(lang(?capLabel)="en")
    OPTIONAL { ?capital wdt:P625 ?capCoord }
  }
  OPTIONAL {
    ?c p:P37 ?langSt .
    ?langSt ps:P37 ?lang .
    ?lang rdfs:label ?langLabel FILTER(lang(?langLabel)="en")
    BIND(CONCAT(?langLabel, IF(BOUND(?langSt2), "", "")) AS ?l1)
  }
  OPTIONAL { ?c wdt:P30 ?religion . ?religion rdfs:label ?religionLabel FILTER(lang(?religionLabel)="en") }
  OPTIONAL { ?c wdt:P1549 ?demonymEn FILTER(lang(?demonymEn)="en") }
  OPTIONAL { ?c wdt:P1549 ?demonymFr FILTER(lang(?demonymFr)="fr") }
  OPTIONAL { ?c wdt:P1549 ?demonymZh FILTER(lang(?demonymZh)="zh") }
  OPTIONAL { ?c wdt:P1549 ?demonymZhHant FILTER(lang(?demonymZhHant)="zh-hant") }
  OPTIONAL { ?c wdt:P122 ?govType . ?govType rdfs:label ?govTypeLabel FILTER(lang(?govTypeLabel)="en") }
  OPTIONAL {
    ?c p:P6 ?hogSt .
    ?hogSt ps:P6 ?hogEntity .
    ?hogEntity rdfs:label ?hogLabel FILTER(lang(?hogLabel)="en")
    OPTIONAL { ?hogSt pq:P39 ?hogTitleQ . ?hogTitleQ rdfs:label ?hogTitle FILTER(lang(?hogTitle)="en") }
    OPTIONAL { ?hogSt pq:P580 ?hogStart }
    FILTER NOT EXISTS { ?hogSt pq:P582 ?hogEnd }
  }
  OPTIONAL {
    ?c p:P35 ?hosSt .
    ?hosSt ps:P35 ?hosEntity .
    ?hosEntity rdfs:label ?hosLabel FILTER(lang(?hosLabel)="en")
    OPTIONAL { ?hosSt pq:P39 ?hosTitleQ . ?hosTitleQ rdfs:label ?hosTitle FILTER(lang(?hosTitle)="en") }
    OPTIONAL { ?hosSt pq:P580 ?hosStart }
    FILTER NOT EXISTS { ?hosSt pq:P582 ?hosEnd }
  }
  OPTIONAL { ?c wdt:P571 ?established }
  OPTIONAL { ?c wdt:P2046 ?area }
  OPTIONAL { ?c wdt:P1082 ?population }
  OPTIONAL { ?c wdt:P2131 ?gdpTotal }
  OPTIONAL { ?c wdt:P2299 ?gdpPppTotal }
  OPTIONAL { ?c wdt:P4010 ?gdpPcNominal }
  OPTIONAL { ?c wdt:P2299 ?gdpPcPpp }
  OPTIONAL { ?c wdt:P38 ?currency . ?currency rdfs:label ?currencyLabel FILTER(lang(?currencyLabel)="en") }
  OPTIONAL { ?c wdt:P421 ?tzItem }
}
LIMIT 50000
"""

# Wikidata P37 statement + qualifiers (official de jure / de facto / national)
LANG_Q = """
  OPTIONAL {
    ?c p:P37 ?langSt .
    ?langSt ps:P37 ?lang .
    ?lang rdfs:label ?langLabel FILTER(lang(?langLabel)="en")
  }
"""


def run_query(values_clause):
    q = QUERY % values_clause
    req = urllib.request.Request(
        ENDPOINT + "?" + urllib.parse.urlencode({"query": q, "format": "json"}),
        headers={"User-Agent": "atlas-lesson-builder/1.0",
                 "Accept": "application/sparql-results+json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)


def main():
    lesson_files = sorted((ROOT / "lessons/examples").glob("*-countries.json"))
    iso3s = set()
    for f in lesson_files:
        data = json.loads(f.read_text(encoding="utf-8"))
        iso3s.update(c["iso3"] for c in data["countries"])
    iso3s = sorted(iso3s)
    print(f"{len(iso3s)} countries across {len(lesson_files)} lessons")

    values = " ".join(f'"{i}"' for i in iso3s)
    cache = Path("/tmp/wdqs-main.json")
    if cache.exists():
        rows = json.loads(cache.read_text())
        print(f"loaded {len(rows)} cached rows")
    else:
        raw = run_query(values)
        rows = raw["results"]["bindings"]
        cache.write_text(json.dumps(rows))
        print(f"SPARQL returned {len(rows)} rows")

    # ?langLabel per-row via second query (kept separate for clarity)
    lcache = Path("/tmp/wdqs-langs.json")
    if lcache.exists():
        lang_rows = json.loads(lcache.read_text())
        print(f"loaded {len(lang_rows)} cached lang rows")
    else:
        lang_rows = run_lang_query(values)
        lcache.write_text(json.dumps(lang_rows))
        print(f"lang query returned {len(lang_rows)} rows")

    facts = {}
    for b in rows:
        iso3 = b["iso3"]["value"]
        d = facts.setdefault(iso3, {})
        def set1(key, val):
            if val and key not in d:
                d[key] = val
        def addlist(key, val):
            if not val:
                return
            d.setdefault(key, [])
            if val not in d[key]:
                d[key].append(val)
        set1("flag", b.get("flag", {}).get("value"))
        set1("arms", b.get("arms", {}).get("value"))
        set1("capital", b.get("capLabel", {}).get("value"))
        set1("capitalCoord", b.get("capCoord", {}).get("value"))
        addlist("religions", b.get("religionLabel", {}).get("value"))
        set1("demonym_en", b.get("demonymEn", {}).get("value"))
        set1("demonym_fr", b.get("demonymFr", {}).get("value"))
        set1("demonym_zh", b.get("demonymZh", {}).get("value"))
        set1("demonym_zh_hant", b.get("demonymZhHant", {}).get("value"))
        set1("govType", b.get("govTypeLabel", {}).get("value"))
        if "hogEntity" in b:
            d.setdefault("headOfGovernment", [])
            hog = {"name": b["hogLabel"]["value"],
                   "title": b.get("hogTitle", {}).get("value"),
                   "since": b.get("hogStart", {}).get("value", "")[:4]}
            if hog not in d["headOfGovernment"]:
                d["headOfGovernment"].append(hog)
        if "hosEntity" in b:
            d.setdefault("headOfState", [])
            hos = {"name": b["hosLabel"]["value"],
                   "title": b.get("hosTitle", {}).get("value"),
                   "since": b.get("hosStart", {}).get("value", "")[:4]}
            if hos not in d["headOfState"]:
                d["headOfState"].append(hos)
        set1("established", (b.get("established", {}) or {}).get("value", "")[:4])
        set1("area_km2", b.get("area", {}).get("value"))
        set1("population", b.get("population", {}).get("value"))
        set1("gdp_nominal_total", b.get("gdpTotal", {}).get("value"))
        set1("gdp_ppp_total", b.get("gdpPppTotal", {}).get("value"))
        set1("gdp_nominal_pc", b.get("gdpPcNominal", {}).get("value"))
        set1("gdp_ppp_pc", b.get("gdpPcPpp", {}).get("value"))
        addlist("currencies", b.get("currencyLabel", {}).get("value"))
        if "tzItem" in b:
            addlist("timezones", b["tzItem"]["value"].rsplit("/", 1)[-1])

    # languages from the separate query
    lang_by_iso = {}
    for b in lang_rows:
        iso3 = b["iso3"]["value"]
        q = b.get("langQual", {}).get("value", "official")
        lang_by_iso.setdefault(iso3, {"official": [], "national": []})
        lbl = b["langLabel"]["value"]
        if lbl not in lang_by_iso[iso3][q if q in ("official", "national") else "official"]:
            lang_by_iso[iso3][q if q in ("official", "national") else "official"].append(lbl)

    for iso3, langs in lang_by_iso.items():
        if iso3 in facts:
            facts[iso3]["languages"] = langs

    out = ROOT / "data/country-facts.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(facts, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} for {len(facts)} countries")

    # coverage report
    fields = ["flag", "arms", "capital", "capitalCoord", "languages", "religions",
              "demonym_en", "govType", "headOfState", "headOfGovernment", "established",
              "area_km2", "population", "gdp_nominal_total", "gdp_ppp_total",
              "gdp_nominal_pc", "gdp_ppp_pc", "currencies", "timezones"]
    print("field coverage (of %d countries):" % len(facts))
    for f_ in fields:
        n = sum(1 for d in facts.values() if d.get(f_))
        print(f"  {f_:18s} {n:3d}")


def run_lang_query(values):
    q = """
SELECT ?iso3 ?langLabel ?langQual WHERE {
  VALUES ?iso3 { %s }
  ?c wdt:P298 ?iso3 .
  ?c p:P37 ?langSt .
  ?langSt ps:P37 ?lang .
  ?lang rdfs:label ?langLabel FILTER(lang(?langLabel)="en")
  OPTIONAL { ?langSt pq:P31 ?q31 }
  BIND(IF(BOUND(?q31), "national", "official") AS ?langQual)
} LIMIT 20000
""" % values
    req = urllib.request.Request(
        ENDPOINT + "?" + urllib.parse.urlencode({"query": q, "format": "json"}),
        headers={"User-Agent": "atlas-lesson-builder/1.0",
                 "Accept": "application/sparql-results+json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)["results"]["bindings"]


if __name__ == "__main__":
    sys.exit(main())
