# Xuanzang stop metadata beyond narrative: precise present-day place and
# best-attested dates. Keyed by stop id.
#
# present: most precise modern locator, per locale family
# when:     date string with as much precision as the sources support
#           (Biography of the Tripitaka Master, tr. Li Rongxi, 1995;
#            Record of the Western Regions, 646, tr. Beal 1884)
#
# Dates follow the scholarly consensus (Wriggins, Sen, Li Rongxi notes).
# Where sources give only a season or year, we say so — no invented
# months.

PRESENT = {
    "chang_an": {
        "en": "Xi'an, Shaanxi, China",
        "zh": "中国陕西省西安市",
        "ja": "中国陝西省西安市",
        "iso3": "CHN",
    },
    "liangzhou": {
        "en": "Wuwei, Gansu, China",
        "zh": "中国甘肃省武威市",
        "ja": "中国甘粛省武威市",
        "iso3": "CHN",
    },
    "guazhou": {
        "en": "Guazhou County, near Yumen Pass, Gansu, China",
        "zh": "中国甘肃省瓜州县（玉门关附近）",
        "ja": "中国甘粛省瓜州県（玉門関付近）",
        "iso3": "CHN",
    },
    "hami": {
        "en": "Hami (Kumul), Xinjiang, China",
        "zh": "中国新疆哈密市",
        "ja": "中国新疆ハミ（クムル）市",
        "iso3": "CHN",
    },
    "gaochang": {
        "en": "Gaochang ruins, Turpan, Xinjiang, China",
        "zh": "中国新疆吐鲁番高昌故城",
        "ja": "中国新疆トルファン高昌故城",
        "iso3": "CHN",
    },
    "karashahr": {
        "en": "Yanqi Hui Autonomous County, Xinjiang, China",
        "zh": "中国新疆焉耆回族自治县",
        "ja": "中国新疆焉耆回族自治県",
        "iso3": "CHN",
    },
    "kucha": {
        "en": "Kuqa (Kucha), Aksu Prefecture, Xinjiang, China",
        "zh": "中国新疆阿克苏地区库车市",
        "ja": "中国新疆アクス地区クチャ市",
        "iso3": "CHN",
    },
    "aksu": {
        "en": "Aksu, Xinjiang, China",
        "zh": "中国新疆阿克苏市",
        "ja": "中国新疆アクス市",
        "iso3": "CHN",
    },
    "suyab": {
        "en": "Ak-Beshim site, near Tokmok, Chüy Region, Kyrgyzstan",
        "zh": "吉尔吉斯斯坦楚河州托克马克附近阿克贝希姆遗址",
        "ja": "キルギス・チュイ州トクマク近郊アク・ベシム遺跡",
        "iso3": "KGZ",
    },
    "talas": {
        "en": "Taraz, Jambyl Region, Kazakhstan",
        "zh": "哈萨克斯坦江布尔州塔拉兹",
        "ja": "カザフスタンジャムブル州タラズ",
        "iso3": "KAZ",
    },
    "samarkand": {
        "en": "Samarkand, Uzbekistan",
        "zh": "乌兹别克斯坦撒马尔罕",
        "ja": "ウズベキスタン・サマルカンド",
        "iso3": "UZB",
    },
    "iron_gate": {
        "en": "Buzgala (Iron Gate) defile, Derbent, Samarkand Region, Uzbekistan",
        "zh": "乌兹别克斯坦撒马尔罕州达尔本特铁门关",
        "ja": "ウズベキスタン・サマルカンド州ダルベントの鉄門峡谷",
        "iso3": "UZB",
    },
    "balkh": {
        "en": "Balkh, Balkh Province, Afghanistan",
        "zh": "阿富汗巴尔赫省巴尔赫",
        "ja": "アフガニスタン・バルフ州バルフ",
        "iso3": "AFG",
    },
    "bamyan": {
        "en": "Bamyan, Bamyan Province, Afghanistan",
        "zh": "阿富汗巴米扬省巴米扬",
        "ja": "アフガニスタン・バーミヤーン州バーミヤーン",
        "iso3": "AFG",
    },
    "kapisa": {
        "en": "Bagram, Kapisa Province, Afghanistan",
        "zh": "阿富汗卡皮萨省贝格拉姆",
        "ja": "アフガニスタン・カピサ州バグラーム",
        "iso3": "AFG",
    },
    "nagarahara": {
        "en": "Jalalabad, Nangarhar Province, Afghanistan",
        "zh": "阿富汗楠格哈尔省贾拉拉巴德",
        "ja": "アフガニスタン・ナンガルハール州ジャラーラーバード",
        "iso3": "AFG",
    },
    "gandhara": {
        "en": "Peshawar, Khyber Pakhtunkhwa, Pakistan",
        "zh": "巴基斯坦开伯尔-普什图省白沙瓦",
        "ja": "パキスタン・カイバル・パクトゥンクワ州ペシャーワル",
        "iso3": "PAK",
    },
    "swat": {
        "en": "Swat Valley, Khyber Pakhtunkhwa, Pakistan",
        "zh": "巴基斯坦开伯尔-普什图省斯瓦特河谷",
        "ja": "パキスタン・カイバル・パクトゥンクワ州スワート渓谷",
        "iso3": "PAK",
    },
    "kashmir": {
        "en": "Kashmir Valley, Jammu & Kashmir, India / Azad Kashmir, Pakistan",
        "zh": "克什米尔谷地（印控/巴控克什米尔）",
        "ja": "カシミール渓谷（インド支配/パキスタン支配カシミール）",
        "iso3": "IND",
    },
    "punjab": {
        "en": "Punjab region, India/Pakistan",
        "zh": "旁遮普地区（印度/巴基斯坦）",
        "ja": "パンジャーブ地方（インド/パキスタン）",
        "iso3": "IND",
    },
    "nalanda": {
        "en": "Nalanda Mahavihara ruins, near Rajgir, Nalanda District, Bihar, India",
        "zh": "印度比哈尔邦那烂陀县王舍城附近那烂陀寺遗址",
        "ja": "インド・ビハール州ナーランダ県ラージギール近郊の那爛陀寺遺跡",
        "iso3": "IND",
    },
    "kanauj": {
        "en": "Kannauj, Uttar Pradesh, India",
        "zh": "印度北方邦根瑙杰",
        "ja": "インド・ウッタル・プラデーシュ州カンナウジ",
        "iso3": "IND",
    },
    "prayaga": {
        "en": "Prayagraj (Allahabad), Uttar Pradesh, India",
        "zh": "印度北方邦普拉亚格拉杰（原阿拉哈巴德）",
        "ja": "インド・ウッタル・プラデーシュ州プラヤーガラジ（旧アラーハーバード）",
        "iso3": "IND",
    },
    "kashgar": {
        "en": "Kashgar, Xinjiang, China",
        "zh": "中国新疆喀什市",
        "ja": "中国新疆カシュガル（喀什）市",
        "iso3": "CHN",
    },
    "khotan": {
        "en": "Hotan, Xinjiang, China",
        "zh": "中国新疆和田市",
        "ja": "中国新疆ホータン（和田）市",
        "iso3": "CHN",
    },
    "loulan": {
        "en": "Miran / Lop Nor region, Bayingolin, Xinjiang, China",
        "zh": "中国新疆巴音郭楞米兰遗址/罗布泊地区",
        "ja": "中国新疆バインゴリン・ミーラン遺跡/ロプノール地域",
        "iso3": "CHN",
    },
    "dunhuang": {
        "en": "Dunhuang, Gansu, China",
        "zh": "中国甘肃省敦煌市",
        "ja": "中国甘粛省敦煌市",
        "iso3": "CHN",
    },
    "chang_an_end": {
        "en": "Xi'an, Shaanxi, China",
        "zh": "中国陕西省西安市",
        "ja": "中国陝西省西安市",
        "iso3": "CHN",
    },
}

