# -*- coding: utf-8 -*-
"""Metadata for the Magellan lesson stops: WHEN (best-attested date
strings) and PRESENT (precise present-day places, en + native + iso3).
Dates per Pigafetta and standard reconstructions; months/days only
where attested."""

WHEN = {
    "sanlucar": "20 September 1519",
    "tenerife": "26 September – 3 October 1519",
    "rio": "13 December 1519 – 11 January 1520",
    "plata": "10 – 24 January 1520",
    "san_julian": "31 March – 24 August 1520",
    "strait": "21 October – 28 November 1520",
    "pacific_crossing": "28 November 1520 – 6 March 1521 (98 days)",
    "guam": "6 – 9 March 1521",
    "homonhon": "16 – 25 March 1521",
    "limasawa": "28 – 31 March 1521",
    "cebu": "7 – 27 April 1521",
    "mactan": "27 April 1521",
    "palawan": "19 April – 4 May 1521 (fleet passages)",
    "brunei": "8 – 29 July 1521",
    "tidore": "8 November – 21 December 1521",
    "ambon": "November 1521 – January 1522 (area)",
    "timor": "c. 15 – 25 January 1522",
    "cape_hope": "19 May 1522 (passed)",
    "verde": "9 – 15 July 1522",
    "sanlucar_end": "6 September 1522",
}

# per-stop year for badges / quiz
YEAR = {
    "sanlucar": 1519, "tenerife": 1519, "rio": 1519, "plata": 1520,
    "san_julian": 1520, "strait": 1520, "pacific_crossing": 1521,
    "guam": 1521, "homonhon": 1521, "limasawa": 1521, "cebu": 1521,
    "mactan": 1521, "palawan": 1521, "brunei": 1521, "tidore": 1521,
    "ambon": 1521, "timor": 1522, "cape_hope": 1522, "verde": 1522,
    "sanlucar_end": 1522,
}

# native (local-script) names, keyed like Xuanzang's PRESENT module:
# id -> {en, zh, ja, iso3}
PRESENT = {
    "sanlucar": {"en": "Sanlúcar de Barrameda, Andalusia, Spain",
                 "zh": "西班牙安达卢西亚桑卢卡尔-德巴拉梅达",
                 "ja": "スペイン・アンダルシア州サンルカル・デ・バラメダ", "iso3": "ESP"},
    "tenerife": {"en": "Tenerife, Canary Islands, Spain",
                 "zh": "西班牙加那利群岛特内里费岛",
                 "ja": "スペイン・カナリア諸島テネリフェ島", "iso3": "ESP"},
    "rio": {"en": "Rio de Janeiro, Brazil",
            "zh": "巴西里约热内卢", "ja": "ブラジル・リオデジャネイロ", "iso3": "BRA"},
    "plata": {"en": "Río de la Plata estuary, Argentina/Uruguay",
              "zh": "阿根廷/乌拉圭拉普拉塔河口",
              "ja": "アルゼンチン/ウルグアイ・ラプラタ川河口", "iso3": "ARG"},
    "san_julian": {"en": "Puerto San Julián, Santa Cruz Province, Argentina",
                   "zh": "阿根廷圣克鲁斯省圣胡利安港",
                   "ja": "アルゼンチン・サンタクルス州プエルト・サンフリアン", "iso3": "ARG"},
    "strait": {"en": "Strait of Magellan, Chile",
               "zh": "智利麦哲伦海峡",
               "ja": "チリ・マゼラン海峡", "iso3": "CHL"},
    "pacific_crossing": {"en": "Pacific Ocean (track unknown; likely through the Tuamotus' north)",
                         "zh": "太平洋（航线不详，可能在土阿莫土群岛以北）",
                         "ja": "太平洋（航路不明、トゥアモトゥ諸島以北か）", "iso3": None},
    "guam": {"en": "Guam (US territory), Micronesia",
             "zh": "关岛（美国领地），密克罗尼西亚",
             "ja": "グアム（米国領）、ミクロネシア", "iso3": "GUM"},
    "homonhon": {"en": "Homonhon Island, Eastern Samar, Philippines",
                 "zh": "菲律宾东萨马省霍蒙洪岛",
                 "ja": "フィリピン・東サマール州ホモンホン島", "iso3": "PHL"},
    "limasawa": {"en": "Limasawa Island, Southern Leyte, Philippines",
                 "zh": "菲律宾南莱特省利马萨瓦岛",
                 "ja": "フィリピン・南レイテ州リマサワ島", "iso3": "PHL"},
    "cebu": {"en": "Cebu City, Cebu, Philippines",
             "zh": "菲律宾宿务省宿务市",
             "ja": "フィリピン・セブ州セブ市", "iso3": "PHL"},
    "mactan": {"en": "Mactan Island, Cebu, Philippines",
               "zh": "菲律宾宿务马克坦岛",
               "ja": "フィリピン・セブ州マクタン島", "iso3": "PHL"},
    "palawan": {"en": "Palawan, Philippines (MIMAROPA region)",
                "zh": "菲律宾巴拉望省",
                "ja": "フィリピン・パラワン州", "iso3": "PHL"},
    "brunei": {"en": "Bandar Seri Begawan (then Brunei Town), Brunei",
               "zh": "文莱斯里巴加湾市（旧称文莱城）",
               "ja": "ブルネイ・スリバガワン市（旧ブルネイ・タウン）", "iso3": "BRN"},
    "tidore": {"en": "Tidore Island, North Maluku, Indonesia",
               "zh": "印度尼西亚北马鲁古省蒂多雷岛",
               "ja": "インドネシア・北マルク州ティドレ島", "iso3": "IDN"},
    "ambon": {"en": "Ambon Island, Maluku, Indonesia",
              "zh": "印度尼西亚马鲁古省安汶岛",
              "ja": "インドネシア・マルク州アンボン島", "iso3": "IDN"},
    "timor": {"en": "Timor (island), Indonesia / Timor-Leste",
              "zh": "帝汶岛（印度尼西亚/东帝汶）",
              "ja": "ティモール島（インドネシア/東ティモール）", "iso3": "IDN"},
    "cape_hope": {"en": "Cape of Good Hope, Western Cape, South Africa",
                  "zh": "南非西开普省好望角",
                  "ja": "南アフリカ・西ケープ州喜望峰", "iso3": "ZAF"},
    "verde": {"en": "Santiago Island, Cape Verde",
              "zh": "佛得角圣地亚哥岛",
              "ja": "カーボベルデ・サンティアゴ島", "iso3": "CPV"},
    "sanlucar_end": {"en": "Sanlúcar de Barrameda, then upriver to Seville, Spain",
                     "zh": "西班牙桑卢卡尔-德巴拉梅达，溯河至塞维利亚",
                     "ja": "スペイン・サンルカル・デ・バラメダ、川を遡りセビーリャへ", "iso3": "ESP"},
}

