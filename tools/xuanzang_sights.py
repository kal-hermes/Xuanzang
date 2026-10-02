# -*- coding: utf-8 -*-
# Quiz content for the Xuanzang journey lesson (English source).
#
# SIGHTS: one fact per stop, each derived strictly from the published
# narratives in xuanzang_text_*.py (Record of the Western Regions tr.
# Beal; Biography tr. Li Rongxi; Wriggins 2004) — used for the
# "guess the sights" quiz mode.
#
# PLACES: real 7th-century polities from the Record's route sequence
# that are NOT stops of our 28-stop lesson — used as believable
# place-distractors for the "guess the route" quiz. Coordinates are the
# commonly accepted identifications (approximate where disputed).

SIGHTS = {
    "chang_an": "Slipped out of the Tang capital in autumn 629 amid famine, defying the imperial ban on leaving the empire — alone and unauthorised.",
    "liangzhou": "Taught for weeks until the governor ordered him sent back; a sympathetic official smuggled him onward by night with two disciples.",
    "guazhou": "Crossed the 'River of Sand' alone after his guide fled at the first beacon tower — four nights and five days without water, saved when his old red horse smelled out a spring.",
    "hami": "Recovered for about ten days under the devout king of Yiwu, then was all but summoned to Gaochang by an envoy with mounting threats.",
    "gaochang": "Hunger-struck for three days until King Qu Wentai relented, swore brotherhood with him, and funded twenty-four years of travel with gold, horses and letters.",
    "karashahr": "Was received by a king related to Kucha's royal house — in a court the Record describes as destabilised, its ministers violent and its laws unevenly enforced.",
    "kucha": "Defeated the India-trained monk Mokshagupta in debate, then waited two months before the caravan crossed the Bedel Pass, losing men and animals in the frozen scree.",
    "aksu": "Made a brief halt in Baluka; beyond it the road ran out of cultivated land and the ascent over the Tian Shan glaciers took seven days, killing several men.",
    "suyab": "Met Tong Yabghu Khagan in a felt tent hung with silk before two hundred chieftains — taking grape juice instead of wine — and left with the khagan's sealed letter of safe conduct.",
    "talas": "Passed through vineyard country of green-eyed, felt-clad Iranian speakers — a marchland of the khaganate between Turkic power and the Persian world.",
    "samarkand": "Found the Sogdian metropolis worshipping fire: both Buddhist monasteries stood abandoned, and fire-priests drove his young followers out with burning brands.",
    "iron_gate": "Passed the Iron Gate — a defile between black-red cliffs barely wide enough for one horse, closed by iron doors plated over the rock and garrisoned.",
    "balkh": "Studied for about a month at the Nava Vihara under the aged master Prajnakara, in the 'mother of cities' ringed by a hundred monasteries and three thousand monks.",
    "bamyan": "Saw the two colossal standing Buddhas — 55 and 38 metres, gilded and dazzling — and a colossal reclining Buddha in parinirvana about 300 metres long.",
    "kapisa": "Wintered roughly two years with the Buddhist Kabul Shahi king and was shown the Buddha's skull-bone relic, exhibited only rarely and under royal guard.",
    "nagarahara": "Walked a robber-infested road alone with a young guide to worship in the dark cave where the Buddha was said to have left his shadow.",
    "gandhara": "Toured a great ruined landscape around Kanishka's stupa — of the region's thousand monasteries most stood empty, the sangha in decay.",
    "swat": "Described an abandoned sacred land: ancient stupas crowning every hill, monasteries mostly ruined, and mountain defiles notoriously infested with robbers.",
    "kashmir": "Studied Buddhist logic and the Abhidharma for about two years in a kingdom of roughly a hundred monasteries and five thousand monks given to disputation.",
    "punjab": "Recorded monastery after monastery in decay and blamed the Huna king Mihirakula, whose wars a century and a half earlier had shattered the monastic network.",
    "nalanda": "Studied about five years under the centenarian abbot Shilabhadra, mastering the Yogacara corpus at the greatest centre of learning in the world.",
    "kanauj": "Championed Mahayana at Emperor Harsha's assembly in 643 with his head forfeit on his theses — for days no one dared answer, until riots were set and suppressed.",
    "prayaga": "Watched Emperor Harsha give away his entire treasury over seventy-five days at the Ganges-Yamuna confluence, ransoming even his robes back from his nobles.",
    "kashgar": "Came down from the Pamirs after his elephant slipped into a torrent gorge and drowned with manuscripts, and praised the kingdom's sandalwood Buddha-carvers.",
    "khotan": "Waited nearly half a year at the desert's edge for Emperor Taizong's reply to his humble memorial before leaving in 644 under imperial protection.",
    "loulan": "Crossed the dying Lop Nor along beacon mounds between dunes, navigating by the skeletons of earlier travellers.",
    "dunhuang": "Re-entered the Tang empire in form at the garrison town of Shazhou, received with escort and supplies under the emperor's standing order.",
    "chang_an_end": "Reached Chang'an in February 645 to a capital that turned out entire; declined office, won a translation bureau, and translated 75 works before dying in 664.",
}

