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

  // ---------- preferences cookie ----------
  // One JSON cookie remembers locale/lesson/mode/view/projection so a
  // revisit restores the session. localStorage values (locale,
  // projection) remain as fallback: some browsers do not persist
  // cookies for file:// pages.
  const PREFS_COOKIE = "atlas.prefs";
  function readPrefs() {
    // Chromium (and others) block document.cookie on file:// pages, so
    // prefs are mirrored into localStorage; on http(s) the cookie wins
    const raw = (document.cookie.match(/(?:^|;\s*)atlas\.prefs=([^;]*)/) || [])[1];
    if (raw) {
      try { return JSON.parse(decodeURIComponent(raw)) || {}; } catch (e) { /* bad cookie */ }
    }
    const ls = localStorage.getItem("atlas.prefs");
    if (ls) {
      try { return JSON.parse(ls) || {}; } catch (e) { /* bad value */ }
    }
    return {};
  }
  function writePrefs(patch) {
    const next = Object.assign(readPrefs(), patch);
    const val = encodeURIComponent(JSON.stringify(next));
    document.cookie = PREFS_COOKIE + "=" + val +
      "; max-age=31536000; path=/; SameSite=Lax";
    try { localStorage.setItem("atlas.prefs", decodeURIComponent(val)); } catch (e) { /* quota */ }
  }

  const state = {
    lesson: null,
    mode: "learn",
    answerStyle: "choice",
    projection: readPrefs().projection || localStorage.getItem("atlas.projection") || "equirectangular",
    order: [],          // shuffled iso3 list for tests
    index: 0,
    correct: 0,
    locked: false,
    journeyView: "explore", // "explore" | "step"
    stepIdx: null,
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
    { file: "lessons/magellan/voyage.json" },
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
    // keep the dropdown in sync (init may load a saved lesson directly)
    const selEl = $("#lesson-select");
    if (selEl.value !== file) selEl.value = file;
    state.visitedStops = null;
    state.focusedStop = null;
    state.stepIdx = null;
    state.journeyView = (data.type === "journey" && readPrefs().journeyView === "step") ? "step" : "explore";
    $("#journey-view-select").value = state.journeyView;
    $("#journey-view-row").hidden = data.type !== "journey";
    writePrefs({ lesson: file });
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

  function quizTotal() {
    if (state.mode === "route") return state.lesson.stops.length - 1;
    if (state.mode === "sights") return state.lesson.stops.length;
    return state.order.length;
  }

  function updateScore() {
    $("#score-display").textContent =
      i18n.t("score", { correct: state.correct, total: quizTotal() });
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
    // cancel any pending quiz advance from a previous mode
    if (state.quizTimer) { clearTimeout(state.quizTimer); state.quizTimer = null; }
    // journey lessons have their own test modes; the country locate /
    // name tests don't apply to them
    const isJourney = state.lesson.type === "journey";
    for (const opt of $("#mode-select").options) {
        const journeyOnly = opt.value === "route" || opt.value === "sights";
        const countryOnly = ["locate", "name"].includes(opt.value);
        opt.hidden = isJourney ? countryOnly : journeyOnly;
    }
    // if the saved mode is now hidden, fall back to learn
    if ($("#mode-select").selectedOptions[0] && $("#mode-select").selectedOptions[0].hidden) {
      $("#mode-select").value = "learn";
      state.mode = "learn";
    }

    map.clearOverlay();
    map.clearRevealed();
    map.clearHighlights("correct");
    map.clearHighlights("wrong");
    map.clearHighlights("highlighted");
    map.resetView();
    $("#info-panel").hidden = true;
    $("#info-panel").classList.toggle("journey",
      state.mode === "learn" && state.lesson.type === "journey");
    const journeyLearn = state.mode === "learn" && state.lesson.type === "journey";
    const isQuiz = ["locate", "name", "route", "sights"].includes(state.mode);
    $("#prompt-bar").hidden = isQuiz ? false : (!journeyLearn || state.journeyView !== "step");
    $("#journey-controls").hidden = !journeyLearn;
    if (journeyLearn) {
      $("#journey-prev").hidden = false;
      $("#journey-next").hidden = false;
      $("#prompt-text").textContent = "";
      $("#score-display").textContent = "";
    }
    $("#answer-box").hidden = true;
    $("#answer-style-row").hidden = state.mode !== "name";

    map.render(state.lesson, { projection: state.projection });

    if (state.mode === "learn") {
      setHint(state.projection === "globe" ? i18n.t("hint_globe") : i18n.t("hint_learn"));
      if (state.lesson.type === "journey") {
        // journey learn mode: only the stop dots are interactive
        map.setClickHandler(() => {});
      } else {
        map.setClickHandler((iso3) => learnClick(iso3, false));
      }
      if (!state.visited) state.visited = new Set();
      renderCountryList();
      if (state.lesson.type === "journey") renderJourney();
    } else {
      $("#country-list-panel").hidden = true;
      state.locked = false;
      if (state.mode === "route" || state.mode === "sights") {
        // journey quiz modes: no country list, no reveal button
        $("#reveal-button").hidden = true;
        map.setClickHandler(() => {});
        setHint(state.projection === "globe" ? i18n.t("hint_globe") : "");
        state.index = 0;
        state.correct = 0;
        state.quizOrder = shuffle(state.lesson.stops.map((_, i) => i));
        if (state.mode === "route") startRouteQuiz();
        else startSightsQuiz();
        updateScore();
        return;
      }
      state.order = shuffle((state.lesson.countries || []).map((c) => c.iso3));
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
    // journey lessons render their stop list instead (renderJourneySidebar)
    if (state.lesson.type === "journey") { panel.hidden = false; return; }
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
    if (state.journeyView === "step") {
      renderJourneyStepMode();
      renderJourneySidebar(true);
      return;
    }
    renderJourneyRoutes();
    map.renderStopDots(L.stops, state.stepIdx ?? null, (idx) => {
      const s = L.stops[idx];
      if (s) journeyStopClick(s);
    });
    renderJourneySidebar(false);
  }

  function renderJourneySidebar(numbered) {
    const L = state.lesson;
    // stops sidebar replaces the alphabetical country list
    const ul = $("#country-list");
    ul.innerHTML = "";
    ul.classList.add("journey-order");
    L.stops.forEach((s, i) => {
      const li = document.createElement("li");
      li.dataset.stop = s.id;
      li.dataset.idx = i;
      if (state.visitedStops && state.visitedStops.has(s.id)) li.classList.add("visited");
      if (numbered) {
        const no = document.createElement("span");
        no.className = "stop-no";
        no.textContent = String(i + 1).padStart(2, "0");
        li.append(no, document.createTextNode(" "));
      }
      const yr = document.createElement("span");
      yr.className = "stop-year";
      yr.textContent = s.year;
      const nm = document.createElement("span");
      nm.textContent = loc(s.names) || s.id;
      li.append(yr, document.createTextNode(" "), nm);
      li.addEventListener("click", () => journeyStopClick(s, i));
      ul.appendChild(li);
    });
    $("#country-list-panel h2").textContent = i18n.t("stops");
  }

  function renderJourneyRoutes() {
    const L = state.lesson;
    if (L.voyage) {
      map.addSeaRoute(L.route_out, "#ffd24a");
      if (L.route_back) map.addSeaRoute(L.route_back, "#e05674");
    } else {
      map.addArrow(L.route_out, "#ffd24a");
      map.addArrow(L.route_back, "#e05674");
    }
  }

  // explore mode: click on a dot / sidebar entry
  function journeyStopClick(s, idx) {
    if (!state.visitedStops) state.visitedStops = new Set();
    state.visitedStops.add(s.id);
    state.focusedStop = s.id;
    const li = (idx != null)
      ? document.querySelector(`#country-list li[data-idx="${idx}"]`)
      : document.querySelector(`#country-list li[data-stop="${s.id}"]`);
    if (li) li.classList.add("visited");
    map.focusStopDot(idx != null ? idx : L_indexOf(s));
    map.rotateToCoord(s.coords);
    map.pointAt(s.coords);
    showStopInfo(s);
    if (s.iso3) {
      map.reveal(s.iso3);
      map.setCurrent(s.iso3);
    }
  }

  function L_indexOf(s) {
    return state.lesson.stops.indexOf(s);
  }

  // ----- step-through mode -----
  // journeyView: "explore" (default, everything visible) or "step"
  // (only stops visited so far; segments drawn/undrawn one hop at a
  // time with the buttons / arrow keys)
  function renderJourneyStepMode() {
    const L = state.lesson;
    if (state.stepIdx == null) state.stepIdx = 0;
    map.renderStopDots(
      L.stops.slice(0, state.stepIdx + 1).map((s) => ({ ...s })),
      state.stepIdx,
      (idx) => {
        // clicking an earlier dot in step mode jumps to that step
        journeyStep(idx, true);
      }
    );
    // segments between consecutive visited stops
    for (let i = 0; i < state.stepIdx; i++) {
      const seg = map.addSegment(L.stops[i].coords, L.stops[i + 1].coords, colorOf(i, L), "static");
      if (seg) seg.dataset.hop = i;
    }
    updateStepUI();
  }

  function colorOf(i, L) {
    // stops after nalanda (last outbound) use the return color
    const nIdx = L.stops.findIndex((s) => s.id === "nalanda");
    return i >= nIdx ? "#e05674" : "#ffd24a";
  }

  function journeyStep(deltaOrIdx, absolute = false) {
    const L = state.lesson;
    const max = L.stops.length - 1;
    let next = absolute ? deltaOrIdx : (state.stepIdx ?? 0) + deltaOrIdx;
    next = Math.max(0, Math.min(max, next));
    const prev = state.stepIdx ?? 0;
    if (next === prev) { updateStepUI(); return; }
    if (next > prev) {
      // advance: draw segment prev->next (could be multiple hops via
      // dot click; draw each hop)
      for (let i = prev; i < next; i++) {
        const seg = map.addSegment(L.stops[i].coords, L.stops[i + 1].coords, colorOf(i, L));
        if (seg) seg.dataset.hop = i;
      }
      fadeDotIn(next);
    } else {
      // step back: erase segments down to next and drop dots beyond it
      for (let i = next; i < prev; i++) {
        removeSegment(i);
      }
      // re-render dots limited to next (drops later dots)
      map.renderStopDots(
        L.stops.slice(0, next + 1).map((s) => ({ ...s })),
        next,
        (i) => journeyStep(i, true)
      );
    }
    state.stepIdx = next;
    const s = L.stops[next];
    if (!state.visitedStops) state.visitedStops = new Set();
    state.visitedStops.add(s.id);
    const li = document.querySelector(`#country-list li[data-idx="${next}"]`);
    if (li) li.classList.add("visited");
    map.rotateToCoord(s.coords);
    map.focusStopDot(next);
    showStopInfo(s);
    syncSidebarActive(next);
    updateStepUI();
  }

  function fadeDotIn(idx) {
    // dot for stop idx appears (created if needed) and takes focus
    const L = state.lesson;
    // ensure dot exists: easiest is re-rendering dots up to idx
    map.renderStopDots(
      L.stops.slice(0, idx + 1).map((s) => ({ ...s })),
      idx,
      (i) => journeyStep(i, true)
    );
  }

  function removeSegment(i) {
    // erase the segment hop i -> i+1 with the shorten-back animation
    const seg = document.querySelector(`#map path.segment[data-hop="${i}"]`);
    if (!seg) return;
    seg.dataset.hop = i; // already set at creation
    const len = seg.getTotalLength();
    seg.style.strokeDasharray = len;
    seg.style.strokeDashoffset = 0;
    seg.getBoundingClientRect();
    seg.style.transition = "stroke-dashoffset 0.6s linear";
    seg.style.strokeDashoffset = String(len);
    setTimeout(() => seg.remove(), 650);
  }

  function syncSidebarActive(idx) {
    for (const li of document.querySelectorAll("#country-list li")) {
      li.classList.toggle("active", Number(li.dataset.idx) === idx);
    }
  }

  function updateStepUI() {
    const L = state.lesson;
    const idx = state.stepIdx ?? 0;
    const prevB = $("#journey-prev"), nextB = $("#journey-next");
    if (prevB) prevB.disabled = idx === 0;
    if (nextB) nextB.disabled = idx >= L.stops.length - 1;
    const counter = $("#journey-counter");
    if (counter) counter.textContent = `${idx + 1} / ${L.stops.length}`;
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
    addRow(i18n.t("year"), loc(s.when) || s.year);
    if (s.present) addRow(i18n.t("today_at"), loc(s.present) || s.present["en"] || "");
    // journey lessons like Magellan's have no `countries` list — only
    // Xuanzang-style lessons carry it; guard or the whole infobox dies
    // before reaching the narrative paragraphs
    const country = (state.lesson.countries || []).find((c) => c.iso3 === s.iso3);
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

  // ---------- journey quiz: guess the route ----------
  // From the current stop, guess the next stop's year AND place from
  // 3-4 options. Wrong answers vary: right place + wrong year, wrong
  // place + right year, or both wrong. Wrong places come from real
  // 7th-century polities near the route (lesson.quizPlaces) or real
  // stops that are not the answer; wrong years are the correct year
  // nudged by 1-3 years.
  function stopLabel(s) {
    return loc(s.names) + " (" + s.year + ")";
  }

  function routeYearVariants(year) {
    const y = Number(String(year).replace(/[^0-9]/g, "").slice(0, 4)) || 630;
    // keep variants within +-3 of the real year (never before the
    // departure year, which we take from the lesson's first stop)
    const firstYear = Number(String(state.lesson.stops[0].year)
      .replace(/[^0-9]/g, "").slice(0, 4)) || y - 5;
    const lastYear = Number(String(
      state.lesson.stops[state.lesson.stops.length - 1].year)
      .replace(/[^0-9]/g, "").slice(0, 4)) || y + 5;
    const out = new Set();
    let guard = 0;
    while (out.size < 3 && guard++ < 30) {
      const d = (Math.floor(Math.random() * 3) + 1) * (Math.random() < 0.5 ? -1 : 1);
      const v = y + d;
      if (v >= firstYear && v <= lastYear && v !== y) out.add(v);
    }
    return [...out];
  }

  function startRouteQuiz() {
    state.routeIdx = 0;
    nextRouteQuestion();
  }

  function nextRouteQuestion() {
    const L = state.lesson;
    const stops = L.stops;
    if (state.routeIdx >= stops.length - 1) return finishTest();
    const cur = stops[state.routeIdx];
    const nxt = stops[state.routeIdx + 1];
    map.clearOverlay();
    // show progress so far: dots up to current stop + static segments
    map.renderStopDots(stops.slice(0, state.routeIdx + 1), state.routeIdx, () => {});
    for (let i = 0; i < state.routeIdx; i++) {
      map.addSegment(stops[i].coords, stops[i + 1].coords, routeColor(i, stops), "static");
    }
    map.rotateToCoord(cur.coords);
    setHint("");
    $("#prompt-text").textContent = i18n.t("prompt_route",
      { name: loc(cur.names), year: cur.year,
        traveler: loc(L.traveler) || "he" });

    // answer options: always [correct, place-right-year-wrong,
    // place-wrong-year-right, maybe place-wrong-year-wrong]
    const mkOpt = (stop, year, correct) => ({
      correct,
      labelHtml: `<span class="quiz-place"></span><span class="quiz-year"></span>`,
      stop, year,
    });
    const opts = [mkOpt(nxt, nxt.year, true)];
    const wrongYears = routeYearVariants(nxt.year);
    if (wrongYears.length) {
      opts.push(mkOpt(nxt, String(wrongYears[0]), false)); // year-only wrong
    }
    const wrongPlaces = routeDistractorPlaces(nxt, L);
    const yRight = wrongPlaces[0];
    if (yRight) opts.push(mkOpt(yRight, nxt.year, false)); // place-only wrong
    const both = wrongPlaces[1];
    if (both && wrongYears[1]) {
      opts.push(mkOpt(both, String(wrongYears[1]), false)); // both wrong
    }
    renderQuizChoices(shuffle(opts), (opt, btn) => routeAnswer(opt, btn, nxt), true);
  }

  // plausible wrong places: other real stops ±3 away (not adjacent),
  // plus the historical distractor polities from the lesson data
  function routeDistractorPlaces(nxt, L) {
    const idx = L.stops.indexOf(nxt);
    const near = L.stops.filter((s, i) =>
      Math.abs(i - idx) >= 2 && Math.abs(i - idx) <= 8);
    const pool = [...shuffle(near).slice(0, 3)];
    const extras = (L.quizPlaces || []).map((p) => ({
      names: p.names, year: p.year, pseudo: p,
    }));
    let guard = 0;
    while (pool.length < 3 && guard++ < 40) {
      const e = extras[Math.floor(Math.random() * extras.length)];
      if (e && !pool.includes(e)) pool.push(e);
      else if (!extras.length) break;
    }
    return shuffle(pool).slice(0, 3);
  }

  // lesson-specific return-color split: Xuanzang turns at Nalanda,
  // Magellan's fleet turns at Tidore
  function routeColor(i, stops) {
    const pivot = stops.findIndex((s) =>
      s.id === "nalanda" || s.id === "tidore");
    return i >= pivot ? "#e05674" : "#ffd24a";
  }

  function routeAnswer(opt, btn, nxt) {
    if (state.locked) return;
    state.locked = true;
    const L = state.lesson;
    if (opt.correct) {
      state.correct++;
      btn.classList.add("correct");
      // animate the line to the next stop, then fade in its dot
      const seg = map.addSegment(L.stops[state.routeIdx].coords, nxt.coords,
        routeColor(state.routeIdx, L.stops));
      if (seg) seg.dataset.hop = state.routeIdx;
      const stops = L.stops.slice(0, state.routeIdx + 2);
      state.quizTimer = setTimeout(() => {
        map.renderStopDots(stops, state.routeIdx + 1, () => {});
      }, 800);
    } else {
      btn.classList.add("wrong");
      [...$("#choices").querySelectorAll("button")].forEach((b) => {
        if (b.dataset.correct === "1") b.classList.add("correct");
      });
      setHint(i18n.t("wrong_route"));
    }
    updateScore();
    state.quizTimer = setTimeout(() => {
      state.routeIdx++;
      state.locked = false;
      nextRouteQuestion();
    }, 1400);
  }

  // ---------- journey quiz: guess the sights ----------
  // A stop is highlighted (rotated + pulsing dot); pick what Xuanzang
  // saw / did / what was happening there. Distractors are sights from
  // other stops (weighted to ±5 stops so they're not obvious).
  function startSightsQuiz() {
    state.index = 0;
    nextSightsQuestion();
  }

  function nextSightsQuestion() {
    const L = state.lesson;
    if (state.index >= state.quizOrder.length) return finishTest();
    const idx = state.quizOrder[state.index];
    const s = L.stops[idx];
    map.clearOverlay();
    map.renderStopDots([s], 0, () => {});
    map.rotateToCoord(s.coords);
    setHint("");
    $("#prompt-text").textContent = i18n.t("prompt_sights",
      { name: loc(s.names), year: s.year,
        traveler: loc(state.lesson.traveler) || "he" });

    const sights = L.quizSights || {};
    const fact = sights[s.id];
    if (!fact) { state.index++; return nextSightsQuestion(); }
    const correct = { text: loc(fact), correct: true };
    // distractors: sights of other stops, nearest stops preferred
    const others = L.stops
      .map((o, i) => ({ o, i, d: Math.abs(i - idx) }))
      .filter((x) => x.i !== idx && sights[x.o.id])
      .sort((a, b) => a.d - b.d);
    const near = others.slice(0, 10);
    const picked = shuffle(near).slice(0, 3).map((x) =>
      ({ text: loc(sights[x.o.id]), correct: false }));
    renderQuizChoices(shuffle([correct, ...picked]), (opt, btn) => {
      if (state.locked) return;
      state.locked = true;
      if (opt.correct) {
        state.correct++;
        btn.classList.add("correct");
      } else {
        btn.classList.add("wrong");
        [...$("#choices").querySelectorAll("button")].forEach((b) => {
          if (b.dataset.correct === "1") b.classList.add("correct");
        });
        // show the real story in the hint
        setHint(i18n.t("sights_answer", { fact: loc(fact) }));
      }
      updateScore();
      state.quizTimer = setTimeout(() => {
        state.index++;
        state.locked = false;
        nextSightsQuestion();
      }, opt.correct ? 900 : 3200);
    });
  }

  // shared choice-button rendering for the journey quizzes; route mode
  // renders a two-line label (place + year), sights mode plain text
  function renderQuizChoices(options, onPick, routeStyle) {
    const box = $("#answer-box");
    box.hidden = false;
    $("#choices").innerHTML = "";
    $("#text-form").hidden = true;
    for (const opt of options) {
      const btn = document.createElement("button");
      btn.dataset.correct = opt.correct ? "1" : "0";
      if (routeStyle) {
        const place = document.createElement("div");
        place.className = "quiz-place";
        place.textContent = loc(opt.stop.names);
        const year = document.createElement("div");
        year.className = "quiz-year";
        year.textContent = opt.year;
        btn.append(place, year);
      } else {
        btn.textContent = opt.text;
      }
      btn.addEventListener("click", () => onPick(opt, btn));
      $("#choices").appendChild(btn);
    }
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
      total: quizTotal(),
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
      writePrefs({ mode: state.mode });
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
      writePrefs({ locale: ev.target.value });
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
      writePrefs({ projection: state.projection });
      if (state.lesson) startMode();
    });
    $("#reset-view-button").addEventListener("click", () => map.resetView());
    $("#reveal-button").addEventListener("click", revealAnswer);
    // journey view toggle: explore (all visible) vs step (one at a time)
    $("#journey-view-select").addEventListener("change", (ev) => {
      state.journeyView = ev.target.value;
      writePrefs({ journeyView: state.journeyView });
      state.stepIdx = state.journeyView === "step" ? 0 : null;
      map.clearOverlay();
      if (state.journeyView === "step") {
        const s = state.lesson.stops[0];
        if (!state.visitedStops) state.visitedStops = new Set();
        state.visitedStops.add(s.id);
        renderJourney();
        showStopInfo(s);
        map.focusStopDot(0);
      } else {
        renderJourney();
      }
      $("#prompt-bar").hidden = state.journeyView !== "step";
    });
    $("#journey-prev").addEventListener("click", () => journeyStep(-1));
    $("#journey-next").addEventListener("click", () => journeyStep(1));
    document.addEventListener("keydown", (ev) => {
      if (state.mode !== "learn" || !state.lesson ||
          state.lesson.type !== "journey" || state.journeyView !== "step") return;
      if (ev.target.tagName === "SELECT" || ev.target.tagName === "INPUT") return;
      if (ev.key === "ArrowRight") { ev.preventDefault(); journeyStep(1); }
      else if (ev.key === "ArrowLeft") { ev.preventDefault(); journeyStep(-1); }
    });
    $("#restart-button").addEventListener("click", () => {
      state.visited = null;
      if (state.lesson) startMode();
    });
    $("#info-close").addEventListener("click", () => { $("#info-panel").hidden = true; });

    // restore saved session (cookie) + ?lang= override.
    // ?lang must be one of the locale-select option values (en-GB,
    // fr-CA, zh-Hans, zh-HK, ja); it wins over the saved preference
    // and persists as the new preference.
    const urlLang = new URLSearchParams(location.search).get("lang");
    const prefs = readPrefs();
    const savedLocale = urlLang && i18n.locales.includes(urlLang)
      ? urlLang
      : (prefs.locale || localStorage.getItem("atlas.locale") || "en-GB");
    i18n.setLocale(savedLocale);
    $("#locale-select").value = i18n.locale;
    if (prefs.mode && ["learn", "locate", "name"].includes(prefs.mode)) {
      state.mode = prefs.mode;
      $("#mode-select").value = prefs.mode;
    }
    if (prefs.projection) $("#projection-select").value = prefs.projection;

    map.loadWorld()
      .then(() => loadLesson(
        (prefs.lesson && LESSONS.some((l) => l.file === prefs.lesson))
          ? prefs.lesson
          : LESSONS[0].file))
      .then(refreshLessonTitles)
      .catch((err) => {
        setHint("Error: " + err.message +
          " — serve the app over HTTP (e.g. python3 -m http.server), not file://");
      });
  }

  document.addEventListener("DOMContentLoaded", init);
})();
