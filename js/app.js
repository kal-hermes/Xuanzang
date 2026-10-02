/* app.js — lesson loading, mode state machines, UI wiring.
 *
 * Lesson JSON contract (schema v0, docs/LESSON_SCHEMA.md):
 *   { id, title: {locale: str}, type: "countries",
 *     view: {lon0, lat0, lon1, lat1},
 *     countries: [{iso3, names: {locale: str}, facts: {population, capital,
 *                 demonym, founded, collapsed}}] }
 */
(function () {
  "use strict";

  const $ = (sel) => document.querySelector(sel);
  const map = window.AtlasMap;
  const i18n = window.I18n;

  const state = {
    lesson: null,
    mode: "learn",
    answerStyle: "choice",
    projection: localStorage.getItem("atlas.projection") || "equirectangular",
    order: [],          // shuffled iso3 list for tests
    index: 0,
    correct: 0,
    locked: false,
  };

  // ---------- lesson loading ----------

  const LESSONS = [
    { file: "lessons/examples/europe-countries.json" },
    { file: "lessons/examples/asia-countries.json" },
    { file: "lessons/examples/africa-countries.json" },
    { file: "lessons/examples/north-america-countries.json" },
    { file: "lessons/examples/south-america-countries.json" },
    { file: "lessons/examples/oceania-countries.json" },
    { file: "lessons/xuanzang/journey.json" },
  ];

  async function loadLesson(file) {
    // script-tag data first (file://-safe); fetch fallback otherwise
    let data = window.ATLAS_LESSONS && window.ATLAS_LESSONS[file];
    if (!data) {
      const res = await fetch(file);
      if (!res.ok) throw new Error(`failed to load ${file}: ${res.status}`);
      data = await res.json();
    }
    state.lesson = data;
    state.visited = null; // fresh learn-session per lesson
    state.mode = $("#mode-select").value;
    startMode();
  }

  function fillLessonSelect() {
    const sel = $("#lesson-select");
    sel.innerHTML = "";
    for (const l of LESSONS) {
      const opt = document.createElement("option");
      opt.value = l.file;
      // placeholder text; replaced once titles are fetched below
      opt.textContent = l.file.split("/").pop().replace(/\.json$/, "");
      sel.appendChild(opt);
    }
    sel.addEventListener("change", async () => {
      await loadLesson(sel.value);
      refreshLessonTitles();
    });
    // fetch every lesson's title up front so ALL options show proper
    // localized names immediately, not just the selected one
    for (const l of LESSONS) {
      Promise.resolve(
        (window.ATLAS_LESSONS && window.ATLAS_LESSONS[l.file]) ||
        fetch(l.file).then((r) => r.json())
      ).then((j) => {
        lessonTitles[l.file] = j.title;
        refreshLessonTitles();
        })
        .catch(() => {});
    }
  }

  function refreshLessonTitles() {
    const sel = $("#lesson-select");
    [...sel.options].forEach((opt) => {
      const title = lessonTitles[opt.value];
      if (title) opt.textContent = loc(title) || opt.textContent;
    });
  }

  function loc(dict) {
    if (!dict) return "";
    return dict[i18n.locale] ?? dict["en-GB"] ?? Object.values(dict)[0] ?? "";
  }

  // lesson file -> title dict (all locales), fetched once at startup
  const lessonTitles = {};

  // ---------- helpers ----------

  function shuffle(arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  function country(iso3) {
    return state.lesson.countries.find((c) => c.iso3 === iso3);
  }

  function displayName(iso3) {
    const c = country(iso3);
    return c ? loc(c.names) : iso3;
  }

  function setHint(text) { $("#hint-text").textContent = text; }

  function updateScore() {
    $("#score-display").textContent =
      i18n.t("score", { correct: state.correct, total: state.order.length });
  }

  function normalizeAnswer(s) {
    return s.trim().toLowerCase().replace(/\s+/g, " ");
  }

  function acceptableAnswers(c) {
    // localized name in every supported locale + accepted aliases
    const answers = new Set();
    for (const v of Object.values(c.names || {})) answers.add(normalizeAnswer(v));
    for (const v of c.accept || []) answers.add(normalizeAnswer(v));
    return answers;
  }

  // ---------- modes ----------

  function startMode() {
    map.clearOverlay();
    map.clearRevealed();
    map.clearHighlights("correct");
    map.clearHighlights("wrong");
    map.clearHighlights("highlighted");
    map.resetView();
    $("#info-panel").hidden = true;
    $("#prompt-bar").hidden = state.mode === "learn";
    $("#answer-box").hidden = true;
    $("#answer-style-row").hidden = state.mode !== "name";

    map.render(state.lesson, { projection: state.projection });

    if (state.mode === "learn") {
      setHint(state.projection === "globe" ? i18n.t("hint_globe") : i18n.t("hint_learn"));
      map.setClickHandler((iso3) => learnClick(iso3, false));
      if (!state.visited) state.visited = new Set();
      renderCountryList();
      if (state.lesson.type === "journey") renderJourney();
    } else {
      $("#country-list-panel").hidden = true;
      state.order = shuffle(state.lesson.countries.map((c) => c.iso3));
      state.index = 0;
      state.correct = 0;
      state.locked = false;
      if (state.mode === "locate") {
        setHint(state.projection === "globe" ? i18n.t("hint_globe") : i18n.t("hint_locate"));
        map.setClickHandler((iso3) => locateClick(iso3));
        $("#reveal-button").hidden = false;
        nextLocate();
      } else {
        $("#reveal-button").hidden = true;
        state.answerStyle = $("#answer-style-select").value;
        setHint(state.projection === "globe" ? i18n.t("hint_globe") : i18n.t("hint_name"));
        map.setClickHandler(() => {});
        nextName();
      }
      updateScore();
    }
  }

  function learnClick(iso3, viaSidebar) {
    const c = country(iso3);
    if (!c) return; // country not part of this lesson; ignore
    map.reveal(iso3);
    map.setCurrent(iso3);
    if (state.visited) state.visited.add(iso3);
    const li = document.querySelector(`#country-list li[data-iso3="${iso3}"]`);
    if (li) li.classList.add("visited");
    // sidebar clicks additionally point at the country on the map
    // (the user presumably doesn't know where it is)
    if (viaSidebar) {
      map.rotateToFace(iso3);
      map.pointCountry(iso3);
    } else {
      map.clearOverlay(); // wipes journey route arrows too — redraw them
      if (state.lesson.type === "journey") renderJourneyRoutes();
    }
    showInfo(c, iso3);
  }

  // Sidebar (Learn mode): every country in the lesson; visited ones
  // are crossed out. Clicking a name behaves like clicking the country
  // on the map, plus an arrow pointing at it on the map.
  function renderCountryList() {
    const panel = $("#country-list-panel");
    if (!state.lesson) { panel.hidden = true; return; }
    panel.hidden = false;
    const ul = $("#country-list");
    ul.innerHTML = "";
    const coll = new Intl.Collator(i18n.locale);
    const items = [...state.lesson.countries].sort((a, b) =>
      coll.compare(loc(a.names) || a.iso3, loc(b.names) || b.iso3));
    for (const c of items) {
      const li = document.createElement("li");
      li.dataset.iso3 = c.iso3;
      if (state.visited && state.visited.has(c.iso3)) li.classList.add("visited");
      li.textContent = loc(c.names) || c.iso3;
      li.addEventListener("click", () => learnClick(c.iso3, true));
      ul.appendChild(li);
    }
  }

  // ---------- journey lessons ----------
  // Learn mode for type:"journey": draw both route legs and list the
  // stops in TRAVEL ORDER (not alphabetically). Clicking a stop points
  // at its coordinates and shows year + narrative.
  function renderJourney() {
    const L = state.lesson;
    renderJourneyRoutes();
    map.renderStopDots(L.stops, state.focusedStop || null, (id) => {
      const s = L.stops.find((x) => x.id === id);
      if (s) journeyStopClick(s);
    });
    // stops sidebar replaces the alphabetical country list
    const ul = $("#country-list");
    ul.innerHTML = "";
    ul.classList.add("journey-order");
    for (const s of L.stops) {
      const li = document.createElement("li");
      li.dataset.stop = s.id;
      if (state.visitedStops && state.visitedStops.has(s.id)) li.classList.add("visited");
      const yr = document.createElement("span");
      yr.className = "stop-year";
      yr.textContent = s.year;
      const nm = document.createElement("span");
      nm.textContent = loc(s.names) || s.id;
      li.append(yr, document.createTextNode(" "), nm);
      li.addEventListener("click", () => journeyStopClick(s));
      ul.appendChild(li);
    }
    $("#country-list-panel h2").textContent = i18n.t("stops");
  }

  function renderJourneyRoutes() {
    const L = state.lesson;
    map.addArrow(L.route_out, "#ffd24a");
    map.addArrow(L.route_back, "#e05674");
  }

  function journeyStopClick(s) {
    if (!state.visitedStops) state.visitedStops = new Set();
    state.visitedStops.add(s.id);
    state.focusedStop = s.id;
    const li = document.querySelector(`#country-list li[data-stop="${s.id}"]`);
    if (li) li.classList.add("visited");
    map.focusStopDot(s.id);
    map.rotateToCoord(s.coords);
    map.pointAt(s.coords);
    showStopInfo(s);
    if (s.iso3) {
      map.reveal(s.iso3);
      map.setCurrent(s.iso3);
    }
  }

  function showStopInfo(s) {
    $("#info-panel").hidden = false;
    $("#info-name").textContent = loc(s.names) || s.id;
    $("#info-name").dataset.iso3 = "";
    const dl = $("#info-facts");
    dl.innerHTML = "";
    const addRow = (label, value, cls) => {
      const dt = document.createElement("dt");
      dt.textContent = label;
      const dd = document.createElement("dd");
      if (cls) dd.className = cls;
      dd.textContent = value;
      dl.append(dt, dd);
    };
    addRow(i18n.t("year"), s.when || s.year);
    if (s.present) addRow(i18n.t("today_at"), loc(s.present) || s.present.en || "");
    const country = state.lesson.countries.find((c) => c.iso3 === s.iso3);
    if (country) addRow(i18n.t("today_in"), loc(country.names) || s.iso3);
    // narrative: {locale: [paragraphs]} (rich) or {locale: string} (legacy)
    const narr = s.narrative || {};
    let paras = narr[i18n.locale];
    if (paras == null) paras = Object.values(narr)[0];
    if (typeof paras === "string") paras = [paras];
    const first = document.createElement("dt");
    first.textContent = i18n.t("what_he_saw");
    dl.appendChild(first);
    for (const p of paras || []) {
      const dd = document.createElement("dd");
      dd.className = "narrative";
      dd.textContent = p;
      dl.appendChild(dd);
    }
  }

  async function showInfo(c, iso3) {
    $("#info-panel").hidden = false;
    $("#info-name").textContent = loc(c.names) || iso3;
    $("#info-name").dataset.iso3 = iso3;
    const dl = $("#info-facts");
    dl.innerHTML = "";
    const factDefs = [
      ["capital", c.facts && c.facts.capital],
      ["languages", null],
      ["demonym", c.facts && c.facts.demonym],
      ["government", null],
      ["established", null],
      ["area", null],
      ["population", c.facts && c.facts.population],
      ["gdp_nominal", null],
      ["gdp_ppp", null],
      ["currency", null],
      ["timezone", null],
      ["founded", c.facts && c.facts.founded],
      ["collapsed", c.facts && c.facts.collapsed],
    ];
    // lesson facts render instantly; Wikidata facts replace/augment them
    // once the entity arrives (cached in localStorage after first click)
    renderFacts(dl, factDefs, {});
    let f = null;
    try {
      f = await AtlasFacts.get(iso3);
    } catch (err) {
      f = null; // offline / Wikidata down: lesson facts stay visible
    }
    if (!f) return;
    // bail if another country was clicked while fetching
    if ($("#info-name").textContent !== (loc(c.names) || iso3)) return;
    const locale = I18n.locale;
    const nf = new Intl.NumberFormat(locale);
    const fmtInt = (n) => nf.format(n);
    const t = (k, p) => i18n.t(k, p);
    const values = {
      capital: f.capital,
      languages: f.languages,
      demonym: f.demonym || (c.facts && c.facts.demonym),
      government: f.government,
      established: f.established,
      area: f.areaKm2 ? fmtInt(f.areaKm2) + " km²" : null,
      population: f.population ? fmtInt(f.population) : null,
      gdp_nominal: f.gdpNominalTotalUsd
        ? f.gdpNominalPerCapitaUsd
          ? t("gdp_total_pc", {
              total: "US$" + fmtInt(f.gdpNominalTotalUsd),
              pc: "US$" + fmtInt(f.gdpNominalPerCapitaUsd),
              year: f.gdpYear || "",
            })
          : t("gdp_total_only", { total: "US$" + fmtInt(f.gdpNominalTotalUsd) })
        : null,
      gdp_ppp: f.gdpPppTotalUsd
        ? f.gdpPppPerCapitaUsd
          ? t("gdp_pc_noyear", {
              total: "US$" + fmtInt(f.gdpPppTotalUsd),
              pc: "US$" + fmtInt(f.gdpPppPerCapitaUsd),
            })
          : t("gdp_total_only", { total: "US$" + fmtInt(f.gdpPppTotalUsd) })
        : null,
      currency: f.currencies,
      timezone: f.timezones,
    };
    // capital coordinates: small vendored dataset, no live fetch needed
    if (window.AtlasFacts && AtlasFacts.CAPITAL_COORDS && AtlasFacts.CAPITAL_COORDS[iso3]) {
      const [lon, lat] = AtlasFacts.CAPITAL_COORDS[iso3];
      const dirNS = (v) => i18n.t(v >= 0 ? "dir_n" : "dir_s");
      const dirEW = (v) => i18n.t(v >= 0 ? "dir_e" : "dir_w");
      values.capital_coord = Math.abs(lat).toFixed(2) + "°" + dirNS(lat) +
        " " + Math.abs(lon).toFixed(2) + "°" + dirEW(lon);
    }
    renderFacts(dl, factDefs, values, f);
  }

  function renderFacts(dl, factDefs, values, f) {
    dl.innerHTML = "";
    for (const [key, val] of factDefs) {
      const v = values && key in values ? values[key] : val;
      if (v == null || v === "") continue;
      const dt = document.createElement("dt");
      dt.textContent = i18n.t(key);
      const dd = document.createElement("dd");
      dd.textContent = String(v);
      dl.appendChild(dt);
      dl.appendChild(dd);
    }
    // flag + coat of arms images, each with its own visible caption
    if (f && (f.flag || f.arms)) {
      const dd = document.createElement("dd");
      dd.className = "emblems";
      if (f.flag) {
        const g = document.createElement("figure");
        g.appendChild(commonsImg(f.flag, "flag", 63));
        const cap = document.createElement("figcaption");
        cap.textContent = i18n.t("flag");
        g.appendChild(cap);
        dd.appendChild(g);
      }
      if (f.arms) {
        const g = document.createElement("figure");
        g.appendChild(commonsImg(f.arms, "arms", 80));
        const cap = document.createElement("figcaption");
        cap.textContent = i18n.t("arms");
        g.appendChild(cap);
        dd.appendChild(g);
      }
      const dt = document.createElement("dt");
      dt.textContent = i18n.t("emblems");
      dl.appendChild(dt);
      dl.appendChild(dd);
    }
    // leaders: grouped and labelled — head of state and head of
    // government each get their own label, so the role is always
    // identifiable even when Wikidata lacks the specific P39 title
    const groups = [];
    if (f && f.leaders && f.leaders.length) {
      groups.push({ label: "head_of_state", rows: f.leaders });
    }
    if (f && f.hog && f.hog.length) {
      groups.push({ label: "head_of_government", rows: f.hog });
    }
    for (const grp of groups) {
      const dt = document.createElement("dt");
      dt.textContent = i18n.t(grp.label);
      const dd = document.createElement("dd");
      for (const row of grp.rows) {
        const line = document.createElement("div");
        const key = row.title && row.since ? "leader_full"
          : row.title ? "leader_title"
          : row.since ? "leader_since" : null;
        line.textContent = key
          ? i18n.t(key, { title: row.title || "", name: row.name, since: row.since || "" })
          : row.name;
        dd.appendChild(line);
      }
      dl.appendChild(dt);
      dl.appendChild(dd);
    }
    if (!dl.children.length) {
      const dd = document.createElement("dd");
      dd.textContent = "—";
      dl.appendChild(dd);
    }
  }

  // Commons image via the stable FilePath redirect (renders SVG as PNG)
  function commonsImg(filename, kind, widthPx) {
    const name = filename.replace(/^File:/, "").replace(/ /g, "_");
    const img = document.createElement("img");
    img.src = "https://commons.wikimedia.org/wiki/Special:FilePath/" +
      encodeURIComponent(name) + "?width=" + widthPx;
    img.alt = kind;
    img.className = "emblem-" + kind;
    img.loading = "lazy";
    return img;
  }

  function nextLocate() {
    if (state.index >= state.order.length) return finishTest();
    const iso3 = state.order[state.index];
    $("#prompt-text").textContent = i18n.t("prompt_locate", { name: displayName(iso3) });
    state.locked = false;
  }

  function locateClick(iso3) {
    if (state.locked) return;
    const target = state.order[state.index];
    const c = country(iso3);
    if (!c) return; // clicked a country outside the lesson
    state.locked = true;
    map.clearOverlay();
    if (iso3 === target) {
      state.correct++;
      map.highlight(iso3, "correct");
    } else {
      map.highlight(iso3, "wrong");
      map.highlight(target, "correct");
      setHint(i18n.t("wrong", { name: displayName(target) }));
    }
    updateScore();
    setTimeout(() => {
      map.clearHighlights("correct");
      map.clearHighlights("wrong");
      state.index++;
      state.locked = false;
      nextLocate();
    }, 1200);
  }

  // "Reveal answer": show where the target country is (arrow + dot),
  // mark the round as wrong, and move on
  function revealAnswer() {
    if (state.locked || state.mode !== "locate") return;
    const target = state.order[state.index];
    if (!target) return;
    state.locked = true;
    map.rotateToFace(target);
    map.highlight(target, "correct");
    map.pointCountry(target);
    setTimeout(() => {
      map.clearHighlights("correct");
      map.clearOverlay();
      state.index++;
      state.locked = false;
      nextLocate();
    }, 2200);
  }

  // ---------- confusion groups ----------
  // Countries that are easily mixed up (geographic neighbours or
  // similar names). When quizzing a member of a group, all answer
  // options are drawn from the same group.
  const CONFUSION_GROUPS = [
    // Middle East
    ["ARE", "BHR", "EGY", "IRN", "IRQ", "ISR", "JOR", "KWT", "LBN",
      "OMN", "PSE", "QAT", "SAU", "SYR", "TUR", "YEM"],
    // North Africa
    ["DZA", "EGY", "LBY", "MAR", "TUN", "ESH"],
    // Southeast Asia
    ["BRN", "IDN", "KHM", "LAO", "MMR", "MYS", "PHL", "SGP", "THA",
      "TLS", "VNM"],
    // Caribbean
    ["ATG", "BHS", "BRB", "CUB", "DMA", "DOM", "GRD", "HTI", "JAM",
      "KNA", "LCA", "TTO", "VCT"],
    // Central Asian -stans
    ["AFG", "KAZ", "KGZ", "TJK", "TKM", "UZB"],
    // Nordic countries
    ["DNK", "FIN", "ISL", "NOR", "SWE"],
    // Central Europe (Slovakia/Slovenia cluster)
    ["AUT", "CZE", "HRV", "HUN", "SVK", "SVN"],
    // West Africa / Guinea belt
    ["GMB", "GNB", "GIN", "GNQ", "LBR", "SEN", "SLE"],
    // Guianas (French Guiana is a French department, not a country)
    ["GUY", "SUR"],
    // Congo pair + neighbours
    ["AGO", "CAF", "COG", "COD"],
    // Niger / Nigeria + neighbours (Chad->Niger confusion in tap data)
    ["CMR", "NER", "NGA", "TCD"],
    // Baltic states + neighbours
    ["BLR", "EST", "LTU", "LVA", "POL"],
    // Balkans
    ["ALB", "BIH", "BGR", "GRC", "MKD", "MNE", "SRB"],
    // Central America
    ["BLZ", "CRI", "GTM", "HND", "NIC", "PAN", "SLV"],
    // Southern Africa (Zambia confused with 5 different neighbours)
    ["AGO", "BWA", "COD", "MOZ", "NAM", "TZA", "ZMB", "ZWE"],
  ];

  function confusionGroup(iso3) {
    return CONFUSION_GROUPS.find((g) => g.includes(iso3)) || null;
  }

  function pickDistractors(iso3, pool) {
    // prefer same-group countries (harder); fall back to random
    const group = confusionGroup(iso3);
    const others = pool.filter((c) => c.iso3 !== iso3);
    if (group) {
      const inGroup = shuffle(others.filter((c) => group.includes(c.iso3)));
      if (inGroup.length >= 3) return inGroup.slice(0, 3);
      // not enough group members in this lesson: top up with randoms
      const rest = shuffle(others.filter((c) => !group.includes(c.iso3)));
      return [...inGroup, ...rest].slice(0, 3);
    }
    return shuffle(others).slice(0, 3);
  }

  function nextName() {
    if (state.index >= state.order.length) return finishTest();
    const iso3 = state.order[state.index];
    map.clearHighlights("highlighted");
    map.highlight(iso3, "highlighted");
    $("#prompt-text").textContent = state.answerStyle === "choice"
      ? i18n.t("prompt_name_choice")
      : i18n.t("prompt_name_text");

    const box = $("#answer-box");
    box.hidden = false;
    if (state.answerStyle === "choice") {
      $("#choices").innerHTML = "";
      $("#text-form").hidden = true;
      const distractors = pickDistractors(iso3, state.lesson.countries);
      const options = shuffle([country(iso3), ...distractors]);
      for (const opt of options) {
        const btn = document.createElement("button");
        btn.textContent = loc(opt.names);
        btn.addEventListener("click", () => nameAnswer(opt.iso3, btn));
        $("#choices").appendChild(btn);
      }
    } else {
      $("#choices").innerHTML = "";
      $("#text-form").hidden = false;
      const input = $("#text-input");
      input.value = "";
      input.focus();
    }
    state.locked = false;
  }

  function nameAnswer(chosenIso3, btnEl) {
    if (state.locked) return;
    const target = state.order[state.index];
    state.locked = true;
    if (chosenIso3 === target) {
      state.correct++;
      if (btnEl) btnEl.classList.add("correct");
      map.clearHighlights("highlighted");
      map.highlight(target, "correct");
    } else {
      if (btnEl) btnEl.classList.add("wrong");
      // reveal the right button
      [...$("#choices").querySelectorAll("button")].forEach((b) => {
        if (b.textContent === loc(country(target).names)) b.classList.add("correct");
      });
      setHint(i18n.t("wrong", { name: displayName(target) }));
    }
    updateScore();
    setTimeout(() => {
      map.clearHighlights("correct");
      state.index++;
      state.locked = false;
      nextName();
    }, 1200);
  }

  $("#text-form").addEventListener("submit", (ev) => {
    ev.preventDefault();
    if (state.locked || state.mode !== "name") return;
    const raw = $("#text-input").value;
    if (!raw.trim()) return;
    const target = state.order[state.index];
    const answers = acceptableAnswers(country(target));
    if (answers.has(normalizeAnswer(raw))) {
      state.correct++;
      map.clearHighlights("highlighted");
      map.highlight(target, "correct");
      updateScore();
      state.locked = true;
      setTimeout(() => {
        map.clearHighlights("correct");
        state.index++;
        state.locked = false;
        nextName();
      }, 800);
    } else {
      state.locked = true;
      setHint(i18n.t("wrong", { name: displayName(target) }));
      const input = $("#text-input");
      input.classList.add("wrong-input");
      setTimeout(() => {
        input.classList.remove("wrong-input");
        state.locked = false;
        input.focus();
      }, 700);
    }
  });

  function finishTest() {
    $("#answer-box").hidden = true;
    $("#prompt-text").textContent = i18n.t("finished", {
      correct: state.correct,
      total: state.order.length,
    });
    $("#score-display").textContent = "";
    setHint("");
    state.order = [];
  }

  // ---------- wiring ----------

  async function init() {
    i18n.setLocale(i18n.locale);
    $("#projection-select").value = state.projection;
    map.init($("#map"));
    map.attachNavigation();
    fillLessonSelect();
    // Wikidata maps for the live facts popup
    try {
      if (window.ATLAS_QID_MAP) {
        AtlasFacts.ISO3_TO_QID = window.ATLAS_QID_MAP;
        AtlasFacts.CAPITAL_COORDS = window.ATLAS_CAPITAL_COORDS || {};
      } else {
        const [qidMap, capCoords] = await Promise.all([
          fetch("data/iso3-to-qid.json").then((r) => r.json()),
          fetch("data/capital-coords.json").then((r) => r.json()),
        ]);
        AtlasFacts.ISO3_TO_QID = qidMap;
        AtlasFacts.CAPITAL_COORDS = capCoords;
      }
    } catch (e) {
      // facts popup falls back to lesson facts only
    }

    $("#mode-select").addEventListener("change", (ev) => {
      state.mode = ev.target.value;
      if (state.lesson) startMode();
    });
    $("#answer-style-select").addEventListener("change", () => {
      if (state.mode === "name" && state.lesson) {
        state.answerStyle = $("#answer-style-select").value;
        nextName(); // re-ask current question in new style — index unchanged
      }
    });
    $("#locale-select").addEventListener("change", (ev) => {
      i18n.setLocale(ev.target.value);
      refreshLessonTitles();
      if (state.lesson) startMode();
      // re-render an open info panel in the new locale (facts are
      // cached; labels re-fetch per language chain)
      const iso3 = $("#info-name").dataset.iso3;
      if (iso3 && state.lesson) {
        const c = country(iso3);
        if (c) showInfo(c, iso3);
      }
    });
    $("#projection-select").addEventListener("change", (ev) => {
      state.projection = ev.target.value;
      localStorage.setItem("atlas.projection", state.projection);
      if (state.lesson) startMode();
    });
    $("#reset-view-button").addEventListener("click", () => map.resetView());
    $("#reveal-button").addEventListener("click", revealAnswer);
    $("#restart-button").addEventListener("click", () => {
      state.visited = null;
      if (state.lesson) startMode();
    });
    $("#info-close").addEventListener("click", () => { $("#info-panel").hidden = true; });

    map.loadWorld()
      .then(() => loadLesson(LESSONS[0].file))
      .then(refreshLessonTitles)
      .catch((err) => {
        setHint("Error: " + err.message +
          " — serve the app over HTTP (e.g. python3 -m http.server), not file://");
      });
  }

  document.addEventListener("DOMContentLoaded", init);
})();
