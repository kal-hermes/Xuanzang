# -*- coding: utf-8 -*-
"""Magellan-Elcano circumnavigation (1519-1522) lesson data.

Stops use Wikidata QIDs (verified via wbsearchentities/wbgetentities,
same protocol as the Xuanzang lesson). Dates per Pigafetta's account
(Il viaggio fatto da gli spagnuoli a torno il mondo, 1524) and the
standard reconstructions (Wikipedia's Magellan expedition timeline,
cross-checked against historyextra/HISTORY.com).

Route waypoints: OFFSHORE sea track (inshore only via short anchor
points near ports, kept just outside the coastline). The renderer
joins them with gentle cubic Bezier bows. Land-crossing verified by
sampling the rendered curve against the country polygons.
"""

# stop id -> (QID, search tokens, iso3 of the modern country)
# QIDs resolver-verified (wbsearchentities + P625 cross-check)
STOPS = {
    "sanlucar":  ("Q210887",  ["Sanlúcar de Barrameda"], "ESP"),
    "tenerife":  ("Q40846",   ["Tenerife"], "ESP"),
    "rio":       ("Q8678",    ["Rio de Janeiro"], "BRA"),
    "plata":     ("Q35827",   ["Río de la Plata"], "ARG"),
    "san_julian": ("Q955668", ["Puerto San Julián"], "ARG"),
    "strait":    ("Q48365",   ["Strait of Magellan"], "CHL"),
    "pacific_crossing": (None, [], None),  # mid-ocean, no place
    "guam":      ("Q16635",   ["Guam"], "GUM"),
    "homonhon":  ("Q1626237", ["Homonhon Island"], "PHL"),
    "limasawa":  ("Q173678",  ["Limasawa"], "PHL"),
    "cebu":      ("Q1467",    ["Cebu City"], "PHL"),
    "mactan":    ("Q685318",  ["Mactan"], "PHL"),
    "palawan":   ("Q13869",   ["Palawan"], "PHL"),
    "brunei":    ("Q9279",    ["Bandar Seri Begawan"], "BRN"),
    "tidore":    ("Q12506955", ["Tidore Island"], "IDN"),
    "ambon":     ("Q219608",  ["Ambon Island"], "IDN"),
    "timor":     ("Q83067",   ["Timor"], "IDN"),
    "cape_hope": ("Q4092",    ["Cape of Good Hope"], "ZAF"),
    "verde":     ("Q108448",  ["Santiago Island Cape Verde"], "CPV"),
    "sanlucar_end": ("Q210887", ["Sanlúcar de Barrameda"], "ESP"),
}

# offshore sea track [lon, lat]; anchors sit just off the ports
ROUTE_OUT = [
    [-7.2, 36.4],    # off Cape St Mary / Cádiz — depart 20 Sep 1519
    [-9.7, 35.5],    # SW past Cape St Vincent
    [-17.0, 28.4],   # off Tenerife (W anchor) 26 Sep – 3 Oct
    [-19.0, 24.0],   # SSW
    [-22.0, 17.0],
    [-26.0, 9.0],
    [-30.0, 1.0],
    [-34.0, -7.0],
    [-35.5, -13.0],  # well off NE Brazil
    [-37.0, -19.0],
    [-40.0, -23.0],
    [-42.5, -23.5],  # Rio de Janeiro anchor 13 Dec 1519 – 11 Jan 1520
    [-45.0, -25.0],
    [-48.0, -28.5],
    [-51.5, -32.5],
    [-54.5, -35.0],
    [-55.4, -36.2],  # Río de la Plata anchor (off Montevideo) 10 Jan 1520
    [-57.4, -37.9],
    [-61.0, -39.0],
    [-63.0, -43.0],
    [-65.0, -47.0],
    [-67.2, -49.8],  # Puerto San Julián anchor 31 Mar – 24 Aug
    [-68.8, -51.0],
    [-70.5, -52.6],  # strait entrance (Atlantic side) 21 Oct
    [-73.2, -53.9],  # through the strait (mid-channel)
    [-75.4, -52.9],  # Pacific exit 28 Nov 1520
    [-78.0, -50.0],
    [-82.0, -44.0],  # NW along Chile
    [-88.0, -36.0],
    [-96.0, -27.0],
    [-105.0, -18.0],
    [-115.0, -9.0],
    [-127.0, -2.0],
    [-140.0, 3.0],
    [-153.0, 7.0],
    [-166.0, 10.0],
    [-178.0, 11.5],
    [170.0, 12.0],
    [157.0, 12.5],
    [147.0, 13.6],   # Guam anchor (W side) 6 Mar 1521
    [142.0, 13.0],
    [135.0, 12.5],
    [129.0, 12.0],
    [126.2, 11.5],   # Homonhon anchor (E side) 16 Mar
    [125.6, 10.6],
    [125.3, 10.1],   # Limasawa anchor (S tip) 28 Mar
    [124.8, 10.2],
    [124.1, 10.4],   # Cebu anchor (E strait) 7 Apr
    [124.15, 10.5],  # Mactan anchor 27 Apr
    [122.6, 10.9],
    [119.9, 10.6],   # Palawan N coast track
    [118.5, 10.0],   # Palawan (off Puerto Princesa) 19 Apr – 4 May
    [116.8, 8.3],
    [115.2, 6.5],
    [114.85, 5.3],    # Brunei anchor (off Muara) 8 – 29 Jul
    [116.9, 3.8],
    [121.2, 1.9],
    [124.5, 1.6],
    [127.3, 1.0],
    [127.5, 0.6],    # Tidore anchor (W side) 8 Nov 1521
]

ROUTE_BACK = [
    [127.5, 0.6],    # Tidore
    [128.4, -1.2],
    [128.4, -3.6],   # Ambon anchor (S approach) Nov 1521 – Jan 1522
    [127.0, -6.0],
    [124.9, -8.7],   # Timor anchor (S coast) c. 15 – 25 Jan 1522
    [122.0, -10.0],
    [117.0, -13.0],
    [111.0, -17.0],
    [104.0, -22.0],
    [97.0, -28.0],
    [90.0, -34.0],
    [82.0, -38.0],
    [73.0, -40.0],
    [63.0, -41.0],
    [52.0, -40.5],
    [41.0, -39.0],
    [31.0, -37.0],
    [23.0, -35.0],
    [18.9, -34.9],   # Cape of Good Hope anchor (S of cape) 19 May 1522
    [17.0, -35.3],
    [13.0, -32.0],
    [8.0, -26.0],
    [2.0, -18.0],
    [-4.0, -10.0],
    [-10.0, -3.0],
    [-16.0, 4.0],
    [-21.0, 10.0],
    [-24.5, 14.6],   # Cape Verde anchor (S of Santiago) 9 – 15 Jul 1522
    [-26.5, 18.5],
    [-31.0, 23.0],
    [-36.0, 28.0],
    [-41.0, 33.0],
    [-45.0, 36.0],
    [-25.0, 37.5],   # W of Portugal, then E into Cádiz bay
    [-12.0, 37.0],
    [-8.5, 36.7],
    [-7.0, 36.6],    # Sanlúcar anchor 6 Sep 1522
]
