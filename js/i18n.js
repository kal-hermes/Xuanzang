/* i18n.js — locale dictionaries and formatting.
 * Locale data in lessons carries full localized strings; the UI chrome
 * strings live here. Country display names come from lesson data
 * (lesson.data.countries[id].names[locale]) so the creator skill owns
 * localized content end-to-end.
 */
(function () {
  "use strict";

  const UI_STRINGS = {
    "en-GB": {
      lesson: "Lesson",
      mode: "Mode",
      mode_learn: "Learn",
      mode_locate: "Locate the country",
      mode_name: "Name the country",
      language: "Language",
      answer_style: "Answer",
      answer_choice: "Multiple choice",
      answer_text: "Type the name",
      restart: "Restart",
      submit: "Check",
      close: "Close",
      hint_learn: "Click a country to reveal its name and facts.",
      hint_locate: "Click the country you think matches the prompt.",
      hint_name: "Click the highlighted country, then answer.",
      prompt_locate: "Where is {name}?",
      prompt_name_choice: "Which country is highlighted?",
      prompt_name_text: "Name the highlighted country.",
      correct: "Correct!",
      wrong: "Not quite — this is {name}.",
      score: "Score: {correct}/{total}",
      finished: "Finished! Final score: {correct}/{total}",
      no_lesson: "No lesson selected.",
      population: "Population",
      capital: "Capital",
      demonym: "Demonym",
      founded: "Founded",
      collapsed: "Collapsed",
      "projection": "Projection",
      "proj_equirectangular": "Equirectangular",
      "proj_mercator": "Mercator",
      "proj_naturalEarth": "Natural Earth",
      "proj_robinson": "Robinson",
      "proj_globe": "3D Globe",
      "hint_globe": "Drag to rotate the globe; scroll to zoom.",
      "reset_view": "⟲",
      "languages": "Official languages",
      "government": "Government",
      "established": "Established",
      "area": "Area",
      "gdp_nominal": "GDP (nominal)",
      "gdp_ppp": "GDP (PPP)",
      "currency": "Currency",
      "timezone": "Time zone",
      "emblems": "Emblems",
      "leaders": "Leaders",
      "capital_coord": "Capital coordinates",
      "reset_view_title": "Reset map view"
    },
    "fr-CA": {
      lesson: "Leçon",
      mode: "Mode",
      mode_learn: "Apprendre",
      mode_locate: "Localiser le pays",
      mode_name: "Nommer le pays",
      language: "Langue",
      answer_style: "Réponse",
      answer_choice: "Choix multiples",
      answer_text: "Taper le nom",
      restart: "Recommencer",
      submit: "Vérifier",
      close: "Fermer",
      hint_learn: "Cliquez sur un pays pour révéler son nom et ses informations.",
      hint_locate: "Cliquez sur le pays correspondant à la consigne.",
      hint_name: "Cliquez sur le pays surligné, puis répondez.",
      prompt_locate: "Où se trouve {name} ?",
      prompt_name_choice: "Quel pays est surligné ?",
      prompt_name_text: "Nommez le pays surligné.",
      correct: "Exact !",
      wrong: "Pas tout à fait — c'est {name}.",
      score: "Score : {correct}/{total}",
      finished: "Terminé ! Score final : {correct}/{total}",
      no_lesson: "Aucune leçon sélectionnée.",
      population: "Population",
      capital: "Capitale",
      demonym: "Gentilé",
      founded: "Fondation",
      collapsed: "Disparition",
      "projection": "Projection",
      "proj_equirectangular": "Équirectangulaire",
      "proj_mercator": "Mercator",
      "proj_naturalEarth": "Natural Earth",
      "proj_robinson": "Robinson",
      "proj_globe": "Globe 3D",
      "hint_globe": "Faites glisser pour faire pivoter le globe; molette pour zoomer.",
      "reset_view": "⟲",
      "languages": "Langues officielles",
      "government": "Régime",
      "established": "Fondation",
      "area": "Superficie",
      "gdp_nominal": "PIB (nominal)",
      "gdp_ppp": "PIB (PPA)",
      "currency": "Monnaie",
      "timezone": "Fuseau horaire",
      "emblems": "Emblèmes",
      "leaders": "Dirigeants",
      "capital_coord": "Coordonnées de la capitale",
      "reset_view_title": "Réinitialiser la vue"
    },
    "zh-Hans": {
      lesson: "课程",
      mode: "模式",
      mode_learn: "学习",
      mode_locate: "找国家",
      mode_name: "认国家",
      language: "语言",
      answer_style: "作答方式",
      answer_choice: "选择题",
      answer_text: "输入名称",
      restart: "重新开始",
      submit: "检查",
      close: "关闭",
      hint_learn: "点击国家即可显示名称及资料。",
      hint_locate: "点击你认为符合提示的国家。",
      hint_name: "点击高亮的国家，然后作答。",
      prompt_locate: "{name} 在哪里？",
      prompt_name_choice: "高亮的是哪个国家？",
      prompt_name_text: "请说出高亮国家的名称。",
      correct: "答对了！",
      wrong: "不对哦——这是{name}。",
      score: "得分：{correct}/{total}",
      finished: "完成！最终得分：{correct}/{total}",
      no_lesson: "未选择课程。",
      population: "人口",
      capital: "首都",
      demonym: "国民称呼",
      founded: "建立",
      collapsed: "灭亡",
      "projection": "投影",
      "proj_equirectangular": "等距圆柱",
      "proj_mercator": "墨卡托",
      "proj_naturalEarth": "自然地球",
      "proj_robinson": "罗宾森",
      "proj_globe": "3D 地球仪",
      "hint_globe": "拖动旋转地球仪；滚轮缩放。",
      "reset_view": "⟲",
      "languages": "官方语言",
      "government": "政体",
      "established": "成立",
      "area": "面积",
      "gdp_nominal": "GDP（名义）",
      "gdp_ppp": "GDP（购买力平价）",
      "currency": "货币",
      "timezone": "时区",
      "emblems": "徽章",
      "leaders": "领导人",
      "capital_coord": "首都坐标",
      "reset_view_title": "重置地图视图"
    },
    "zh-HK": {
      lesson: "課程",
      mode: "模式",
      mode_learn: "學習",
      mode_locate: "搵國家",
      mode_name: "認國家",
      language: "語言",
      answer_style: "作答方式",
      answer_choice: "選擇題",
      answer_text: "輸入名稱",
      restart: "重新開始",
      submit: "檢查",
      close: "關閉",
      hint_learn: "點擊國家即可顯示名稱及資料。",
      hint_locate: "點擊你認為符合提示嘅國家。",
      hint_name: "點擊高亮嘅國家，然後作答。",
      prompt_locate: "{name} 喺邊度？",
      prompt_name_choice: "高亮嘅係邊個國家？",
      prompt_name_text: "請講出高亮國家嘅名稱。",
      correct: "答啱咗！",
      wrong: "唔啱——呢個係{name}。",
      score: "得分：{correct}/{total}",
      finished: "完成！最終得分：{correct}/{total}",
      no_lesson: "未選擇課程。",
      population: "人口",
      capital: "首都",
      demonym: "國民稱呼",
      founded: "建立",
      collapsed: "滅亡",
      "projection": "投影",
      "proj_equirectangular": "等距圓柱",
      "proj_mercator": "麥卡托",
      "proj_naturalEarth": "自然地球",
      "proj_robinson": "羅賓森",
      "proj_globe": "3D 地球儀",
      "hint_globe": "拖動旋轉地球儀；滾輪縮放。",
      "reset_view": "⟲",
      "languages": "官方語言",
      "government": "政體",
      "established": "成立",
      "area": "面積",
      "gdp_nominal": "GDP（名義）",
      "gdp_ppp": "GDP（購買力平價）",
      "currency": "貨幣",
      "timezone": "時區",
      "emblems": "徽章",
      "leaders": "領導人",
      "capital_coord": "首都座標",
      "reset_view_title": "重置地圖視圖"
    },
  };

  const SUPPORTED = ["en-GB", "fr-CA", "zh-Hans", "zh-HK"];

  let currentLocale = localStorage.getItem("atlas.locale") || "en-GB";
  if (!SUPPORTED.includes(currentLocale)) currentLocale = "en-GB";

  window.I18n = {
    get locale() { return currentLocale; },
    locales: SUPPORTED,

    setLocale(locale) {
      if (!SUPPORTED.includes(locale)) return;
      currentLocale = locale;
      localStorage.setItem("atlas.locale", locale);
      document.documentElement.lang = locale;
      this.applyStaticTexts();
    },

    t(key, params) {
      const dict = UI_STRINGS[currentLocale] || UI_STRINGS["en-GB"];
      let s = dict[key] ?? UI_STRINGS["en-GB"][key] ?? key;
      if (params) {
        for (const [k, v] of Object.entries(params)) {
          s = s.split("{" + k + "}").join(String(v));
        }
      }
      return s;
    },

    applyStaticTexts() {
      document.querySelectorAll("[data-i18n]").forEach((el) => {
        el.textContent = this.t(el.getAttribute("data-i18n"));
      });
    },
  };
})();
