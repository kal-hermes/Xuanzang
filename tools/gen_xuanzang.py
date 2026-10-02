#!/usr/bin/env python3
"""Generate the Xuanzang journey lesson.

Stops are historical places geocoded from their Wikidata QIDs (P625
coordinates), so locations come from Wikidata rather than hand-typed.
Narrative: Xuanzang's own Record of the Western Regions (646 CE) as
translated by Samuel Beal (1884), plus standard reconstructions.

Outputs:
  lessons/xuanzang/journey.json
  lessons/xuanzang/journey.js   (script-tag twin for file://)
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "Xuanzang-app-lesson-builder/1.0 (educational)"}

# rich content + metadata from sibling modules (loaded lazily in main()
# so a missing translation file doesn't break --help imports)
NARRATIVE_RICH = {"en-GB": {}, "fr-CA": {}, "zh-Hans": {}, "zh-HK": {}, "ja": {}}
META_I18N = {}  # locale -> {"when": {stop: str}, "present": {stop: str}}

def _load_content():
    import importlib.util
    base = Path(__file__).parent
    def load(name, fname, attr="NARRATIVE_RICH"):
        p = base / fname
        if not p.exists():
            print(f"  (no {fname}; falling back to short narratives)", file=sys.stderr)
            return
        spec = importlib.util.spec_from_file_location(name, p)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        NARRATIVE_RICH[name] = getattr(m, attr)
    load("en-GB", "xuanzang_text_en.py")
    load("fr-CA", "xuanzang_text_fr-CA.py")
    load("zh-Hans", "xuanzang_text_zh-Hans.py")
    load("zh-HK", "xuanzang_text_zh-HK.py")
    load("ja", "xuanzang_text_ja.py")
    # localized when/present strings (GLM-generated, reviewed keys)
    i18n_path = base / "xuanzang_meta_i18n.json"
    global META_I18N
    META_I18N = {}
    if i18n_path.exists():
        META_I18N = json.loads(i18n_path.read_text(encoding="utf-8"))
    else:
        print("  (no xuanzang_meta_i18n.json; when/present stay English)", file=sys.stderr)
    global WHEN, PRESENT
    spec = importlib.util.spec_from_file_location("meta", base / "xuanzang_meta.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    WHEN, PRESENT = m.WHEN, m.PRESENT


# QIDs resolved via wbsearchentities + verified by label/description
# and coordinates (see resolve log in tools/gen_xuanzang.py history).
STOPS = [
    # key, Wikidata QID, year label, modern country (iso3)
    ("chang_an",     "Q6501000", "629", "CHN"),  # ancient capital, Tang
    ("liangzhou",    "Q249007",  "629", "CHN"),  # modern Wuwei
    ("guazhou",      "Q1201947", "629", "CHN"),  # Guazhou county, Gansu
    ("hami",         "Q989892",  "629", "CHN"),  # Hami (Kumul), Xinjiang
    ("gaochang",     "Q877381",  "630", "CHN"),  # ruins site, Turpan
    ("karashahr",    "Q1156662", "630", "CHN"),  # town Yanqi
    ("kucha",        "Q1328546", "630", "CHN"),  # former kingdom Kucha
    ("aksu",         "Q421648",  "630", "CHN"),  # Aksu, county-level city
    ("suyab",        "Q413452",  "630", "KGZ"),  # ancient Silk Road city
    ("talas",        "Q486545",  "630", "KAZ"),  # Taraz, Kazakhstan
    ("samarkand",    "Q5753",    "630", "UZB"),
    ("iron_gate",    "Q3399252", "630", "UZB"),  # defile in Central Asia
    ("balkh",        "Q182159",  "630", "AFG"),  # city, not the province
    ("bamyan",       "Q214495",  "630", "AFG"),  # city Bamyan
    ("kapisa",       "Q173816",  "630", "AFG"),  # province (region anchor)
    ("nagarahara",   "Q183303",  "630", "AFG"),  # Jalalabad
    ("gandhara",     "Q1113311", "630", "PAK"),  # Peshawar
    ("swat",         "Q389161",  "630", "PAK"),  # Swat District
    ("kashmir",      "Q43100",   "631", "IND"),  # Kashmir region
    ("punjab",       "Q169132",  "633", "IND"),  # Punjab region (Takka)
    ("nalanda",      "Q216243",  "636", "IND"),  # Nalanda Mahavihara
    ("kanauj",       "Q614890",  "641", "IND"),  # Kannauj town
    ("prayaga",      "Q162442",  "643", "IND"),  # Prayagraj
    # --- return leg ---
    ("kashgar",      "Q170521",  "643", "CHN"),  # Kashgar city
    ("khotan",       "Q914898",  "644", "CHN"),  # Kingdom of Khotan (oasis)
    ("loulan",       "Q1057551", "644", "CHN"),  # Loulan Kingdom (Miran)
    ("dunhuang",     "Q319114",  "644", "CHN"),  # county-level city
    ("chang_an_end", "Q6501000", "645", "CHN"),
]

NARRATIVE = {
    # en-GB blurb — what he saw / what was happening, per stop
    "chang_an": "Tang capital. Departed in secret — travel west was banned; a famine in the Yellow River valley had emptied the roads of border checks.",
    "liangzhou": "Frontier city under Huili the governor, who — sympathetic to the pilgrim — warned him the passes ahead were hunted with warrants for his arrest.",
    "guazhou": "Last Chinese town. Slipped out at night past the Yumen Pass; his guide betrayed him, his horse died, and he nearly perished of thirst crossing the Mo-sha (Gobi) desert.",
    "hami": "First foreign kingdom (Yiwu). Collapsed from his horse with exhaustion; the king's messengers found him and carried him to the court.",
    "gaochang": "The fervently Buddhist king Qu Wentai wanted to keep him as state preceptor; Xuanzang went on hunger strike until the king relented — and became his sworn brother, equipping the journey with gold, silk, letters and 4 monks.",
    "kucha": "Kingdom of Kucha — " + "the great centre of Sarvastivada Buddhism. Kept for two months by King Suvarnadeva for debates; Xuanzang out-argued the local Arhat Mokṣagupta, who conceded that Chinese Buddhism 'went far'.",
    "karashahr": "The ancient kingdom of Agni (Karashahr). A stop on the northern Silk Road; its king, a Kuchean kinsman, received the pilgrim with horse and supplies for the next desert crossing.",
    "aksu": "Small oasis kingdom of Baluka (modern Aksu). The king, a Turkic appointee, was a patron of the Sarvastivada school; Xuanzang lectured on Buddhist logic to the monks.",
    "suyab": "Capital of the Western Turkic Khaganate. The khagan Tong Yabghu — recently victorious, at the height of his power — received him seated on a felt throne amid his armed horsemen, and gave him letters of safe passage.",
    "talas": "A fertile valley town of the khaganate. Here he first saw large vineyards — Xuanzang records the region's grapes and its felt-clothed, green-eyed Iranian inhabitants.",
    "samarkand": "The great Sogdian metropolis under Western Turkic overlordship. He found the people fire-worshippers (Zoroastrians); the two Buddhist monasteries stood abandoned, and the king had recently (and nominally) converted to Buddhism.",
    "iron_gate": "The Iron Gate — a narrow fortified pass between cliffs, the strategic chokepoint on the road south out of Sogdiana; iron gates hung across it, giving the pass its name.",
    "balkh": "Ancient Bactra, 'mother of cities', then under the Western Turks. A hundred viharas and 3,000 monks of the Sarvastivada school; Xuanzang stayed in Navavihara (Nava Vihara), the famed monastery where he met the aged master Prajñakara.",
    "bamyan": "The valley of the colossal Buddhas: a 55-metre standing Buddha and a 38-metre one, carved in the cliff face, with some 10 monasteries and a thousand monks of the Lokottaravada school.",
    "kapisa": "Capital of the Kabul Shahi kingdom. The Buddhist-leaning Shahi king hosted Xuanzang and a debate assembly; he passed two summers here (632/633) waiting out the snows.",
    "nagarahara": "The ancient Nagaraha (modern Jalalabad region), home of the Buddha's skull-relic shrine — Xuanzang saw monks carrying the relic in procession through the streets amid clouds of incense.",
    "gandhara": "The old Gandharan capital Purusapura (Peshawar). The great stupa of King Kanishka still stood, but he found the once-flourishing Buddhism in decay — monasteries mostly empty and ruined, a thousand years after the kings who built them.",
    "swat": "The Uddiyana valley — in Xuanzang's account the very land where Padmasambhava would later be born; he found the valley dotted with ancient stupa sites, though by his time largely given over to the laity.",
    "kashmir": "Kingdom of Kashmir. He entered via the Pir Panjal passes and studied Buddhist logic (yogācāra scholasticism) for two years under a master, and collected texts; a kingdom of some 100 monasteries and 5,000 monks.",
    "punjab": "The Takka country of the eastern Punjab. Crossing the Sutlej, he found the land laid waste — the great monasteries of the region ruined by Mihirakula's old Hūṇa wars a century before, and Brahmanism now dominant.",
    "nalanda": "The great mahāvihāra of Nalanda — the greatest centre of Buddhist learning in the world. ~1500 monks; Xuanzang studied ~5 years under the aged master Śīlabhadra, debate champion at 106 years old, mastering Yogācāra.",
    "kanauj": "King Harsha's capital on the Ganges. Xuanzang stayed ~2 years at the emperor's court; at the Kanauj assembly of 643, called in Xuanzang's honour, a heretic's arson sparked a panic and death threats against the pilgrim — Harsha suppressed it, but Xuanzang resolved to leave.",
    "prayaga": "The Prayaga mela of 643 — King Harsha's great quinquennial assembly at the Ganges–Yamuna confluence. A vast charity festival where Harsha gave away his treasury; the 75-day event ended in Brahmin arson and the emperor's intervention.",
    "kashgar": "Turning for home across the Pamirs — the 'ridge of the world'. On the descent, his elephant drowned in a gorge river chased by bandits, and many manuscript loads were lost.",
    "khotan": "The prosperous Buddhist kingdom of Khotan. Fearing the emperor's wrath for having left illegally, he sent a humble letter ahead to Taizong from here — and waited some months until a gracious reply arrived, inviting him back.",
    "loulan": "The ruined realm of Loulan around Lop Nor — by Xuanzang's time a windswept waste of buried towns on the southern Taklamakan road; he crossed its waterless flats on the last desert leg.",
    "luolan_placeholder": "",
    "dunhuang": "The frontier garrison and Buddhist centre of Shazhou, gateway of the Mogao caves, where the pilgrim re-entered Chinese territory with escort and supplies provided by the local authorities.",
    "chang_an_end": "Chang'an, February 645. Greeted by crowds so vast his entry was delayed a day. Brought ~700 Sanskrit works, relics and statues; spent his remaining 19 years translating, with the emperor's patronage, at the Great Wild Goose Pagoda.",
}
# Fix the accidentally assembled Kucha text and remove the placeholder:
NARRATIVE["kucha"] = ("Kingdom of Kucha — the great centre of Sarvastivada "
    "Buddhism. Kept for two months by King Suvarnadeva; Xuanzang out-argued "
    "the local Arhat Mokṣagupta, who conceded that Chinese Buddhism 'went far'.")
del NARRATIVE["luolan_placeholder"]

# --- translations for the other locales (kept terse) ---
NARRATIVE_FR = {
    "chang_an": "Capitale des Tang. Départ clandestin — le voyage vers l'ouest était interdit ; une famine avait vidé les routes de leurs contrôles.",
    "liangzhou": "Ville frontière ; le gouverneur Huili, sympathique, l'avertit que des mandats d'arrêt circulaient contre lui aux passes.",
    "guazhou": "Dernière ville chinoise. Sorti de nuit passe de Yumen ; son guide le trahit, son cheval mourut, et il faillit périr de soix dans le désert de Gobi.",
    "hami": "Premier royaume étranger (Yiwu). Tombé de cheval d'épuisement ; les messagers du roi le portèrent à la cour.",
    "gaochang": "Le roi bouddhiste Qu Wentai voulut le garder comme précepteur ; Xuanzang jeûna jusqu'à ce que le roi cède — puis devint son frère juré et dota le voyage d'or et de soie.",
    "kucha": "Grand centre du bouddhisme Sarvastivada. Retenu deux mois par le roi ; Xuanzang surpassa l'Arhat local Mokṣagupta en débat.",
    "karashahr": "L'ancien royaume d'Agni (Karashahr) ; son roi, parent du roi de Kucha, fournit chevaux et provisions pour la traversée suivante.",
    "aksu": "Petit royaume-oasis de Baluka ; le roi, d'origine turque, patronnait l'école Sarvastivada ; Xuanzang y enseigna la logique bouddhique.",
    "suyab": "Capitale du Khaganat turc occidental. Le khagan Tong Yabghu le reçut sur un trône de feutre au milieu de ses cavaliers et lui donna un laissez-passer.",
    "talas": "Bourgade fertile du khaganat ; Xuanzang y vit de grands vignobles et des habitants iraniens aux yeux verts.",
    "samarkand": "Grande métropole sogdienne ; le peuple adorait le feu (zoroastrisme), les deux monastères bouddhiques étaient abandonnés.",
    "iron_gate": "La Porte de Fer — étroit passage fortifié entre falaises, verrou stratégique de la route du sud.",
    "balkh": "Bactra, « mère des cités » ; cent viharas et 3 000 moines ; il séjourna au Nava Vihara auprès du vieux maître Prajñakara.",
    "bamyan": "La vallée des Bouddhas colossaux : 55 m et 38 m, taillés dans la falaise ; une dizaine de monastères, mille moines.",
    "kapisa": "Capitale du royaume Kaboul Shahi ; le roi bouddhiste l'hébergea ; il y passa deux étés à attendre la fonte des neiges.",
    "nagarahara": "L'ancienne Nagaraha (région de Jalalabad), sanctuaire de la relique du crâne du Bouddha — procession d'encens dans les rues.",
    "gandhara": "Purusapura (Peshawar), capitale de l'ancien Gandhara ; le grand stupa de Kanishka dressait, mais le bouddhisme y déclinait — monastères vides.",
    "swat": "La vallée d'Uddiyana, parsemée d'anciens stupas, largement passée aux laïcs.",
    "kashmir": "Il y étudia la logique bouddhique deux ans ; royaume d'environ cent monastères et cinq mille moines.",
    "punjab": "Le pays de Takka ; les grands monastères ruinés par les guerres des Hūṇa un siècle plus tôt ; le brahmanisme dominait désormais.",
    "nalanda": "Le grand mahāvihāra de Nalanda, plus grand centre d'études bouddhiques au monde ; cinq ans d'étude sous Śīlabhadra, doyen de 106 ans.",
    "kanauj": "Capitale du roi Harsha ; à l'assemblée de Kanauj (643), un incendie criminel et des menaces de mort poussèrent Xuanzang au départ.",
    "prayaga": "La grande assemblée de Prayaga (643) : festival de charité de Harsha au confluent Gange–Yamuna, troublé par un incendie brahmane.",
    "kashgar": "Retour par les Pamirs, « le toit du monde » ; son éléphant se noya dans une gorge, emportant une partie des manuscrits.",
    "khotan": "Royaume bouddhiste prospère ; craignant la colère de l'empereur, il y écrivit sa lettre d'excuse à Taizong et attendit la réponse ~six mois.",
    "loulan": "Le royaume en ruine de Loulan, autour du Lop Nor — à son époque une étendue désolée de villes ensablées sur la route sud du Taklamakan.",
    "dunhuang": "La place-frontière de Shazhou, porte des grottes de Mogao, où il rentra sur le territoire chinois sous escorte.",
    "chang_an_end": "Chang'an, février 645. Accueil triomphal ; ~700 ouvrages sanscrits ; 19 ans de traduction sous les auspices impériaux.",
}
NARRATIVE_ZH_HANS = {
    "chang_an": "唐朝都城。违禁西行，悄然出发——当时朝廷禁绝西行，中原饥荒使关防松弛。",
    "liangzhou": "河西重镇。凉州都督慧威法师敬其志，密遣二弟子送他西行。",
    "guazhou": "瓜州，唐朝最后一座边城。夜里偷渡玉门关，向导叛离，老马倒毙，他几乎渴死在莫贺延碛（戈壁）中。",
    "hami": "伊吾（哈密），第一外国。因极度疲惫坠马，被国王的使者救入王庭。",
    "gaochang": "高昌。笃信佛教的麴文泰国王想强留他为国师，玄奘绝食明志；国王遂与他结为兄弟，赠黄金绸缎、文书与四名沙弥。",
    "kucha": "龟兹，说一切有部的重镇。被苏伐叠国王挽留两月；与木叉毱多（Mokṣagupta）论辩胜出。",
    "karashahr": "阿耆尼国（焉耆）。北道丝路要站；国王与龟兹王同族，供给马匹粮草以度碛。",
    "aksu": "拨换国（今阿克苏），小绿洲王国；国王为突厥所立，崇奉有部；玄奘为众僧讲经。",
    "suyab": "西突厥汗庭素叶城（碎叶）。统叶护可汗坐于帐中金狼头旗下接见玄奘，并颁发给沿途诸国的通行文书。",
    "talas": "怛罗斯，汗国境内的富饶城镇；玄奘记此地葡萄茂盛，居民碧眼多须。",
    "samarkand": "康国（撒马尔罕），粟特大都会。国人事火（祆教），两所佛寺荒废；国王虽名义上皈依佛教，其民不信。",
    "iron_gate": "铁门关——两侧悬崖夹峙的狭窄要隘，出粟特南行的战略锁钥，因装有铁门而得名。",
    "balkh": "缚喝国（巴尔赫，大夏故都），「小王舍城」；百所伽蓝、三千僧众；玄奘驻锡那伽毱沙那（新寺），参谒般若羯罗长老。",
    "bamyan": "梵衍那国（巴米扬）。石崖立佛高五十五米、三十八米两尊，伽蓝十余所、僧徒千余人。",
    "kapisa": "迦毕试国，迦毕试王国的都城；崇佛的罽宾王设大会迎玄奘；在此度过两个夏天等雪化。",
    "nagarahara": "那揭罗喝国（今贾拉拉巴德一带），佛顶骨舍利寺所在地——玄奘见僧众捧舍利于街市游行，香烟如云。",
    "gandhara": "健驮罗（布路沙布逻，今白沙瓦），迦腻色迦王大塔犹存，而佛法衰微，伽蓝多颓毁芜蔓。",
    "swat": "乌仗那国（斯瓦特河谷），古圣迹遍布；至玄奘时僧徒寡少，多已还俗。",
    "kashmir": "迦湿弥罗（克什米尔）。翻越毗罗山口入国，随高僧学俱舍、因明两年，收集经典；国有伽蓝百余所、僧五千余人。",
    "dict__punjab": "",
    "punjab": "磔迦国（旁遮普东部）。信度河畔，昔匈奴王摩醯逻矩罗（Mihirakula）毁法之后，伽蓝颓坏，婆罗门教盛行。",
    "nalanda": "那烂陀寺——当时世界最大的佛学中心，僧众千余。玄奘师从百零六岁的戒贤法师，五年研习瑜伽行派（唯识）。",
    "kanauj": "羯若鞠阇国（曲女城），戒日王的都城。玄奘留住两年；643 年曲女城大会遭纵火与死亡威胁，遂决意东归。",
    "prayaga": "643 年钵罗耶伽无遮大会——戒日王在恒河与阎牟那河交汇处的大施会，七十五日倾尽府库；末遭婆罗门纵火。",
    "kashgar": "疏勒（喀什噶尔），越过葱岭（帕米尔）东归。下山时大象坠涧溺亡，损失部分经卷。",
    "khotan": "于阗，富庶的佛国。因当年违禁出关，他在此地先上表太宗请罪，等待约半年后获敕迎还。",
    "loulan": "楼兰故地（罗布泊一带）——至玄奘时已成流沙掩埋的废墟，他沿塔克拉玛干南道穿越这片无水的荒滩。",
    "dunhuang": "沙州（敦煌），佛教重镇、莫高窟门户，在此正式重返唐境，官府供应接待。",
    "chang_an_end": "长安，贞观十九年（645 年 2 月）。万人空巷，次日方能入城。携梵本经卷约六百五十七部；此后十九年在慈恩寺（大雁塔）译经。",
}
del NARRATIVE_ZH_HANS["dict__punjab"]
NARRATIVE_ZH_HANT = {
    "chang_an": "唐朝都城。違禁西行，悄然出發——當時朝廷禁絕西行，中原饑荒使關防鬆弛。",
    "liangzhou": "河西重鎮。涼州都督慧威法師敬其志，密遣二弟子送他西行。",
    "guazhou": "瓜州，唐朝最後一座邊城。夜裡偷渡玉門關，嚮導叛離，老馬倒斃，他幾乎渴死在莫賀延磧（戈壁）中。",
    "hami": "伊吾（哈密），第一外國。因極度疲憊墜馬，被國王的使者救入王庭。",
    "gaochang": "高昌。篤信佛教的麴文泰國王想強留他為國師，玄奘絕食明志；國王遂與他結為兄弟，贈黃金綢緞、文書與四名沙彌。",
    "kucha": "龜茲，說一切有部的重鎮。被蘇伐疊國王挽留兩月；與木叉毱多（Mokṣagupta）論辯勝出。",
    "karashahr": "阿耆尼國（焉耆）。北道絲路要站；國王與龜茲王同族，供給馬匹糧草以度磧。",
    "aksu": "撥換國（今阿克蘇），小綠洲王國；國王為突厥所立，崇奉有部；玄奘為眾僧講經。",
    "suyab": "西突厥汗庭素葉城（碎葉）。統葉護可汗坐於帳中接見玄奘，並頒發給沿途諸國的通行文書。",
    "talas": "怛羅斯，汗國境內的富饒城鎮；玄奘記此地葡萄茂盛，居民碧眼多鬚。",
    "samarkand": "康國（撒馬爾罕），粟特大都會。國人事火（祆教），兩所佛寺荒廢。",
    "iron_gate": "鐵門關——兩側懸崖夾峙的狹窄要隘，出粟特南行的戰略鎖鑰，因裝有鐵門而得名。",
    "balkh": "縛喝國（巴爾赫），「小王舍城」；百所伽藍、三千僧眾；玄奘參謁般若羯羅長老。",
    "bamyan": "梵衍那國（巴米揚）。石崖立佛高五十五米、三十八米兩尊，伽藍十餘所、僧徒千餘人。",
    "kapisa": "迦畢試國；崇佛的罽賓王設大會迎玄奘；在此度過兩個夏天等雪化。",
    "nagarahara": "那揭羅喝國（今賈拉拉巴德一帶），佛頂骨舍利寺——僧眾捧舍利遊行街市，香煙如雲。",
    "gandhara": "健馱羅（布路沙布邏，今白沙瓦），迦膩色迦王大塔猶存，而佛法衰微，伽藍多頹毀。",
    "swat": "烏仗那國（斯瓦特河谷），古聖跡遍布；至玄奘時僧徒寡少，多已還俗。",
    "kashmir": "迦濕彌羅（克什米爾）。隨高僧學俱舍、因明兩年；國有伽藍百餘所、僧五千餘人。",
    "punjab": "磔迦國（旁遮普東部）。昔匈奴王毀法之後，伽藍頹壞，婆羅門教盛行。",
    "nalanda": "那爛陀寺——當時世界最大的佛學中心。玄奘師從百零六歲的戒賢法師，五年研習瑜伽行派。",
    "kanauj": "羯若鞠闍國（曲女城），戒日王的都城；643 年曲女城大會遭縱火與死亡威脅，遂決意東歸。",
    "prayaga": "643 年缽羅耶伽無遮大會——戒日王在恆河與閻牟那河交匯處的大施會，七十五日傾盡府庫；末遭婆羅門縱火。",
    "kashgar": "疏勒（喀什噶爾），越過蔥嶺（帕米爾）東歸。下山時大象墜澗溺亡，損失部分經卷。",
    "khotan": "于闐，富庶的佛國。因當年違禁出關，先上表太宗請罪，等待約半年後獲敕迎還。",
    "loulan": "樓蘭故地（羅布泊一帶）——至玄奘時已成流沙掩埋的廢墟，他沿塔克拉瑪干南道穿越這片無水的荒灘。",
    "dunhuang": "沙州（敦煌），佛教重鎮、莫高窟門戶，在此正式重返唐境。",
    "chang_an_end": "長安，貞觀十九年（645 年 2 月）。萬人空巷，次日方能入城。攜梵本約六百五十七部；此後十九年譯經於慈恩寺（大雁塔）。",
}
NARRATIVE_JA = {
    "chang_an": "唐の都。出境禁止の禁を犯して密かに出発——中原の飢饉で関所の手薄な隙を突いた。",
    "liangzhou": "河西の要衝。涼州の都督は敬虔な仏教徒で、密かに二人の弟子を送って西行を助けた。",
    "guazhou": "唐最後の辺城。夜陰に玉門関を密越；案内人に裏切られ、馬も倒れ、砂漠（莫賀延磧）で幾度となく死線を彷徨った。",
    "hami": "伊吾（ハミ）、最初の異国。疲労で落馬し、王の使者に救助された。",
    "gaochang": "高昌。熱心な仏教徒の麴文泰王は国師として留めようとしたが、玄奘は断食で抗し、王は義兄弟となり金銀・絹・通行文書と四人の僧を贈った。",
    "kucha": "亀茲、説一切有部の中心。二か月滞在して木叉毱多（モクシャグプタ）との論争に勝った。",
    "karashahr": "阿耆尼国（焉耆）。シルクロード北道の要衝；王は亀茲王の同族で、次の砂漠越えの馬と食糧を供給した。",
    "aksu": "拨换国（現在のアクス）。 Oasis の小王国；突厥系の王は有部を保護し、玄奘は僧たちに因明を講じた。",
    "suyab": "西突厥の牙帳・素葉城（スヤブ）。統葉護可汗は羊毛の座に座って玄奘を引見し、諸国への通行文書を与えた。",
    "talas": "タラス。肥沃な谷の町；玄奘は葡萄の棚と碧眼多鬚の住民を記録している。",
    "samarkand": "康国（サマルカンド）、ソグドの大都。住民は火を礼拝（ゾロアスター教）し、二つの仏寺は荒廃していた。",
    "iron_gate": "鉄門——絶壁に挟まれた狭い関所、ソグドから南へ抜ける戦略の要。",
    "balkh": "縛喝国（バルフ）、「小王舎城」。百の伽藍と三千の僧；般若羯羅長老に会った。",
    "bamyan": "梵衍那国（バーミヤーン）。崖に刻まれた高さ55mと38mの大仏、十余りの僧院と千人の僧。",
    "kapisa": "迦畢試国の都。仏教を保護する王の歓迎を受け、雪解けを待って二夏を過ごした。",
    "nagarahara": "那揭羅喝国（ジャラーラーバード周辺）、仏頂骨舎利の寺——僧たちが舎利を捧げて街を練り歩くのを見た。",
    "gandhara": "犍陀羅（プルシャプラ、現在のペシャーワル）。カニシカ王の大塔は残っていたが、仏教は衰え、僧院の多くは荒れ果てていた。",
    "swat": "烏仗那国（スワート谷）。古い仏跡が点在するが、僧は少なく多くは俗に下っていた。",
    "kashmir": "迦湿弥羅（カシミール）。二年間論理（因明）を学び経典を収集；百余りの僧院と五千人の僧。",
    "punjab": "磔迦国（東パンジャーブ）。フーナ族の戦乱で大僧院は廃墟となり、バラモン教が優勢だった。",
    "nalanda": "那爛陀寺——当時世界最大の仏教教学の中心。106歳の戒賢法師に師事し、五年かけて瑜伽行派を学んだ。",
    "kanauj": "羯若鞠闍国（カナウジ）、戒日王の都。643年の大会は放火と死の脅しに見舞われ、帰国を決意した。",
    "prayaga": "643年の钵羅耶伽無遮大会——ガンジスとヤムナーの合流点での大布施会、75日間に及んだ。",
    "kashgar": "疏勒（カシュガル）。帕米爾（蔥嶺）越えの帰路、谷川で象が溺死し経巻の一部を失った。",
    "khotan": "于闐、豊かな仏教国。禁を破った出国の罪を詫びる表を太宗に奉り、半年後に入国の勅許を得た。",
    "loulan": "楼蘭の故地（ロプノール周辺）——玄奘の時代には流砂に埋もれた廃墟となっており、タクラマカン南道の最後の砂漠越えとなった。",
    "dunhuang": "沙州（敦煌）、莫高窟の門戸。ここで正式に唐の領内に戻った。",
    "chang_an_end": "長安、645年2月。群衆で入城が一日遅れた。梵本約700部を携え、のち19年を大雁塔で訳経に捧げた。",
}

TITLES = {
    "en-GB": "Xuanzang's Journey to the West (629–645)",
    "fr-CA": "Le voyage de Xuanzang vers l'Ouest (629–645)",
    "zh-Hans": "玄奘西行（629–645）",
    "zh-HK": "玄奘西行（629–645）",
    "ja": "玄奘の西への旅（629–645）",
}

STOP_NAMES = {
    # display names per locale, keyed by stop key
    "chang_an": {"en-GB": "Chang'an", "fr-CA": "Chang'an", "zh-Hans": "长安", "zh-HK": "長安", "ja": "長安"},
    "liangzhou": {"en-GB": "Liangzhou", "fr-CA": "Liangzhou", "zh-Hans": "凉州", "zh-HK": "涼州", "ja": "涼州"},
    "guazhou": {"en-GB": "Guazhou", "fr-CA": "Guazhou", "zh-Hans": "瓜州", "zh-HK": "瓜州", "ja": "瓜州"},
    "hami": {"en-GB": "Hami (Yiwu)", "fr-CA": "Hami (Yiwu)", "zh-Hans": "伊吾（哈密）", "zh-HK": "伊吾（哈密）", "ja": "伊吾（ハミ）"},
    "gaochang": {"en-GB": "Gaochang", "fr-CA": "Gaochang", "zh-Hans": "高昌", "zh-HK": "高昌", "ja": "高昌"},
    "karashahr": {"en-GB": "Karashahr (Agni)", "fr-CA": "Karashahr (Agni)", "zh-Hans": "焉耆", "zh-HK": "焉耆", "ja": "焉耆"},
    "kucha": {"en-GB": "Kucha", "fr-CA": "Kucha", "zh-Hans": "龟兹", "zh-HK": "龜茲", "ja": "亀茲"},
    "aksu": {"en-GB": "Aksu (Baluka)", "fr-CA": "Aksu (Baluka)", "zh-Hans": "阿克苏", "zh-HK": "阿克蘇", "ja": "アクス"},
    "suyab": {"en-GB": "Suyab", "fr-CA": "Suyab", "zh-Hans": "碎叶", "zh-HK": "碎葉", "ja": "素葉城"},
    "talas": {"en-GB": "Talas", "fr-CA": "Talas", "zh-Hans": "怛罗斯", "zh-HK": "怛羅斯", "ja": "タラス"},
    "samarkand": {"en-GB": "Samarkand", "fr-CA": "Samarkand", "zh-Hans": "撒马尔罕", "zh-HK": "撒馬爾罕", "ja": "サマルカンド"},
    "iron_gate": {"en-GB": "Iron Gate", "fr-GB": "Porte de Fer", "fr-CA": "Porte de Fer", "zh-Hans": "铁门关", "zh-HK": "鐵門關", "ja": "鉄門"},
    "balkh": {"en-GB": "Balkh", "fr-CA": "Balkh", "zh-Hans": "巴尔赫", "zh-HK": "巴爾赫", "ja": "バルフ"},
    "bamyan": {"en-GB": "Bamyan", "fr-CA": "Bâmiyân", "zh-Hans": "巴米扬", "zh-HK": "巴米揚", "ja": "バーミヤーン"},
    "kapisa": {"en-GB": "Kapisa", "fr-CA": "Kapisa", "zh-Hans": "迦毕试", "zh-HK": "迦畢試", "ja": "迦畢試"},
    "nagarahara": {"en-GB": "Nagarahara", "fr-CA": "Nagarahara", "zh-Hans": "那揭罗喝", "zh-HK": "那揭羅喝", "ja": "那揭羅喝"},
    "gandhara": {"en-GB": "Gandhara (Peshawar)", "fr-CA": "Gandhara (Peshawar)", "zh-Hans": "犍陀罗（白沙瓦）", "zh-HK": "犍陀羅（白沙瓦）", "ja": "犍陀羅（ペシャーワル）"},
    "swat": {"en-GB": "Swat (Uddiyana)", "fr-CA": "Swat (Uddiyana)", "zh-Hans": "乌仗那（斯瓦特）", "zh-HK": "烏仗那（斯瓦特）", "ja": "烏仗那（スワート）"},
    "kashmir": {"en-GB": "Kashmir", "fr-CA": "Cachemire", "zh-Hans": "克什米尔", "zh-HK": "克什米爾", "ja": "カシミール"},
    "punjab": {"in-GB": "Punjab (Takka)", "en-GB": "Punjab (Takka)", "fr-CA": "Pendjab (Takka)", "zh-Hans": "旁遮普（磔迦）", "zh-HK": "旁遮普（磔迦）", "ja": "パンジャーブ（磔迦）"},
    "nalanda": {"en-GB": "Nalanda", "fr-CA": "Nâlandâ", "zh-Hands": "那烂陀", "zh-Hans": "那烂陀", "zh-HK": "那爛陀", "ja": "那爛陀"},
    "kanauj": {"en-GB": "Kanauj", "fr-CA": "Kanauj", "zh-Hans": "曲女城", "zh-HK": "曲女城", "ja": "カナウジ"},
    "prayaga": {"en-GB": "Prayaga", "fr-CA": "Prayaga", "zh-Hans": "钵罗耶伽", "zh-HK": "缽羅耶伽", "ja": "プラヤーガ"},
    "kashgar": {"en-GB": "Kashgar", "fr-CA": "Kachgar", "zh-Hans": "疏勒", "zh-HK": "疏勒", "ja": "カシュガル"},
    "khotan": {"en-GB": "Khotan", "fr-CA": "Khotan", "zh-Hans": "于阗", "zh-HK": "于闐", "ja": "于闐（コータン）"},
    "loulan": {"en-GB": "Loulan (Miran)", "fr-CA": "Loulan (Miran)", "zh-Hans": "楼兰（米兰）", "zh-HK": "樓蘭（米蘭）", "ja": "楼蘭（ミーラン）"},
    "dunhuang": {"en-GB": "Dunhuang", "fr-CA": "Dunhuang", "zh-Hans": "敦煌", "zh-HK": "敦煌", "ja": "敦煌"},
    "chang_an_end": {"en-GB": "Chang'an", "fr-CA": "Chang'an", "zh-Hans": "长安", "zh-HK": "長安", "ja": "長安"},
}


def fetch_all_coords(stops):
    """One batched wbgetentities call for all QIDs: {key: coords}."""
    qids = [qid for _, qid, _, _ in stops]
    coords, labels = {}, {}
    for i in range(0, len(qids), 50):
        chunk = qids[i:i + 50]
        url = ("https://www.wikidata.org/w/api.php?action=wbgetentities"
               f"&ids={'|'.join(chunk)}&props=labels|claims&languages=en&format=json")
        for attempt in range(6):
            try:
                req = urllib.request.Request(url, headers=UA)
                with urllib.request.urlopen(req, timeout=30) as r:
                    data = json.load(r)
                break
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < 5:
                    time.sleep(5 * (attempt + 1))
                    continue
                raise
        for qid, ent in data.get("entities", {}).items():
            labels[qid] = ent.get("labels", {}).get("en", {}).get("value", "")
            for snak in ent.get("claims", {}).get("P625", []):
                dv = snak.get("mainsnak", {}).get("datavalue")
                if dv and "value" in dv:
                    v = dv["value"]
                    coords[qid] = [v["longitude"], v["latitude"]]
                    break
        time.sleep(1.5)
    return coords, labels


def main():
    _load_content()
    # country names for the test modes, from the vendored CLDR files
    # (raw cldr-json structure: main.<locale>...territories, keyed alpha-2)
    ISO3_TO_A2 = {"CHN": "CN", "KGZ": "KG", "KAZ": "KZ", "UZB": "UZ",
                  "AFG": "AF", "PAK": "PK", "IND": "IN"}
    cldr_files = {
        "en-GB": ROOT / "tools/cldr-en.json",
        "fr-CA": ROOT / "tools/cldr-fr-CA.json",
        "zh-Hans": ROOT / "tools/cldr-zh-Hans.json",
        "zh-HK": ROOT / "tools/cldr-zh-Hant-HK.json",
        "ja": ROOT / "tools/cldr-ja.json",
    }
    country_names = {}  # iso3 -> {locale: name}
    territories = {}  # locale -> {alpha2: name}
    for loc, path in cldr_files.items():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            main = next(iter(data["main"].values()))
            territories[loc] = main["localeDisplayNames"]["territories"]
        except (FileNotFoundError, KeyError, StopIteration) as e:
            print(f"CLDR problem for {loc}: {e}", file=sys.stderr)
    for iso3 in {s[3] for s in STOPS}:
        a2 = ISO3_TO_A2[iso3]
        country_names[iso3] = {loc: t[a2] for loc, t in territories.items() if a2 in t}

    lesson = {
        "id": "xuanzang-journey",
        "type": "journey",
        "title": TITLES,
        "view": {"lon0": 55, "lat0": 5, "lon1": 125, "lat1": 55},
        "stops": [],
        "route_out": [],
        "route_back": [],
        "countries": [],
    }
    stops_meta = []
    print("Geocoding stops from Wikidata…")
    coords_by_qid, labels_by_qid = fetch_all_coords(STOPS)
    for key, qid, year, iso3 in STOPS:
        coords = coords_by_qid.get(qid)
        label = labels_by_qid.get(qid, "")
        if coords is None:
            print(f"  FAIL {key}: no P625 on {qid} ({label})", file=sys.stderr)
            return 1
        print(f"  {key:14s} {qid} {coords}  «{label}»")
        stops_meta.append({"key": key, "qid": qid, "coords": coords,
                           "year": year, "iso3": iso3, "label": label})
    # verify identity by eyeball list above; bail if anything is null-island
    for s in stops_meta:
        assert -180 <= s["coords"][0] <= 180 and -90 <= s["coords"][1] <= 90
    # cross-check: label must mention a plausible token
    EXPECT = {
        "chang_an": ["xi'an", "xian", "chang'an"], "liangzhou": ["wuwei", "liangzhou"],
        "guazhou": ["guazhou", "gua"], "hami": ["hami", "kumul", "yiwu"],
        "gaochang": ["gaochang", "karahoja", "turpan", "qocho"], "karashahr": ["karashahr", "karasahr", "yanqi", "agni", "korla"],
        "kucha": ["kucha"], "aksu": ["aksu", "akesu"],
        "suyab": ["suyab", "ak-beshim"], "talas": ["talas", "taraz"],
        "samarkand": ["samarkand"], "iron_gate": ["iron gate", "buzgala", "derbent"],
        "balkh": ["balkh", "bactra"], "bamyan": ["bamyan", "bamiyan"],
        "kapisa": ["kapisa", "kapisa", "begram"], "nagarahara": ["nagarahara", "jalalabad", "nagaraha"],
        "gandhara": ["gandhara", "peshawar"], "swat": ["swat", "uddiyana"],
        "kashmir": ["kashmir", "jammu"], "punjab": ["punjab"],
        "nalanda": ["nalanda"], "kanauj": ["kanauj", "kannauj"],
        "prayaga": ["prayaga", "prayagraj", "allahabad"], "kashgar": ["kashgar", "kashi"],
        "khotan": ["khotan", "hotan", "hetian"], "loulan": ["loulan", "miran"],
        "dunhuang": ["dunhuang"], "chang_an_end": ["xi'an", "xian", "chang'an"],
    }
    bad = []
    for s in stops_meta:
        toks = EXPECT[s["key"]]
        if not any(t in s["label"].lower() for t in toks):
            bad.append((s["key"], s["label"]))
    if bad:
        print("IDENTITY MISMATCH — fix QIDs before shipping:", bad, file=sys.stderr)
        return 1

    for s in stops_meta:
        when_loc = {"en-GB": WHEN.get(s["key"], s["year"])}
        present_loc = dict(PRESENT.get(s["key"]) or {})
        for loc in ("fr-CA", "zh-Hans", "zh-HK", "ja"):
            m = META_I18N.get(loc, {})
            if s["key"] in m.get("when", {}):
                when_loc[loc] = m["when"][s["key"]]
            if s["key"] in m.get("present", {}):
                present_loc[loc] = m["present"][s["key"]]
        stop = {
            "id": s["key"],
            "coords": s["coords"],
            "year": s["year"],
            "when": when_loc,
            "present": present_loc,
            "iso3": s["iso3"],
            "names": STOP_NAMES.get(s["key"], {}),
            "narrative": {
                "en-GB": NARRATIVE_RICH["en-GB"].get(s["key"], [NARRATIVE[s["key"]]]),
                "fr-CA": NARRATIVE_RICH["fr-CA"].get(s["key"], [NARRATIVE_FR[s["key"]]]),
                "zh-Hans": NARRATIVE_RICH["zh-Hans"].get(s["key"], [NARRATIVE_ZH_HANS[s["key"]]]),
                "zh-HK": NARRATIVE_RICH["zh-HK"].get(s["key"], [NARRATIVE_ZH_HANT[s["key"]]]),
                "ja": NARRATIVE_RICH["ja"].get(s["key"], [NARRATIVE_JA[s["key"]]]),
            },
        }
        lesson["stops"].append(stop)

    # Build routes cleanly: nalanda is the last outbound stop; everything
    # after it is the return leg (which starts back at nalanda itself)
    nalanda_idx = next(i for i, s in enumerate(STOPS) if s[0] == "nalanda")
    out_keys = [s[0] for s in STOPS[:nalanda_idx + 1]]
    back_keys = ["nalanda"] + [s[0] for s in STOPS[nalanda_idx + 1:]]
    by_key = {s["key"]: s for s in stops_meta}
    lesson["route_out"] = [by_key[k]["coords"] for k in out_keys]
    lesson["route_back"] = [by_key[k]["coords"] for k in back_keys]

    # countries along the route for the test modes
    seen = []
    for s in stops_meta:
        if s["iso3"] not in seen:
            seen.append(s["iso3"])
    lesson["countries"] = [
        {"iso3": iso3, "names": country_names.get(iso3, {})}
        for iso3 in seen
    ]

    out = ROOT / "lessons/xuanzang/journey.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(lesson, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(lesson['stops'])} stops, "
          f"{len(lesson['route_out'])}+{len(lesson['route_back'])} route pts, "
          f"{len(seen)} countries)")
    # script twin for file://
    js = (f'window.ATLAS_LESSONS["lessons/xuanzang/journey.json"] = '
          + json.dumps(lesson, ensure_ascii=False) + ";\n")
    (out.parent / "journey.js").write_text(
        "window.ATLAS_LESSONS = window.ATLAS_LESSONS || {};\n" + js, encoding="utf-8")
    print("wrote lessons/xuanzang/journey.js")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