# display names per stop: en + native scripts (others via GLM)
NAMES = {
    "sanlucar": {"en-GB": "Sanlúcar de Barrameda", "zh-Hans": "桑卢卡尔-德巴拉梅达", "ja": "サンルカル・デ・バラメダ"},
    "tenerife": {"en-GB": "Tenerife", "zh-Hans": "特内里费岛", "ja": "テネリフェ島"},
    "rio": {"en-GB": "Rio de Janeiro", "zh-Hans": "里约热内卢", "ja": "リオデジャネイロ"},
    "plata": {"en-GB": "Río de la Plata", "zh-Hans": "拉普拉塔河", "ja": "ラプラタ川"},
    "san_julian": {"en-GB": "Puerto San Julián", "zh-Hans": "圣胡利安港", "ja": "サンフリアン港"},
    "strait": {"en-GB": "Strait of Magellan", "zh-Hans": "麦哲伦海峡", "ja": "マゼラン海峡"},
    "pacific_crossing": {"en-GB": "Pacific crossing", "zh-Hans": "横渡太平洋", "ja": "太平洋横断"},
    "guam": {"en-GB": "Guam", "zh-Hans": "关岛", "ja": "グアム"},
    "homonhon": {"en-GB": "Homonhon", "zh-Hans": "霍蒙洪岛", "ja": "ホモンホン島"},
    "limasawa": {"en-GB": "Limasawa", "zh-Hans": "利马萨瓦岛", "ja": "リマサワ島"},
    "cebu": {"en-GB": "Cebu", "zh-Hans": "宿务", "ja": "セブ"},
    "mactan": {"en-GB": "Mactan", "zh-Hans": "马克坦岛", "ja": "マクタン島"},
    "palawan": {"en-GB": "Palawan", "zh-Hans": "巴拉望", "ja": "パラワン"},
    "brunei": {"en-GB": "Brunei", "zh-Hans": "文莱", "ja": "ブルネイ"},
    "tidore": {"en-GB": "Tidore", "zh-Hans": "蒂多雷", "ja": "ティドレ"},
    "ambon": {"en-GB": "Ambon", "zh-Hans": "安汶", "ja": "アンボン"},
    "timor": {"en-GB": "Timor", "zh-Hans": "帝汶", "ja": "ティモール"},
    "cape_hope": {"en-GB": "Cape of Good Hope", "zh-Hans": "好望角", "ja": "喜望峰"},
    "verde": {"en-GB": "Cape Verde (Santiago)", "zh-Hans": "佛得角（圣地亚哥岛）", "ja": "カーボベルデ（サンティアゴ島）"},
    "sanlucar_end": {"en-GB": "Sanlúcar de Barrameda (return)", "zh-Hans": "桑卢卡尔-德巴拉梅达（归航）", "ja": "サンルカル・デ・バラメダ（帰航）"},
}