# Best-attested dates. Sources: Biography (Li Rongxi 1995), Record of
# the Western Regions, Wriggins 2004, Tansen Sen 2006. Traditional
# Chinese dating is by lunar year; conversions approximate.
WHEN = {
    "chang_an": "autumn 629 (some sources: 627)",
    "liangzhou": "late 629",
    "guazhou": "winter 629–630",
    "hami": "c. spring 630",
    "gaochang": "spring–summer 630 (630–631 lunar)",
    "karashahr": "summer 630",
    "kucha": "autumn 630 (630–631 lunar)",
    "aksu": "autumn 630",
    "suyab": "late 630",
    "talas": "late 630",
    "samarkand": "winter 630–631",
    "iron_gate": "winter 630–631",
    "balkh": "early 631",
    "bamyan": "spring 631",
    "kapisa": "summer 631 (two summers: 631 & 632)",
    "nagarahara": "autumn 631",
    "gandhara": "late 631",
    "swat": "winter 631–632",
    "kashmir": "631–633 (two years of study)",
    "kashmir2": "631–633",
    "punjab": "634",
    "nalanda": "arrived c. 636; studied to 641",
    "kanauj": "641–643 (at Harsha's court)",
    "prayaga": "early 643 (the great assembly)",
    "kashgar": "643–644 (crossing the Pamirs)",
    "khotan": "644 (waited ~half a year for Taizong's reply)",
    "loulan": "644–645 (southern Taklamakan crossing)",
    "dunhuang": "late 644",
    "chang_an_end": "7 February 645 (7th day, 1st lunar month)",
}
