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
  ];

  async function loadLesson(file) {
    const res = await fetch(file);
    if (!res.ok) throw new Error(`failed to load ${file}: ${res.status}`);
    state.lesson = await res.json();
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
      fetch(l.file)
        .then((r) => r.json())
        .then((j) => {
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
      map.setClickHandler((iso3) => learnClick(iso3));
    } else {
      state.order = shuffle(state.lesson.countries.map((c) => c.iso3));
      state.index = 0;
      state.correct = 0;
      state.locked = false;
      if (state.mode === "locate") {
        setHint(state.projection === "globe" ? i18n.t("hint_globe") : i18n.t("hint_locate"));
        map.setClickHandler((iso3) => locateClick(iso3));
        nextLocate();
      } else {
        state.answerStyle = $("#answer-style-select").value;
        setHint(state.projection === "globe" ? i18n.t("hint_globe") : i18n.t("hint_name"));
        map.setClickHandler(() => {});
        nextName();
      }
      updateScore();
    }
  }

  function learnClick(iso3) {
    const c = country(iso3);
    if (!c) return; // country not part of this lesson; ignore
    map.reveal(iso3);
    showInfo(c, iso3);
  }

  function showInfo(c, iso3) {
    $("#info-panel").hidden = false;
    $("#info-name").textContent = loc(c.names) || iso3;
    const dl = $("#info-facts");
    dl.innerHTML = "";
    const factDefs = [
      ["population", c.facts && c.facts.population],
      ["capital", c.facts && c.facts.capital],
      ["demonym", c.facts && c.facts.demonym],
      ["founded", c.facts && c.facts.founded],
      ["collapsed", c.facts && c.facts.collapsed],
    ];
    for (const [key, val] of factDefs) {
      if (val == null || val === "") continue;
      const dt = document.createElement("dt");
      dt.textContent = i18n.t(key);
      const dd = document.createElement("dd");
      dd.textContent = String(val);
      dl.appendChild(dt);
      dl.appendChild(dd);
    }
    if (!dl.children.length) {
      const dd = document.createElement("dd");
      dd.textContent = "—";
      dl.appendChild(dd);
    }
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

  function init() {
    i18n.setLocale(i18n.locale);
    $("#projection-select").value = state.projection;
    map.init($("#map"));
    map.attachNavigation();
    fillLessonSelect();

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
    });
    $("#projection-select").addEventListener("change", (ev) => {
      state.projection = ev.target.value;
      localStorage.setItem("atlas.projection", state.projection);
      if (state.lesson) startMode();
    });
    $("#reset-view-button").addEventListener("click", () => map.resetView());
    $("#restart-button").addEventListener("click", () => {
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