# one fact per stop for the sights quiz (en; translated via GLM)
SIGHTS = {
    "sanlucar": "Five ships and about 270 men sailed on 20 September 1519 under a Portuguese captain serving Spain — Magellan, already under a Portuguese death sentence.",
    "tenerife": "Learned here of the Spanish captains' plot against him, and answered by refusing to reveal his route to anyone; a Portuguese squadron sent to intercept him missed him.",
    "rio": "Found 'the best land in the world' — thirteen days of fruit, parrots and freely-giving people while the scurvy crews recovered, the last friendly port for 10,000 km.",
    "plata": "Spent two weeks probing the great estuary hoping it was the strait — a dead end; here they saw penguins and misidentified them as black geese.",
    "san_julian": "Wintered five months at 49° south; crushed the Spanish captains' Easter mutiny — beheadings, a marooning — and lost the Santiago scouting ahead; met the Tehuelche 'giants'.",
    "strait": "Found and fought through 560 km of glacier-cut channels he had promised existed — the San Antonio deserted with most of the food — emerging 28 November into an ocean so calm he named it Pacific.",
    "pacific_crossing": "Ninety-eight days with no land: biscuit gone to powder, water gone yellow, nineteen dead of scurvy — the longest passage any European had ever made.",
    "guam": "First land in 98 days; after the starving crews traded for food, fights ashore left Chamorro dead and the islands named 'Islands of Thieves'.",
    "homonhon": "The first European landfall in the Philippines — stumbled on by accident while water and firewood were sought on an uninhabited island.",
    "limasawa": "The Malay slave Enrique understood the islanders — a man carried from Sumatra via Europe was hearing his own region's speech again: arguably the first circumnavigator, ahead of his master.",
    "cebu": "Rajah Humabon was baptised, a cross planted, the Santo Niño image given to his queen — two weeks of mass baptisms in the great trading port of the Visayas.",
    "mactan": "Magellan died here on 27 April 1521, cut down with eight of his men in the shallows — some fifty armoured Spaniards against some 1,500 warriors of Lapulapu.",
    "palawan": "Reduced to two ships — the Concepción was burned for want of crew — the survivors coasted Palawan's rice-and-swine ports in a rare stretch of peace.",
    "brunei": "Two weeks in the sultan's capital — elephants in silk, cloth-of-gold, porcelain heirlooms — until missing men provoked a bombardment and a departure with hostages and provisions.",
    "tidore": "The Spice Islands at last: the hold filled with cloves worth more than the voyage's whole cost; the Trinidad left behind to try the Pacific, Victoria to run for home westward.",
    "ambon": "Crept through the Molucca Sea between Halmahera and Ceram, avoiding Portuguese patrols while the Trinidad's men were being arrested ashore.",
    "timor": "Bought cloves and sandalwood from Timor's chiefs — among the earliest European records of the sandalwood trade — then sailed alone, no other ship left in company.",
    "cape_hope": "Ran far south past the Cape on 19 May 1522 with the crew dying of scurvy; the pumps never stopped and the masts went over the side in the Atlantic calms.",
    "verde": "Thirteen men sent ashore for rice were unmasked by a date — the Victoria's Thursday was the islands' Friday: the lost day of westbound circumnavigation.",
    "sanlucar_end": "Eighteen men of about 270 returned on 6 September 1522, barefoot to the shrine, with 26 tons of cloves — the first circumnavigation complete.",
}

# quiz distractor places: real 16th-century waypoints near the route
# but not stops of this lesson
QUIZ_PLACES = {
    "canary_las_palmas": {
        "names": {"en-GB": "Las Palmas (Gran Canaria)", "zh-Hans": "拉斯帕尔马斯（大加那利岛）", "ja": "ラスパルマス（グラン・カナリア島）"},
        "year": 1519,
    },
    "st_helena": {
        "names": {"en-GB": "St Helena", "zh-Hans": "圣赫勒拿岛", "ja": "セントヘレナ"},
        "year": 1522,
    },
    "malacca": {
        "names": {"en-GB": "Malacca", "zh-Hans": "马六甲", "ja": "マラッカ"},
        "year": 1511,
    },
    "ternate": {
        "names": {"en-GB": "Ternate", "zh-Hans": "特尔纳特", "ja": "テルナテ"},
        "year": 1521,
    },
    "java_majapahit": {
        "names": {"en-GB": "Java (Majapahit)", "zh-Hans": "爪哇（满者伯夷）", "ja": "ジャワ（マジャパヒト）"},
        "year": 1522,
    },
    "madeira": {
        "names": {"en-GB": "Madeira", "zh-Hans": "马德拉群岛", "ja": "マデイラ諸島"},
        "year": 1519,
    },
    "fernando_noronha": {
        "names": {"en-GB": "Fernando de Noronha", "zh-Hans": "费尔南多-迪诺罗尼亚群岛", "ja": "フェルナンド・デ・ノローニャ"},
        "year": 1520,
    },
    "falklands": {
        "names": {"en-GB": "Falkland Islands", "zh-Hans": "福克兰群岛", "ja": "フォークランド諸島"},
        "year": 1520,
    },
    "molucca_ternate_pt": {
        "names": {"en-GB": "Amboina (Portuguese fort)", "zh-Hans": "安波那（葡萄牙要塞）", "ja": "アンボイナ（ポルトガル要塞）"},
        "year": 1522,
    },
    "azores": {
        "names": {"en-GB": "Azores", "zh-Hans": "亚速尔群岛", "ja": "アゾレス諸島"},
        "year": 1522,
    },
}
