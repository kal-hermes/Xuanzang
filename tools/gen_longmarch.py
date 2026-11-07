#!/usr/bin/env python3
"""Generate lessons/longmarch/journey.{json,js} — Central Red Army (First Front
Army) Long March, Oct 1934 -> Oct 1935.

Waypoints and dates: zh.wikipedia 长征 (Good Article) 红一方面军 sections,
cross-checked with en.wikipedia Long March. Coordinates: Wikidata P625 where
available (泸定桥, 腊子口, 于都, 安顺场, 瑞金, 吴起, 会理, 冕宁, 黎平, 通道,
哈达铺), else town-level coordinates (±0.05 deg, fine at app zoom).
Narratives: zh-Hans source; other locales filled by translate_longmarch.py.

Route policy (declared in the lesson): stops are documented events with
precise coordinates; connecting segments are indicative corridors from
published memorial route maps, not surveyed tracks.
"""
import json
import math
import os

S = []  # (id, lon, lat, year, date_str, present_zh, names_zh, [3 paras zh])

def stop(sid, lon, lat, year, date, present, name, paras):
    S.append(dict(id=sid, coords=[lon, lat], year=year, date=date,
                  present=present, name=name, paras=paras))

stop("ruijin", 116.033, 25.883, 1934, "1934年10月上旬",
     "江西省瑞金市", "瑞金",
     ["瑞金是中华苏维埃共和国的首都，中央革命根据地的政治中心。",
      "1934年9月，国民党军队以百万兵力推进第五次“围剿”的堡垒封锁战略，中央苏区只剩瑞金、于都、兴国等几个县的狭小地带。",
      "10月初，博古、李德等中共中央领导人决定放弃中央苏区，主力红军向西转移，与湘西的红二、六军团会合。"])
stop("yudu", 115.487, 25.958, 1934, "1934年10月17日",
     "江西省于都县", "于都",
     ["中央红军主力一、三、五、八、九军团及机关共8.6万余人，从长汀、瑞金、兴国等地向于都集结。",
      "10月17日傍晚，红军从于都县的八个渡口渡过贡水，迈出了长征的第一步。",
      "1.6万余人的红二十四师和地方部队留在苏区，在项英、陈毅领导下开始南方三年游击战争。"])
stop("xiangjiang", 110.67, 25.61, 1934, "1934年11月27日—12月1日",
     "广西兴安县、全州县之间", "湘江战役",
     ["红军突破前三道封锁线后西进，11月下旬从广西兴安、全州之间抢渡湘江。",
      "11月27日至12月1日，红军苦战五昼夜突破第四道封锁线。携带大量辎重的队伍行动迟缓，付出了惨重代价。",
      "湘江战役后，出发时的8万余中央红军锐减到3万余人。红三十四师在湘江东岸全军覆没。"])
stop("laoshanjie", 110.48, 25.92, 1934, "1934年12月上旬",
     "广西龙胜各族自治县（越城岭）", "老山界",
     ["湘江之后，红军从龙胜翻越老山界——越城岭的主峰地带，这是长征路上第一座真正的高山。",
      "博古、李德此时仍坚持去湘西与红二、六军团会合，而国民党军已在那里布下口袋。",
      "红军进入少数民族聚居区，开始执行民族政策，为后来通过彝族、藏族地区积累经验。"])
stop("tongdao", 109.778, 26.158, 1934, "1934年12月12日",
     "湖南省通道侗族自治县", "通道会议",
     ["12月12日，中共中央在湖南通道召开紧急会议。",
      "毛泽东第一次在会上提出：放弃去湘西的计划，转兵向西进入敌人力量薄弱的贵州。",
      "这个主张得到多数领导人认可，红军由此改变方向，史称“通道转兵”。"])
stop("liping", 109.133, 26.236, 1934, "1934年12月18日",
     "贵州省黎平县", "黎平会议",
     ["12月13日红军占领黎平，18日中央政治局在此召开黎平会议。",
      "会议正式肯定毛泽东转兵贵州的主张，决定向川黔边发展，放弃了原定的湘西会合计划。",
      "黎平会议是通道转兵的延续，红军的战略方向第一次摆脱了博古、李德的既定方案。"])
stop("wujiang", 107.62, 27.17, 1935, "1935年1月初",
     "贵州省瓮安县江界河渡口", "强渡乌江",
     ["1935年1月初，红军强渡乌江天险，突破黔军防线。",
      "乌江是贵州的第一大江，江面宽、水流急，黔军在对岸设防。红军以竹筏强渡，攻占渡口。",
      "渡过乌江，通向遵义的大门打开了。"])