# Distractor places: real polities from the Record's route sequence,
# named in vol. 1 / vol. 12, not among our 28 stops.
# year = the rough year Xuanzang passed through (or would have), used
# only as a plausible anchor for generating wrong answers.
PLACES = {
    "qianquan": {
        "names": {"en-GB": "Qianquan (Thousand Springs)", "zh-Hans": "千泉"},
        "present": "Merke area, Jambyl Region, Kazakhstan",
        "coords": [73.0, 43.05], "year": 630,
    },
    "chach": {
        "names": {"en-GB": "Chach", "zh-Hans": "赭时国"},
        "present": "Tashkent, Uzbekistan",
        "coords": [69.24, 41.30], "year": 630,
    },
    "bukhara": {
        "names": {"en-GB": "Bukhara", "zh-Hans": "捕喝国"},
        "present": "Bukhara, Uzbekistan",
        "coords": [64.42, 39.77], "year": 630,
    },
    "kesh": {
        "names": {"en-GB": "Kesh", "zh-Hans": "羯霜那国"},
        "present": "Shahrisabz, Uzbekistan",
        "coords": [66.83, 39.00], "year": 630,
    },
    "termez": {
        "names": {"en-GB": "Termez", "zh-Hans": "呾蜜国"},
        "present": "Termez, on the Oxus (Amu Darya), Uzbekistan",
        "coords": [67.28, 37.23], "year": 630,
    },
    "kunduz": {
        "names": {"en-GB": "Huo Guo (Valley of Kunduz)", "zh-Hans": "活国"},
        "present": "Kunduz, Afghanistan",
        "coords": [68.86, 36.73], "year": 642,
    },
    "taxila": {
        "names": {"en-GB": "Takshasila", "zh-Hans": "呾叉始罗国"},
        "present": "Taxila, Punjab, Pakistan",
        "coords": [72.52, 33.76], "year": 631,
    },
    "varanasi": {
        "names": {"en-GB": "Varanasi", "zh-Hans": "婆罗痆斯国"},
        "present": "Varanasi (Sarnath), Uttar Pradesh, India",
        "coords": [83.00, 25.32], "year": 636,
    },
    "tashkurgan": {
        "names": {"en-GB": "Kiepantuo (Stone Tower)", "zh-Hans": "朅盘陀国"},
        "present": "Tashkurgan, Xinjiang, China",
        "coords": [75.23, 37.77], "year": 642,
    },
    "yarkant": {
        "names": {"en-GB": "Wusha", "zh-Hans": "乌铩国"},
        "present": "Yarkant (Shache), Xinjiang, China",
        "coords": [77.24, 38.42], "year": 643,
    },
    "chitral": {
        "names": {"en-GB": "Shangmi", "zh-Hans": "商弥国"},
        "present": "Chitral, Khyber Pakhtunkhwa, Pakistan",
        "coords": [71.80, 35.85], "year": 642,
    },
}
