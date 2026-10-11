#!/usr/bin/env python3
"""Curved Xuanzang route polylines — the historical road network.

Anchors are the lesson stops (exact Wikidata coords); shaping points
follow the pre-modern caravan roads as recorded in the Record of the
Western Regions and standard route reconstructions:

OUT (629-633): Wei valley -> Long Mts bend -> Wushao Ling -> Hexi
corridor oasis chain (Zhangye, Jiuquan) -> Guazhou -> Mo-ha desert
beacon line -> Hami -> Tian Shan southern fringe -> Gaochang ->
Karashahr -> Kucha -> Aksu -> Bedel Pass -> Suyab -> Chu valley ->
Talas -> Chach -> Kesh -> Samarkand -> Iron Gate -> Termez -> Balkh ->
Hindu Kush -> Bamyan -> Black Range -> Kapisa -> Kabul -> Khyber ->
Nagarahara -> Gandhara -> Swat valley -> Kashmir -> Jhelum/Chenab ->
Punjab -> Ganges plain -> Nalanda.

BACK (643-645): Nalanda -> Ganges plain NW -> Kanauj -> Prayaga ->
(escorted NW through Punjab/Kashmir in reverse) -> Kapisa -> Kunduz ->
Oxus headwaters -> Wakhan corridor -> Wakhjir -> Tashkurgan -> Kashgar
-> Yarkant -> Khotan -> southern Tarim (Niya, dying rivers) -> Loulan/
Lop Nor -> Dunhuang -> Hexi corridor in reverse -> Chang'an.

No anachronisms: all of these are caravan/mountain roads that
predate Xuanzang (some by centuries). No bridges — rivers were
crossed at fords/ferry points.
"""

ROUTE_OUT_CURVED = [
  [108.85833333333333, 34.30833333333333],  # Chang'an
  [106.85, 34.7], [106.0, 35.3],
  [104.6, 35.6], [103.4, 36.6],
  [103.3, 37.4], [103.1, 37.75],
  [102.63286, 37.92781],                     # Liangzhou
  [102.0, 38.7], [101.0, 38.95],
  [100.45, 38.93],                           # Zhangye (Ganzhou)
  [99.5, 39.3], [98.9, 39.5], [97.9, 39.75],
  [98.5, 39.75],                             # Jiuquan (Suzhou)
  [97.0, 40.2], [96.4, 40.4],
  [95.78058, 40.51481],                      # Guazhou
  [94.6, 41.1],
  [93.51548, 42.83224],                      # Hami
  [92.8, 42.6], [91.9, 42.35],
  [90.8, 42.6],
  [89.529166666667, 42.852777777778],        # Gaochang
  [88.5, 42.5], [87.5, 42.2],
  [86.566666666667, 42.05],                  # Karashahr
  [85.5, 41.95], [84.3, 41.85], [83.6, 41.75],
  [82.9, 41.65],                             # Kucha
  [81.8, 41.5], [80.9, 41.35],
  [80.25, 41.166389],                        # Aksu
  [79.3, 41.6], [78.4, 41.9], [77.3, 42.2], [76.4, 42.5],
  [75.2667, 42.8],                           # Suyab
  [74.3, 43.0], [73.0, 43.05], [72.2, 42.95],
  [71.366666666667, 42.883333333333],        # Talas
  [70.3, 42.9],
  [69.24, 41.3],                             # Chach (Tashkent)
  [68.2, 40.7], [67.5, 39.9],
  [66.83, 39.0],                             # Kesh (Shahrisabz)
  [66.97583333333333, 39.65472222222222],    # Samarkand
  [66.9068, 38.2216],                        # Iron Gate
  [67.28, 37.23],                            # Termez (Oxus ford)
  [67.1, 36.9],
  [66.898888888889, 36.758055555556],        # Balkh
  [67.3, 36.0], [67.55, 35.5], [67.7, 35.15],
  [67.816666666667, 34.816666666667],        # Bamyan
  [68.35, 34.9], [68.9, 34.95],
  [69.7, 35],                                # Kapisa
  [69.2, 34.55], [69.9, 34.45], [70.1, 34.42],
  [70.452777777778, 34.430277777778],        # Nagarahara
  [70.95, 34.2], [71.2, 34.05],
  [71.5675, 34.014444444444],                # Gandhara
  [71.9, 34.35], [72.15, 34.6],
  [72.361944444444, 34.782777777778],        # Swat
  [73.3, 34.7], [74.3, 34.6], [75.2, 34.55],
  [76.0, 34.5],                              # Kashmir
  [75.3, 33.5], [74.8, 32.4], [74.4, 31.6],
  [74.0, 31.0],                              # Punjab
  [75.8, 30.2], [77.2, 29.5], [78.6, 28.5], [79.9, 27.6],
  [80.9, 26.9], [82.0, 26.3], [83.0, 25.6], [84.2, 25.3],
  [85.443827777778, 25.136797222222],        # Nalanda
]

ROUTE_BACK_CURVED = [
  [85.443827777778, 25.136797222222],        # Nalanda
  [84.2, 25.3], [83.0, 25.6], [82.0, 26.3], [80.9, 26.9],
  [79.92201944444444, 27.031336111111113],   # Kanauj
  [80.7, 26.2],
  [81.85, 25.45],                            # Prayaga
  # (escorted NW with Harsha's mission via the Punjab/Kashmir in reverse)
  [81.0, 26.4], [79.0, 27.8], [77.0, 30.0], [75.0, 32.5], [73.0, 34.2],
  [71.5, 34.8], [70.5, 35.0], [69.5, 35.2],
  [68.86, 36.73],                            # Kunduz (Huo)
  # Oxus headwaters -> Wakhan corridor (recorded return route)
  [69.9, 36.7], [70.5, 36.9], [70.8, 36.85],
  [71.3, 36.9], [71.7, 37.0],
  [72.3, 37.0], [73.0, 37.2], [73.5, 37.3],
  [74.0, 37.4], [74.5, 37.5],
  [75.23, 37.77],                            # Tashkurgan (Kiepantuo)
  [75.6, 38.0],
  [75.983333, 39.45],                        # Kashgar
  [77.24, 38.42],                            # Yarkant
  [78.7, 37.8], [79.5, 37.4],
  [80.0167, 37.1],                           # Khotan
  [82.5, 37.5], [84.5, 38.6], [86.5, 39.6], [88.0, 40.1],
  [89.840644444444, 40.527633333333],        # Loulan
  [92.3, 40.6], [93.5, 40.4],
  [94.66388888888889, 40.14111111111111],    # Dunhuang
  [96.4, 40.4], [97.0, 40.2], [98.5, 39.75], [99.5, 39.3], [100.45, 38.93],
  [101.0, 38.95], [102.0, 38.7],
  [102.63286, 37.92781],                     # Liangzhou (return)
  [103.1, 37.75], [103.3, 37.4], [103.4, 36.6], [104.6, 35.6],
  [106.0, 35.3], [106.85, 34.7],
  [108.85833333333333, 34.30833333333333],   # Chang'an
]