stop("zunyi", 106.925, 27.725, 1935, "1935年1月15日—17日",
     "贵州省遵义市", "遵义会议",
     ["1月7日红军占领遵义城。15日至17日，中共中央政治局在此召开扩大会议，史称遵义会议。",
      "会议检讨第五次反围剿以来的军事路线，取消博古、李德的最高军事指挥权，增补毛泽东为政治局常委，恢复对红军的指挥。",
      "遵义会议是中国革命史上最关键的转折点之一：红军此后的行军路线，由这次会议确定的领导格局来主导。"])
stop("tucheng", 106.06, 28.27, 1935, "1935年1月28日—29日",
     "贵州省习水县土城镇", "土城之战与一渡赤水",
     ["遵义会议后，红军计划北渡长江与红四方面军会合。1月24日攻占土城。",
      "1月28日，红军在土城以北的青杠坡进攻川军郭勋祺部，激战一日打成僵局，损失上千人，北渡计划受挫。",
      "1月29日，红军从猿猴场、土城等渡口一渡赤水河，进入川南。"])
stop("zhaxi", 105.04, 27.85, 1935, "1935年2月5日—9日",
     "云南省威信县（扎西）", "扎西会议",
     ["红军进入云贵川三省交界的扎西地域（云南威信），中央政治局连续召开会议。",
      "扎西会议决定：张闻天取代博古负总责；暂缓渡江入川，回兵黔北；部队整编为十六个团。",
      "此时蒋介石调集吴奇伟、周浑元、孙渡等部，准备在川南围歼红军。"])
stop("taipingdu", 105.83, 28.09, 1935, "1935年2月18日—21日",
     "四川省古蔺县太平渡", "二渡赤水",
     ["2月10日，毛泽东决定东进。18日至21日，红军从太平渡、二郎滩东渡赤水河，杀了个回马枪。",
      "这次回师黔北完全出乎国民党军意料，红军五天内连克桐梓、娄山关、遵义。",
      "二渡赤水是四渡赤水中战果最大的一次：红军取得了长征以来最大的一场胜利。"])
stop("loushanguan", 106.83, 27.95, 1935, "1935年2月25日—28日",
     "贵州省遵义市娄山关", "娄山关大捷",
     ["2月25日，红三军团激战夺取娄山关天险，随后再占遵义城，击溃吴奇伟纵队。",
      "娄山关之战是长征以来最大的胜利，但红三军团参谋长邓萍阵亡。",
      "毛泽东在此役后写下《忆秦娥·娄山关》：\u201c雄关漫道真如铁，而今迈步从头越\u201d。"])
stop("maotai", 106.20, 27.79, 1935, "1935年3月16日",
     "贵州省仁怀市茅台镇", "三渡赤水",
     ["3月15日，红军围攻鲁班场的周浑元部失利，次日由茅台渡口西渡赤水。",
      "蒋介石判断红军要北渡长江，急调大军到川南堵截。",
      "三渡赤水是一次“示形”行动：一个团伪装主力大张旗鼓西进，主力却在附近隐蔽待机。"])
stop("erlangtan", 105.95, 28.08, 1935, "1935年3月21日",
     "四川省古蔺县二郎滩", "四渡赤水",
     ["3月21日，红军主力突然掉头，从二郎滩、九溪口、太平渡四渡赤水，秘密东返。",
      "国军重兵集团被甩在川南扑空。3月29日至31日，红军南渡乌江，跳出包围圈。",
      "四渡赤水被毛泽东本人视为一生的“得意之笔”。负责掩护的红九军团被迫独立行动，转战52天后才在西昌归队。"])
stop("guiyang", 106.63, 26.65, 1935, "1935年4月2日",
     "贵州省贵阳市", "兵临贵阳",
     ["4月2日，红军主力突然逼近贵阳，直接威胁贵阳机场，而蒋介石此时正在贵阳督战。",
      "蒋介石急调滇军孙渡部星夜驰援——这正是毛泽东要的效果：滇军东调，云南门户洞开。",
      "红军并不攻城，4月8日从贵阳、龙里间突然穿过防线，以每天百余里的速度向云南疾进。"])
stop("xundian", 102.91, 25.56, 1935, "1935年4月29日",
     "云南省寻甸回族彝族自治县", "进入云南",
     ["4月23日红军越过黄泥河分两路进入云南。龙云把主力收缩到昆明防守。",
      "昆明的收缩让开了一条向西的通道：红军的目标是金沙江渡口。",
      "4月29日中革军委发布指示：迅速渡过金沙江，转入川西。"])
