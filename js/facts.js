/* Atlas — country facts from Wikidata entities, fetched live on click.
 *
 * One GET per country (Special:EntityData, CDN-friendly, no SPARQL),
 * parsed into the info panel fields; entity labels resolved via a
 * single batched wbgetentities call. Cached in localStorage (7 days)
 * so repeat clicks are instant and the app degrades gracefully when
 * offline.
 *
 * Property map (Wikipedia "Infobox country" equivalents):
 *   P41 flag image, P94 coat of arms, P36 capital, P37 official and
 *   national languages, P122 government type, P35 head of state,
 *   P6 head of government, P571 inception/establishment, P2046 area,
 *   P1082 population, P2131 GDP nominal, P2132 GDP nominal per capita,
 *   P38 currency, P421 time zone.
 *
 * Known gaps (verified against live entities): Wikidata has no
 * state-religion property (Wikipedia removed it from infoboxes in
 * 2018); GDP PPP (P2299) / PPP per capita (P4010) are rarely present —
 * per-capita is derived as total/latest-population when missing.
 */
(function () {
  "use strict";

  const ENTITY_CACHE_PREFIX = "atlas.wd.";
  const CACHE_TTL = 7 * 24 * 3600e3;
  const UA = { "Accept": "application/json" };

  function cacheGet(qid) {
    try {
      const raw = localStorage.getItem(ENTITY_CACHE_PREFIX + qid);
      if (!raw) return null;
      const { t, e } = JSON.parse(raw);
      if (Date.now() - t > CACHE_TTL) return null;
      return e;
    } catch { return null; }
  }
  function cacheSet(qid, entity) {
    try {
      localStorage.setItem(ENTITY_CACHE_PREFIX + qid,
        JSON.stringify({ t: Date.now(), e: entity }));
    } catch { /* quota — ignore */ }
  }

  async function fetchEntity(qid) {
    const cached = cacheGet(qid);
    if (cached) return cached;
    const res = await fetch(
      `https://www.wikidata.org/wiki/Special:EntityData/${qid}.json`,
      { headers: UA });
    if (!res.ok) throw new Error(`wikidata ${res.status}`);
    const data = await res.json();
    const entity = data.entities[qid];
    cacheSet(qid, entity);
    return entity;
  }

  // label language fallback chain for a UI locale
  function labelLangs() {
    const loc = (window.I18n && I18n.locale) || "en-GB";
    const chains = {
      "en-GB": ["en"],
      "fr-CA": ["fr", "en"],
      "zh-Hans": ["zh", "zh-hans", "en"],
      "zh-HK": ["zh-hant", "zh-hk", "zh", "en"],
      "ja": ["ja", "en"],
    };
    return chains[loc] || ["en"];
  }

  function pickLabel(labels) {
    if (!labels) return null;
    for (const lang of labelLangs()) {
      const l = labels[lang];
      if (l && l.value) return l.value;
    }
    // en occasionally absent outright; en-* -> any
    const enVar = Object.keys(labels).find((k) => k.startsWith("en-"));
    if (enVar) return labels[enVar].value;
    const any = Object.values(labels)[0];
    return any && any.value;
  }

  // batched label lookup: ids -> {id: label}, chunked (API cap: 50 ids)
  async function fetchLabels(ids) {
    const out = {};
    if (!ids.length) return out;
    for (let i = 0; i < ids.length; i += 50) {
      const chunk = ids.slice(i, i + 50);
      try {
        // NOTE: no &languages= param — the server-side filter can zero
        // out items whose labels exist only outside the requested
        // chain (e.g. Q4916 euro has no 'en' label at all); language
        // selection happens client-side in pickLabel()
        const res = await fetch(
          "https://www.wikidata.org/w/api.php?action=wbgetentities" +
          `&ids=${chunk.join("|")}&props=labels&format=json&origin=*`,
          { headers: UA });
        if (!res.ok) continue;
        const data = await res.json();
        for (const [id, e] of Object.entries(data.entities || {})) {
          if (e.missing !== undefined) continue;
          const l = pickLabel(e.labels);
          if (l) out[id] = l;
        }
      } catch { /* chunk failed; ids stay unresolved */ }
    }
    return out;
  }

  // one retry pass for ids that didn't resolve (throttle/transient 500s)
  async function fetchLabelsWithRetry(ids) {
    const labels = await fetchLabels(ids);
    const missing = ids.filter((id) => !labels[id]);
    if (missing.length && missing.length < ids.length) {
      const second = await fetchLabels(missing);
      Object.assign(labels, second);
    } else if (missing.length) {
      // everything failed once — a single retry after a beat
      await new Promise((r) => setTimeout(r, 800));
      const second = await fetchLabels(missing);
      Object.assign(labels, second);
    }
    return labels;
  }

  // ---- claim parsing helpers ----

  function statements(entity, prop) {
    return (entity.claims && entity.claims[prop]) || [];
  }

  // statement with no end qualifier (P582) — "current"
  function current(sts) {
    const live = sts.filter((st) => {
      const q = st.qualifiers || {};
      return !q.P582 && !(st.rank === "deprecated");
    });
    return live.length ? live : [];
  }

  function latestByTime(sts) {
    // prefer preferred rank, then the most recent P585 point in time
    const withTime = sts.filter((st) => st.qualifiers && st.qualifiers.P585)
      .map((st) => ({
        st,
        t: st.qualifiers.P585[0].datavalue.value.time,
      }));
    withTime.sort((a, b) => (a.t < b.t ? 1 : -1));
    const ranked = sts.filter((st) => st.rank === "preferred");
    return (ranked.length ? ranked : (withTime.length ? withTime.map((x) => x.st) : sts))[0];
  }

  function qidOf(st) {
    const dv = st.mainsnak.datavalue;
    return dv && dv.value && dv.value.id;
  }

  function amountOf(st) {
    const dv = st.mainsnak.datavalue;
    if (!dv) return null;
    return parseFloat(dv.value.amount);
  }

  function yearOf(st) {
    const dv = st.mainsnak.datavalue;
    if (!dv) return null;
    const t = dv.value.time; // "+1958-10-04T00:00:00Z"
    return t.slice(1, 5);
  }

  // ---- main: parse an entity into display-ready fields ----

  function parseEntity(entity, labels) {
    const f = {};
    const L = (id) => labels[id] || id;

    const flag = statements(entity, "P41")[0];
    if (flag) f.flag = flag.mainsnak.datavalue.value;
    const arms = statements(entity, "P94")[0];
    if (arms) f.arms = arms.mainsnak.datavalue.value;

    const caps = current(statements(entity, "P36"));
    if (caps.length) {
      // several concurrent seat statements can point at the same city
      // (e.g. DEU has 3 Berlin seats) — dedupe by entity id
      const seen = new Set();
      const labels = [];
      for (const st of caps) {
        const id = qidOf(st);
        if (!id || seen.has(id)) continue;
        seen.add(id);
        labels.push(L(id));
      }
      f.capital = labels.join(", ");
      const capCoord = caps[0].qualifiers && caps[0].qualifiers.P625;
    }

    const langs = current(statements(entity, "P37"));
    if (langs.length) {
      f.languages = [...new Set(langs.map((st) => L(qidOf(st))))].join(", ");
    }

    const gov = statements(entity, "P122");
    if (gov.length) {
      f.government = [...new Set(current(gov).map((st) => L(qidOf(st))).values())].join("; ");
    }

    function leader(prop) {
      const live = current(statements(entity, prop));
      if (!live.length) return null;
      return live.map((st) => {
        const q = st.qualifiers || {};
        let title = null;
        if (q.P39) {
          title = q.P39.map((snk) => snk.datavalue.value.id).map(L).join(", ");
        }
        let since = null;
        if (q.P580) since = q.P580[0].datavalue.value.time.slice(1, 5);
        return { name: L(qidOf(st)), title, since };
      });
    }
    f.leaders = leader("P35"); // head of state
    f.hog = leader("P6");      // head of government

    const est = statements(entity, "P571");
    if (est.length) f.established = yearOf(est[0]);

    const area = latestByTime(statements(entity, "P2046"));
    if (area) f.areaKm2 = Math.round(amountOf(area));

    const pop = latestByTime(statements(entity, "P1082"));
    if (pop) f.population = Math.round(amountOf(pop));
    const popTime = pop && pop.qualifiers && pop.qualifiers.P585
      ? pop.qualifiers.P585[0].datavalue.value.time.slice(1, 5) : null;

    const gdpTotal = latestByTime(statements(entity, "P2131"));
    if (gdpTotal) {
      f.gdpNominalTotalUsd = Math.round(amountOf(gdpTotal));
      f.gdpYear = gdpTotal.qualifiers && gdpTotal.qualifiers.P585
        ? gdpTotal.qualifiers.P585[0].datavalue.value.time.slice(1, 5) : null;
      if (f.population) {
        f.gdpNominalPerCapitaUsd = Math.round(f.gdpNominalTotalUsd / f.population);
        f.gdpPerCapitaDerived = true;
      }
    }
    // PPP: rarely present; include when it is
    const gdpPpp = latestByTime(statements(entity, "P2299"));
    if (gdpPpp) {
      f.gdpPppTotalUsd = Math.round(amountOf(gdpPpp));
      if (f.population) f.gdpPppPerCapitaUsd = Math.round(f.gdpPppTotalUsd / f.population);
    }
    const gdpPc = latestByTime(statements(entity, "P2132"));
    if (gdpPc) f.gdpNominalPerCapitaUsd = Math.round(amountOf(gdpPc));

    const currencies = current(statements(entity, "P38"));
    if (currencies.length) {
      f.currencies = [...new Set(currencies.map((st) => L(qidOf(st))))].join(", ");
    }

    const tzs = statements(entity, "P421");
    if (tzs.length) {
      f.timezones = [...new Set(tzs.map((st) => L(qidOf(st))))].join(", ");
    }

    // demonym (P1549 monolingual text) in the UI locale's chain
    const demo = statements(entity, "P1549");
    if (demo.length) {
      const langs = labelLangs();
      for (const lang of langs) {
        const hit = demo.find((st) => {
          const v = st.mainsnak.datavalue && st.mainsnak.datavalue.value;
          return v && v.language === lang && v.text;
        });
        if (hit) { f.demonym = hit.mainsnak.datavalue.value.text; break; }
      }
    }

    return f;
  }

  // ---- public API ----

  window.AtlasFacts = {
    /** populated by app.js from data/iso3-to-qid.json + capital coords */
    ISO3_TO_QID: null,
    CAPITAL_COORDS: null,
    async get(iso3) {
      const qid = (this.ISO3_TO_QID || {})[iso3];
      if (!qid) return null;
      const entity = await fetchEntity(qid);
      // collect item ids needing labels — CURRENT statements only, so
      // historic leaders and former capitals don't bloat the id set
      const ids = new Set([qid]);
      for (const p of ["P36", "P37", "P122", "P38", "P421"]) {
        for (const st of current(statements(entity, p))) {
          const id = st.mainsnak.datavalue && st.mainsnak.datavalue.value.id;
          if (id) ids.add(id);
        }
      }
      for (const p of ["P35", "P6"]) {
        for (const st of current(statements(entity, p))) {
          const id = st.mainsnak.datavalue && st.mainsnak.datavalue.value.id;
          if (id) ids.add(id);
          const q = st.qualifiers || {};
          if (q.P39) for (const snk of q.P39) {
            if (snk.datavalue && snk.datavalue.value.id) ids.add(snk.datavalue.value.id);
          }
        }
      }
      const labels = await fetchLabelsWithRetry([...ids]);
      const facts = parseEntity(entity, labels);
      facts.qid = qid;
      // capital coordinates: look for P625 on capital items is not in
      // labels; fetched lazily by the panel if needed (see app.js)
      return facts;
    },
  };
})();