stop("jiaopingdu", 102.30, 26.19, 1935, "1935年5月1日—9日",
     "云南省禄劝县皎平渡", "巧渡金沙江",
     ["5月1日至9日，中央红军在禄劝皎平渡渡过金沙江——这是长征中最从容的一次渡江。",
      "先遣队化装成国军缴获了两只渡船，随后又找到五只。37名船工轮流摇桨，七只小船九天九夜运送了两万人过江。",
      "等国民党追军赶到江边时，红军已经烧掉渡船走远。第一方面军第一次摆脱了几十万追兵。"])
stop("huili", 102.247, 26.661, 1935, "1935年5月12日",
     "四川省会理县", "会理会议",
     ["5月12日，中央政治局在会理城郊召开会议。",
      "会上批评了林彪“尽走弓背路”的怀疑，统一了继续机动作战的决心，并确定与红四方面军会师的目标。",
      "红军在此短暂休整后，开始向大渡河方向进军——那是一条石达开曾经全军覆没的路线。"])
stop("mianning", 102.169, 28.552, 1935, "1935年5月20日—22日",
     "四川省冕宁县", "彝海结盟",
     ["5月20日红军攻占冕宁。先遣队司令刘伯承与彝族沽基家支首领小叶丹在彝海边歃血为盟。",
      "红军执行民族政策，宣传各民族平等，彝族同胞护送红军通过了彝区。",
      "彝海结盟使红军赢得了宝贵的时间——此后到达的国民党追兵再也没有说服彝族放行。"])
stop("anshunchang", 102.283, 29.277, 1935, "1935年5月25日",
     "四川省石棉县安顺场", "十七勇士强渡大渡河",
     ["5月24日夜，红军先遣队急行军袭占安顺场渡口——70年前石达开在这里全军覆没。",
      "5月25日清晨，十七勇士乘一只小船在机枪掩护下强渡大渡河，占领对岸阵地。",
      "但船只太少，全军无法迅速过河。红军随即兵分两路：一师在此渡河，主力沿河西岸兼程北上泸定桥。"])
stop("ludingqiao", 102.230, 29.915, 1935, "1935年5月29日",
     "四川省泸定县泸定桥", "飞夺泸定桥",
     ["红二师四团接到命令：三天内赶到320里外的泸定桥。他们冒雨一昼夜行军240里，创造了红军行军的纪录。",
      "5月29日，22名突击队员攀着悬空的铁索冲向对岸，夺下泸定桥。两岸部队在桥头会合。",
      "泸定桥保住了红军北上的通道。陈云由此离队前往莫斯科，向共产国际汇报遵义会议。"])
stop("tianquan", 102.76, 30.06, 1935, "1935年6月7日",
     "四川省天全县", "翻二郎山、占天全",
     ["红军渡过大渡河后东翻二郎山，突破川军杨森部六个旅的阻击。",
      "6月7日占领天全，随后经芦山、宝兴北进。",
      "前面等待他们的是长征路上第一座终年积雪的大雪山。"])
stop("jiajinshan", 102.69, 30.72, 1935, "1935年6月8日—11日",
     "四川省宝兴县—懋功县界（夹金山垭口）", "翻越夹金山",
     ["夹金山海拔约4500米，终年积雪，空气稀薄，天气变幻无常，没有道路也没有人烟。",
      "红军战士多数来自南方，穿着单衣草鞋翻越雪山，一些人因冻、饿、力竭倒在雪地里。",
      "翻过夹金山，前方山谷里传来了消息：红四方面军的部队就在山下。"])
stop("dawei", 102.53, 30.94, 1935, "1935年6月12日",
     "四川省小金县达维镇", "达维会师",
     ["6月12日，中央红军先头部队在懋功达维与红四方面军先头部队会师。",
      "两支红军部队在桥头相拥，欢呼声响彻山谷——历尽千辛万苦的中央红军终于见到了友军。",
      "会师时中央红军已从出发时的8.6万人减员到约2万人。"])
stop("lianghekou", 102.44, 31.32, 1935, "1935年6月26日",
     "四川省小金县两河口镇", "两河口会议",
     ["6月26日，张国焘赶到两河口，与中共中央政治局委员们开会。",
      "会议决定红军共同北上，建立川陕甘苏区。但张国焘与中央的分歧就此埋下。",
      "由于战略争论，红军在此滞留过久，松潘大路被国军胡宗南部占领，红军只能转向西边的雪山草地。"])
stop("maoergai", 103.42, 32.14, 1935, "1935年8月20日",
     "四川省松潘县毛儿盖", "毛儿盖会议",
     ["8月，红军混编为左右两路军过草地，中共中央随右路军行动。",
      "8月20日毛儿盖会议决定：以岷州为中心的洮河流域为发展方向，向东发展。",
      "从毛儿盖出发，红军进入了长征中最艰苦的一段路——松潘草地。"])
stop("caodi", 103.05, 33.35, 1935, "1935年8月中下旬",
     "四川省若尔盖县（松潘草地）", "穿越松潘草地",
     ["松潘草地是海拔3500米以上的高原湿地，草甸下是泥沼，荒无人烟，无处补给。",
      "红军经受了高原反应、饮水中毒、饥渴、湿冷和极端天气的极限考验，许多人陷入泥沼再也没能起来。",
      "走出草地的部队几乎耗尽了体力——但甘南的门户打开了。"])
stop("baozo", 103.68, 33.72, 1935, "1935年8月26日—29日",
     "四川省若尔盖县包座", "包座战役",
     ["8月26日，走出草地的红军发动包座战役，击溃胡宗南部第四十九师。",
      "包座之战打开了进军甘南的门户，还缴获了大批粮食弹药——对刚出草地的红军至关重要。",
      "然而张国焘此时坚持南下，一场更大的分裂危机正在逼近。"])
stop("baxi", 103.38, 33.90, 1935, "1935年9月9日",
     "四川省若尔盖县巴西乡", "巴西会议",
     ["9月9日，张国焘电令右路军南下。毛泽东、张闻天、博古连夜赶到巴西，召开政治局紧急会议。",
      "会议决定：中央率一、三军团单独北上——这是与张国焘分裂的决定时刻。",
      "北上支队当时只有约八千人，面临的是尚未征服的雪山、隘口和甘肃的国民党军。"])
stop("ejie", 103.36, 34.07, 1935, "1935年9月12日",
     "甘肃省迭部县俄界（高吉村）", "俄界会议",
     ["9月12日，中央政治局在甘南迭部的俄界召开扩大会议。",
      "会议将北上部队改编为中国工农红军陕甘支队：彭德怀任司令员，毛泽东任政委。",
      "俄界会议之后，这支小部队向腊子口天险进发——那是一道只有几十米宽的隘口。"])
stop("lazikou", 103.894, 34.109, 1935, "1935年9月17日",
     "甘肃省迭部县腊子口", "攻克腊子口",
     ["腊子口是岷山山脉的一道隘口，两边绝壁，中间一道激流上的木桥，鲁大昌部凭险据守。",
      "红军正面强攻受阻后，一名苗族战士攀上绝壁，带人从山顶居高临下攻击，守军崩溃。",
      "9月17日攻克腊子口，红军进入甘南平原的门户打开了。"])
stop("hadapu", 104.224, 34.232, 1935, "1935年9月18日—20日",
     "甘肃省宕昌县哈达铺", "哈达铺：找到去向",
     ["红军进占哈达铺，在这里的邮政所报纸上，毛泽东读到了刘志丹陕甘根据地仍然存在的消息。",
      "长征出发时并没有确定的目的地。在哈达铺，中共中央第一次明确了长征的最终去向：陕北。",
      "部队在哈达铺整编休整，恢复了体力——“到陕北去”从此成为全军的目标。"])
stop("bangluo", 105.06, 35.14, 1935, "1935年9月27日",
     "甘肃省通渭县榜罗镇", "榜罗镇会议",
     ["9月27日，中央政治局在榜罗镇召开会议，正式确定把陕甘根据地作为长征的落脚点。",
      "9月29日部队东进，越过国军在武山、漳县间的封锁线，渡过渭河。",
      "长征的终点就在前方——但还要翻过最后一座大山。"])
stop("liupanshan", 106.21, 35.40, 1935, "1935年10月7日",
     "宁夏固原市隆德县—六盘山", "翻越六盘山",
     ["10月7日，红军翻越六盘山——长征路上翻越的最后一座大山。",
      "毛泽东在山上吟成《清平乐·六盘山》：\u201c不到长城非好汉，屈指行程二万\u201d。",
      "翻过六盘山，就是陕北黄土高原的沟壑地带。"])
stop("wuqi", 108.172, 36.925, 1935, "1935年10月19日",
     "陕西省延安市吴起县", "吴起镇：长征结束",
     ["10月19日，陕甘支队抵达陕北吴起镇——中央红军的长征到此结束。",
      "从于都渡河算起，中央红军历时368天，转战11个省，行程二万余华里，这就是“二万五千里长征”名称的由来。",
      "到达吴起时中央红军不足八千人。11月与红十五军团会合，中国共产党进入延安时期。"])

WHEN = {
    "en-GB": None,  # built from zh date programmatically
}

EN_NAMES = {
    "ruijin": "Ruijin", "yudu": "Yudu", "xiangjiang": "Xiang River battle",
    "laoshanjie": "Laoshanjie (Yuecheng Ling)", "tongdao": "Tongdao Conference",
    "liping": "Liping Conference", "wujiang": "Wu River crossing",
    "zunyi": "Zunyi Conference", "tucheng": "Tucheng & first Chishui crossing",
    "zhaxi": "Zhaxi Conference", "taipingdu": "Second Chishui crossing (Taipingdu)",
    "loushanguan": "Loushanguan victory", "maotai": "Third Chishui crossing (Maotai)",
    "erlangtan": "Fourth Chishui crossing (Erlangtan)", "guiyang": "Approach to Guiyang",
    "xundian": "Into Yunnan (Xundian)", "jiaopingdu": "Jinsha River crossing (Jiaopingdu)",
    "huili": "Huili Conference", "mianning": "Yihai alliance",
    "anshunchang": "Anshunchang crossing", "ludingqiao": "Luding Bridge",
    "tianquan": "Tianquan", "jiajinshan": "Crossing Jiajin Mountain",
    "dawei": "Dawei junction with the 4th Front Army", "lianghekou": "Lianghekou Conference",
    "maoergai": "Mao'ergai Conference", "caodi": "Crossing the Songpan grasslands",
    "baozo": "Baozo battle", "baxi": "Baxi Conference", "ejie": "Ejie Conference",
    "lazikou": "Lazikou Pass", "hadapu": "Hadapu", "bangluo": "Bangluo Conference",
    "liupanshan": "Crossing Liupan Mountain", "wuqi": "Wuqi — end of the march",
}
JA_NAMES = {
    "ruijin": "瑞金", "yudu": "于都", "xiangjiang": "湘江戦役",
    "laoshanjie": "老山界", "tongdao": "通道会議", "liping": "黎平会議",
    "wujiang": "烏江強行渡河", "zunyi": "遵義会議", "tucheng": "土城の戦いと一渡赤水",
    "zhaxi": "扎西会議", "taipingdu": "二渡赤水（太平渡）", "loushanguan": "婁山関の勝利",
    "maotai": "三渡赤水（茅台）", "erlangtan": "四渡赤水（二郎灘）", "guiyang": "貴陽への接近",
    "xundian": "雲南入り（尋甸）", "jiaopingdu": "皎平渡（金沙江渡河）", "huili": "会理会議",
    "mianning": "彝海同盟", "anshunchang": "安順場強行渡河", "ludingqiao": "飛奪瀘定橋",
    "tianquan": "天全", "jiajinshan": "夾金山越え", "dawei": "達維会師",
    "lianghekou": "両河口会議", "maoergai": "毛児蓋会議", "caodi": "松潘草地横断",
    "baozo": "包座戦役", "baxi": "巴西会議", "ejie": "俄界会議",
    "lazikou": "臘子口攻略", "hadapu": "哈達鋪", "bangluo": "榜羅鎮会議",
    "liupanshan": "六盤山越え", "wuqi": "呉起鎮：長征の終わり",
}
PRESENT_EN = {
    "ruijin": "Ruijin, Jiangxi, China", "yudu": "Yudu, Jiangxi, China",
    "xiangjiang": "Xing'an–Quanzhou, Guangxi, China",
    "laoshanjie": "Longsheng, Guangxi, China", "tongdao": "Tongdao, Hunan, China",
    "liping": "Liping, Guizhou, China", "wujiang": "Weng'an, Guizhou, China",
    "zunyi": "Zunyi, Guizhou, China", "tucheng": "Xishui, Guizhou, China",
    "zhaxi": "Weixin, Yunnan, China", "taipingdu": "Gulin, Sichuan, China",
    "loushanguan": "Zunyi, Guizhou, China", "maotai": "Renhuai, Guizhou, China",
    "erlangtan": "Gulin, Sichuan, China", "guiyang": "Guiyang, Guizhou, China",
    "xundian": "Xundian, Yunnan, China", "jiaopingdu": "Luquan, Yunnan, China",
    "huili": "Huili, Sichuan, China", "mianning": "Mianning, Sichuan, China",
    "anshunchang": "Shimian, Sichuan, China", "ludingqiao": "Luding, Sichuan, China",
    "tianquan": "Tianquan, Sichuan, China", "jiajinshan": "Baoxing–Xiaojin border, Sichuan, China",
    "dawei": "Xiaojin, Sichuan, China", "lianghekou": "Xiaojin, Sichuan, China",
    "maoergai": "Songpan, Sichuan, China", "caodi": "Zoige (Ruoergai), Sichuan, China",
    "baozo": "Zoige (Ruoergai), Sichuan, China", "baxi": "Zoige (Ruoergai), Sichuan, China",
    "ejie": "Diebu, Gansu, China", "lazikou": "Diebu, Gansu, China",
    "hadapu": "Dangchang, Gansu, China", "bangluo": "Tongwei, Gansu, China",
    "liupanshan": "Ningxia–Gansu border, China", "wuqi": "Wuqi, Shaanxi, China",
}
PRESENT_JA = {
    "ruijin": "中国江西省瑞金市", "yudu": "中国江西省于都県",
    "xiangjiang": "中国広西チワン族自治区興安県・全州県", "laoshanjie": "中国広西チワン族自治区竜勝県",
    "tongdao": "中国湖南省通道県", "liping": "中国貴州省黎平県",
    "wujiang": "中国貴州省甕安県", "zunyi": "中国貴州省遵義市",
    "tucheng": "中国貴州省習水県", "zhaxi": "中国雲南省威信県",
    "taipingdu": "中国四川省古藺県", "loushanguan": "中国貴州省遵義市",
    "maotai": "中国貴州省仁懷市", "erlangtan": "中国四川省古藺県",
    "guiyang": "中国貴州省貴陽市", "xundian": "中国雲南省尋甸県",
    "jiaopingdu": "中国雲南省禄勧県", "huili": "中国四川省会理県",
    "mianning": "中国四川省冕寧県", "anshunchang": "中国四川省石棉県",
    "ludingqiao": "中国四川省瀘定県", "tianquan": "中国四川省天全県",
    "jiajinshan": "中国四川省宝興県・小金県境", "dawei": "中国四川省小金県",
    "lianghekou": "中国四川省小金県", "maoergai": "中国四川省松潘県",
    "caodi": "中国四川省若爾蓋県", "baozo": "中国四川省若爾蓋県",
    "baxi": "中国四川省若爾蓋県", "ejie": "中国甘粛省迭部県",
    "lazikou": "中国甘粛省迭部県", "hadapu": "中国甘粛省宕昌県",
    "bangluo": "中国甘粛省通渭県", "liupanshan": "中国寧夏・甘粛境界",
    "wuqi": "中国陝西省呉起県",
}
def en_date(zd):
    """Rough en rendering: '1934年10月17日—12月1日' -> '17 Oct – 1 Dec 1934' style."""
    import re
    m = re.match(r"(\d{4})年(\d{1,2})月(\d{1,2})?日?(?:—(\d{1,2})月(\d{1,2})日)?(.*)", zd)
    ym = re.match(r"(\d{4})年(\d{1,2})月(?:中旬|上旬|下旬|中下旬)?(.*)", zd)
    MM = ["", "January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
    MMa = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    if m:
        y, mo, d, mo2, d2, rest = m.groups()
        if d and d2:
            return f"{int(d)} {MMa[int(mo)]} – {int(d2)} {MMa[int(mo2)]} {y}"
        if d:
            return f"{int(d)} {MMa[int(mo)]} {y}"
    if ym:
        y, mo, rest = ym.groups()
        suffix = {"上旬": " early", "中旬": " mid", "下旬": " late", "中下旬": " mid-to-late"}.get(rest or "", "")
        return f"{suffix.strip() or 'mid'} {MM[int(mo)]} {y}" if suffix else f"{MM[int(mo)]} {y}"
    return zd

ZH_TRAD = str.maketrans("于长征会红亿泽东关岭胶礼续变让", "于長征會紅億澤東關嶺膠禮續變讓")

QP = [  # id, zh-Hans, zh-HK, en, ja, year  — nearby real places for quiz distractors
    ("huichang", "会昌", "會昌", "Huichang", "会昌", 1934),
    ("xingguo", "兴国", "興國", "Xingguo", "興國", 1934),
    ("changting", "长汀", "長汀", "Changting", "長汀", 1934),
    ("ningdu", "宁都", "寧都", "Ningdu", "寧都", 1934),
    ("quanzhou_gx", "全州", "全州", "Quanzhou (Guangxi)", "全州", 1934),
    ("xingan", "兴安", "興安", "Xing'an", "興安", 1934),
    ("longsheng", "龙胜", "龍勝", "Longsheng", "龍勝", 1934),
    ("daoxian", "道县", "道縣", "Daoxian", "道県", 1934),
    ("tongzi", "桐梓", "桐梓", "Tongzi", "桐梓", 1935),
    ("renhuai", "仁怀", "仁懷", "Renhuai", "仁懷", 1935),
    ("xifeng", "息烽", "息烽", "Xifeng", "息烽", 1935),
    ("longli", "龙里", "龍里", "Longli", "龍里", 1935),
    ("wengan", "瓮安", "甕安", "Weng'an", "甕安", 1935),
    ("weixin", "威信", "威信", "Weixin", "威信", 1935),
    ("fuyuan", "富源", "富源", "Fuyuan", "富源", 1935),
    ("luquan", "禄劝", "祿勸", "Luquan", "禄勧", 1935),
    ("xichang", "西昌", "西昌", "Xichang", "西昌", 1935),
    ("shimian", "石棉", "石棉", "Shimian", "石綿", 1935),
    ("tianquan", "天全", "天全", "Tianquan", "天全", 1935),
    ("lushan", "芦山", "蘆山", "Lushan (Sichuan)", "蘆山", 1935),
    ("malikang", "马尔康", "馬爾康", "Ma'erkang", "馬爾康", 1935),
    ("heishui", "黑水", "黑水", "Heishui", "黒水", 1935),
    ("songpan", "松潘", "松潘", "Songpan", "松潘", 1935),
    ("diebu", "迭部", "迭部", "Diebu", "迭部", 1935),
    ("tongwei", "通渭", "通渭", "Tongwei", "通渭", 1935),
    ("zhidan", "志丹", "志丹", "Zhidan", "志丹", 1935),
]

SIGHTS = {  # stopId -> zh-Hans one-line fact for 猜见闻
    "ruijin": "出发前这里是中华苏维埃共和国的首都，被称为“红色首都”。",
    "yudu": "1934年10月17日傍晚，8.6万中央红军从这里八个渡口渡过于都河，迈出长征第一步。",
    "xiangjiang": "湘江一战红军从8万余人锐减到3万余人，是长征中最惨烈的一仗。",
    "laoshanjie": "老山界是长征翻越的第一座真正的高山，陆定一《老山界》记的就是这里。",
    "tongdao": "通道会议上毛泽东第一次提出转兵贵州，史称“通道转兵”。",
    "liping": "黎平会议正式否定了去湘西的方案，确定向川黔边发展。",
    "wujiang": "红军以竹筏强渡乌江天险，为占领遵义打开大门。",
    "zunyi": "遵义会议确立了毛泽东在红军和中共中央的领导地位，是长征最关键的转折点。",
    "tucheng": "青杠坡一战打成僵局，红军被迫一渡赤水西进川南。",
    "zhaxi": "扎西会议决定张闻天取代博古负总责，并作出回兵黔北的决定。",
    "taipingdu": "二渡赤水回师黔北，完全出乎国民党军的意料。",
    "loushanguan": "娄山关大捷是长征以来最大的胜利，毛泽东为此写下《忆秦娥·娄山关》。",
    "maotai": "三渡赤水在茅台渡口进行，红军用“示形”调动了国民党重兵。",
    "erlangtan": "四渡赤水秘密东返，随后南渡乌江跳出几十万大军的包围圈。",
    "guiyang": "红军兵临贵阳，正在贵阳的蒋介石急调滇军驰援，云南门户因此洞开。",
    "xundian": "龙云收缩兵力保卫昆明，反而为红军让开了西去金沙江的通道。",
    "jiaopingdu": "七只小船、37名船工，九天九夜把两万红军运过金沙江。",
    "huili": "会理会议批评了林彪的怀疑，确定了与红四方面军会师的方针。",
    "mianning": "刘伯承与彝族首领小叶丹在彝海歃血结盟，红军顺利通过彝区。",
    "anshunchang": "十七勇士在此强渡大渡河——70年前石达开在此全军覆没。",
    "ludingqiao": "22名突击队员攀铁索夺下泸定桥，红军一昼夜奔袭240里创造了行军纪录。",
    "tianquan": "红军东翻二郎山突破川军六个旅的阻击后占领天全。",
    "jiajinshan": "夹金山海拔约4500米终年积雪，是红军翻越的第一座大雪山。",
    "dawei": "1935年6月12日，中央红军与红四方面军先头部队在达维会师。",
    "lianghekou": "两河口会议决定北上建立川陕甘苏区，但张国焘与中央的分歧就此埋下。",
    "maoergai": "毛儿盖会议后，右路军进入了长征中最艰苦的松潘草地。",
    "caodi": "过草地的部队经受了高原反应、泥沼、饥渴和湿冷的极限考验。",
    "baozo": "包座之战击溃胡宗南部，打开了进军甘南的门户。",
    "baxi": "巴西会议决定率一、三军团单独北上——与张国焘分裂的关键时刻。",
    "ejie": "俄界会议将北上部队改编为陕甘支队，彭德怀任司令员。",
    "lazikou": "一名苗族战士攀上绝壁居高临下，帮助红军攻克腊子口天险。",
    "hadapu": "在哈达铺的报纸上，毛泽东得知陕北有刘志丹的根据地——长征终于有了目的地。",
    "bangluo": "榜罗镇会议正式确定陕甘根据地作为长征的落脚点。",
    "liupanshan": "六盘山是长征翻越的最后一座大山，毛泽东在此写下《清平乐·六盘山》。",
    "wuqi": "1935年10月19日到达吴起镇，中央红军368天、转战11省的长征到此结束。",
}

def build():
    stops = []
    for s in S:
        sid = s["id"]
        lon, lat = s["coords"]
        zh_trad = s["name"].translate(ZH_TRAD)
        pres_zh_t = s["present"].translate(ZH_TRAD)
        date_hk = s["date"].translate(ZH_TRAD)
        stops.append({
            "id": s["id"],
            "coords": [lon, lat],
            "year": s["year"],
            "when": {
                "en-GB": en_date(s["date"]),
                "fr-CA": s["date"].replace("年", " ").replace("月", "/").replace("日", ""),
                "zh-Hans": s["date"],
                "zh-HK": date_hk,
                "ja": s["date"].replace("—", "–"),
            },
            "present": {
                "en-GB": PRESENT_EN[sid],
                "fr-CA": PRESENT_EN[sid],
                "zh-Hans": s["present"],
                "zh-HK": pres_zh_t,
                "ja": PRESENT_JA[sid],
            },
            "iso3": "CHN",
            "names": {
                "en-GB": EN_NAMES[sid],
                "zh-Hans": s["name"],
                "zh-HK": zh_trad,
                "fr-CA": EN_NAMES[sid],
                "ja": JA_NAMES[sid],
            },
            "narrative": {"zh-Hans": s["paras"]},
        })

    # indicative corridor: densify straight chains between consecutive stops
    route = []
    for i, s in enumerate(S):
        route.append([s["coords"][0], s["coords"][1]])
        if i + 1 < len(S):
            t = S[i + 1]
            d = math.hypot(t["coords"][0] - s["coords"][0], t["coords"][1] - s["coords"][1])
            n = max(2, int(d / 0.12))
            for k in range(1, n):
                f = k / n
                route.append([round(s["coords"][0] + (t["coords"][0] - s["coords"][0]) * f, 4),
                              round(s["coords"][1] + (t["coords"][1] - s["coords"][1]) * f, 4)])

    lesson = {
        "id": "longmarch",
        "type": "journey",
        "title": {
            "en-GB": "The Long March of the Central Red Army (1934–1935)",
            "fr-CA": "La Longue Marche de l'Armée rouge centrale (1934–1935)",
            "zh-Hans": "二万五千里长征（1934–1935）",
            "zh-HK": "二萬五千里長征（1934–1935）",
            "ja": "二万五千里長征（1934–1935）",
        },
        "traveler": {
            "en-GB": "the Central Red Army",
            "fr-CA": "l'Armée rouge centrale",
            "zh-Hans": "中央红军",
            "zh-HK": "中央紅軍",
            "ja": "中央紅軍",
        },
        "stops": stops,
        "route_out": route,
        "view": {"lon0": 99, "lat0": 20, "lon1": 121, "lat1": 43},
        "quizPlaces": [
            {"id": qid, "year": yr, "names": {
                "en-GB": en, "fr-CA": en, "zh-Hans": zh, "zh-HK": hk, "ja": ja}}
            for (qid, zh, hk, en, ja, yr) in QP
        ],
        "quizSights": {k: {"zh-Hans": v} for k, v in SIGHTS.items()},
        "corridorNote": {
            "en-GB": "Dots mark documented events with precise coordinates; the connecting lines are indicative corridors reconstructed from published route maps, not surveyed tracks.",
            "fr-CA": "Les points marquent des événements documentés aux coordonnées précises ; les lignes sont des couloirs indicatifs reconstitués à partir de cartes publiées.",
            "zh-Hans": "圆点标记有确切坐标的史料事件；站点之间的连线为依据公开路线图重建的指示性走廊，非逐日实测轨迹。",
            "zh-HK": "圓點標記有確切座標的史料事件；站點之間的連線為依據公開路線圖重建的指示性走廊，非逐日實測軌跡。",
            "ja": "ドットは正確な座標が確認されている史実の出来事を示し、駅間の線は公開された路線図から再現した概略走廊であり、実測の軌跡ではありません。",
        },
    }

    os.makedirs("lessons/longmarch", exist_ok=True)
    with open("lessons/longmarch/journey.json", "w", encoding="utf-8") as f:
        json.dump(lesson, f, ensure_ascii=False, indent=1)
    with open("lessons/longmarch/journey.js", "w", encoding="utf-8") as f:
        f.write('window.ATLAS_LESSONS = window.ATLAS_LESSONS || {};\n')
        f.write('window.ATLAS_LESSONS["lessons/longmarch/journey.json"] = ')
        f.write(json.dumps(lesson, ensure_ascii=False))
        f.write(';\n')
    print(f"wrote lessons/longmarch/journey.json: {len(stops)} stops, {len(route)} route pts")

if __name__ == "__main__":
    build()
