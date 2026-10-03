#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rebuild ROUTE_OUT/ROUTE_BACK from primary sources:
- Francisco Albo's derrotero (Victoria's pilot; Wikisource, Stanley
  trans.) — daily course + latitude from Cape St Augustine to Timor,
  strait waypoints, Pacific daily latitudes.
- whalesite.org KML reconstruction (vic3-vic6) for the Brazil coast
  legs (points already follow Albo's daily fixes).
- Pacific longitudes: Albo gives none; dead-reckon from his courses
  and the known anchor points (Guam 13N, per Albo 6 Mar 1521 landfall
  at 12 2/3 N; Strait exit Cabo Pilar ~75.6W). Pacific crossing
  latitudes taken from his daily table (Dec 1520 - Mar 1521).
- Return leg: Victoria went Timor -> (Amsterdam/St Paul islands,
  38S, 18-22 Mar 1522 per Albo) -> Cape of Good Hope (16-19 May,
  Albo: 20 leagues off, 35 39'S) -> far off St Helena / up the
  central Atlantic avoiding the Portuguese coast -> Cape Verde
  (Santiago, 9-15 Jul, ~15N) -> NW then E to Sanlucar. The final
  Atlantic leg is a smooth great-circle-like arc from Cape Verde to
  C. St Vincent (Albo 4 Sep 1522 sighting), NOT a V-shaped detour.
"""

# --- South America coast (whalesite KML, = Albo's daily fixes) ------
# vic3: Cape St Augustine (29 Nov 1519) -> Rio (13 Dec)
# note: our lesson starts at Tenerife; the Atlantic crossing to Brazil
# uses Albo's implied SW track. We skip vic3's start (too far E) and
# join at the coast.
ROUTE_OUT = [
    # Sanlucar -> Tenerife (fleet departed 20 Sep 1519, arrived 26 Sep;
    # Albo: SSW down the Spanish and Moroccan coast)
    [-6.6, 36.4],      # off Sanlucar S 20 Sep 1519
    [-7.2, 35.8],
    [-8.0, 35.0],
    [-9.2, 34.0],      # Cape St Vincent S by W
    [-10.5, 33.0],
    [-12.0, 31.5],
    [-13.5, 30.0],
    [-15.0, 29.2],
    [-16.2, 28.5],     # W of Fuerteventura 24 Sep
    # Tenerife -> Brazil crossing (Albo: no sights until 29 Nov off
    # Cape St Augustine, course S.S.W. throughout => a gentle SW line)
    [-16.8, 28.0],    # off Tenerife W 26 Sep - 3 Oct 1519
    [-19.0, 23.0],
    [-23.0, 16.0],
    [-27.0, 9.0],
    [-31.0, 2.0],
    [-33.6, -7.0],    # Albo 29 Nov: 7S, 27 leagues SW of Cape St Augustine
    [-34.9, -8.3],    # 30 Nov (KML)
    [-35.2, -11.1],   # 3 Dec
    [-36.0, -13.0],   # 4 Dec
    [-36.8, -15.0],   # 5 Dec
    [-37.5, -17.1],   # 6 Dec
    [-38.5, -19.0],   # 7 Dec
    [-39.2, -20.6],   # 8 Dec (soundings 10 fm, land sighted)
    [-40.5, -22.0],   # 9-12 Dec coasting SW
    [-41.9, -22.9],   # Rio de Janeiro 13 Dec - 27 Dec (KML anchor)
    [-43.1, -22.9],   # 27-31 Dec (KML)
    [-44.5, -24.7],   # 31 Dec lat 25 23' (KML/vic4)
    [-46.0, -26.0],   # 1-4 Jan 1520 (KML interpolation)
    [-47.5, -28.0],
    [-48.4, -30.5],   # 5 Jan 29 49'S (KML)
    [-49.5, -32.0],   # 6 Jan 31S
    [-50.8, -33.9],   # 7 Jan 32 56'S
    [-52.5, -34.8],   # 8-9 Jan anchored 34 31'S
    [-54.3, -34.9],   # 10 Jan Cape Sta Maria / Montevideo offing
    [-55.4, -34.8],   # Rio de la Plata anchorage 12 Jan - 11 Feb
    [-56.8, -36.3],   # 7-8 Feb Cabo San Antonio (KML)
    [-57.2, -37.0],   # 9 Feb
    [-57.8, -38.8],   # 10-11 Feb Bahia Blanca offing
    [-59.0, -39.2],   # 14 Feb 39 11'S
    [-60.3, -40.3],   # 20 Feb 40 17'S
    [-61.5, -42.0],   # 21-22 Feb 42-43'S
    [-62.7, -43.0],   # 23-24 Feb, Golfo San Matias
    [-64.2, -44.2],   # 26-28 Feb 44 21'
    [-65.0, -45.5],   # 2 Mar 47'  [Albo: 47S]
    [-65.8, -47.3],   # Valdes offing
    [-66.5, -48.5],
    [-67.7, -49.35],  # Puerto San Julian 31 Mar - 24 Aug (KML)
    [-68.4, -50.1],   # Santa Cruz river 26 Aug - 18 Oct (KML)
    [-69.1, -52.0],   # 21 Oct Cape Virgins, strait entrance (KML/Albo)
    # strait: Albo's own waypoints (52 -> 52.33 -> 53 -> exit 52)
    [-68.9, -52.4],   # Angostura Segunda area
    [-69.6, -52.6],
    [-70.5, -52.9],   # islands anchorage (Isla Isabel) 52 1/3
    [-71.8, -53.2],
    [-73.0, -53.5],   # 53 2/3 southern elbow
    [-74.0, -53.2],
    [-74.7, -52.7],   # Cabo Pilar / Pacific exit 28 Nov 1520 (KML)
    # --- Pacific: Albo's daily latitudes, dead-reckoned longitudes --
    [-76.5, -49.0],   # 1-5 Dec coasting N along Chile 48-44S
    [-78.5, -44.0],
    [-80.5, -40.0],   # 8-10 Dec
    [-83.0, -36.0],
    [-86.0, -32.0],   # 15-18 Dec
    [-89.5, -28.0],
    [-93.0, -24.0],   # 21-24 Dec 30 2/3 -> 29 3/4
    [-97.5, -22.5],   # 27-31 Dec 27-25 1/2
    [-102.0, -22.0],  # 1-7 Jan 25 -> 22
    [-108.0, -21.0],  # 8-14 Jan (two W days ~25 leagues each)
    [-114.0, -19.5],  # 15-18 Jan
    [-120.0, -16.5],  # 19-21 Jan
    [-124.0, -16.0],  # 22-24 Jan (S of San Pablo islet 24 Jan)
    [-129.0, -15.0],  # 25-28 Jan
    [-134.5, -13.0],  # 29-31 Jan
    [-140.0, -11.5],  # 1-4 Feb (Tiburones islet ~4 Feb, 11 3/4)
    [-146.0, -9.0],   # 5-8 Feb
    [-151.0, -6.0],   # 9-11 Feb
    [-156.0, -2.5],   # 12 Feb 1S
    [-160.5, 1.0],    # 14 Feb crosses equator
    [-165.0, 3.5],    # 17-19 Feb
    [-170.0, 6.5],    # 20-22 Feb
    [-175.0, 9.5],    # 23-25 Feb
    [-179.5, 12.0],   # 26-28 Feb 12 1/3 (doldrums drift)
    [179.0, 12.2],    # crosses the antimeridian ~1 Mar
    [177.0, 12.3],
    [174.0, 12.4],
    [170.0, 12.8],
    [165.0, 13.1],
    [155.0, 13.4],    # 5 Mar 13N steady (trade belt)
    [150.0, 13.4],    # 6 Mar Guam landfall next day
    [146.5, 13.4],    # 6 Mar Guam landfall (144.8E actual; offshore)
    [143.0, 12.5],    # 9-10 Mar W 1/4 SW 12-12 1/3
    [139.5, 11.5],    # 11 Mar 11 1/2
    [136.5, 10.9],    # 14-15 Mar 10-10 2/3
    [130.5, 10.0],    # 16 Mar morning: Suluan sighted (125.4E actual)
    [125.6, 10.1],    # Suluan/Yunuguan anchorage (Albo 9 2/3 N)
    [125.4, 10.6],    # Homonhon 16-25 Mar (Albo: Gada watering)
    [125.0, 10.0],    # 28 Mar S. to Mazaba/Limasawa (9 1/3 N)
    [124.9, 9.9],     # Limasawa anchor 28-31 Mar
    [124.4, 10.3],    # 7 Apr N to Cebu (Albo: Subu 10 1/3)
    [124.0, 10.4],    # Cebu anchorage 7 Apr - 1 May
    [124.1, 10.5],    # Mactan 27 Apr battle (channel off Mactan)
    [123.8, 9.8],     # 1-4 May S to Bohol (Albo: 9 1/2)
    [124.2, 9.5],     # Bohol anchorage May
    [122.0, 9.2],     # Quipit Mindanao W.SW (Albo: 8 1/2 N head)
    [123.0, 8.9],     # S past Tagima pearls is. 6 5/6 (Albo)
    [121.5, 7.8],     # Balabac strait area (Albo: Solo is. 6)
    [119.4, 9.4],     # Palawan NE cape Saocao (Albo: 9 1/3)
    [118.5, 9.3],     # Palawan N coast W (Puerto Princesa offing)
    [117.3, 8.7],     # Palawan SW head (Albo: 8 1/3)
    [116.0, 7.2],     # SW to Borneo (Albo: 7 1/2 turn)
    [114.8, 5.5],     # Brunei 8-29 Jul (Albo: port 5 25')
    [119.0, 5.8],     # return E along Borneo N coast
    [122.0, 6.5],
    [124.5, 6.9],     # Tagima pearls is. 6 5/6 (Albo)
    [125.5, 6.0],     # Sarangani 4 2/3 (pilot taken aboard)
    [126.5, 4.0],     # Sanguir 3 2/3
    [127.2, 3.0],     # Sian 3
    [127.8, 1.5],     # Paginsara 1 1/6
    [128.0, 0.5],     # Suar/Atean ~1-1.5
    [127.5, 0.0],     # Tidore 8 Nov 1521 (Albo: 0 30')
]

ROUTE_BACK = [
    [127.5, 0.0],     # Tidore
    [127.8, -0.5],    # Mare, Motil, Maquian passes (Albo 21 Dec)
    [127.9, -1.3],    # S 1/4 W past Latalata
    [128.2, -2.2],    # Lumutola 1 3/4 (Albo)
    [128.3, -3.5],    # Buro 3 1/2; Ambon to the E 29 Dec
    [127.9, -5.5],    # 2-6 Jan 5 1/2 (Albo)
    [127.3, -8.2],    # 8 Jan Lamaluco channel 8 7'
    [126.4, -9.4],    # Timor N coast 9-10 Feb (Albo: 9 24')
    [124.0, -9.9],    # W along Timor (Albo: W cape 9 35' 9 Feb)
    [121.0, -10.5],   # 13 Feb 10 32' WSW
    [115.0, -14.0],   # WSW run, March
    [107.0, -21.0],
    [98.0, -28.0],    # 18 Mar 37 35' Amsterdam Is. 38S sighted
    [92.0, -34.0],
    [84.0, -38.0],
    [73.0, -40.0],    # April-May southern ocean
    [62.0, -41.0],
    [50.0, -40.0],
    [38.0, -38.5],    # 16 May 35 39' 20 leagues off Cape
    [28.0, -36.5],
    [20.0, -35.6],    # 19 May doubled the Cape (Pigafetta)
    [14.0, -34.0],
    [8.0, -29.0],     # June: up the S Atlantic well offshore
    [2.0, -22.0],
    [-3.0, -15.0],
    [-8.0, -8.0],
    [-13.0, -1.0],
    [-18.0, 6.0],
    [-22.5, 12.0],    # late June, approaching Cape Verde from SW
    [-23.5, 14.8],    # Santiago 9-15 Jul (Albo: 15 10')
    # final leg: NW-then-E arc. Pigafetta: provisions low, they made
    # for the Azores area then C. St Vincent; Albo sighted C. St
    # Vincent NE of them on 4 Sep. A smooth arc, NOT a V.
    [-27.0, 18.0],
    [-32.0, 22.5],
    [-37.5, 27.0],
    [-42.5, 31.5],
    [-47.0, 35.5],    # ~36N 47W northernmost point of the arc
    [-45.0, 37.0],    # turn E with the westerlies
    [-38.0, 38.0],
    [-30.0, 38.0],
    [-22.0, 37.5],
    [-14.0, 37.0],
    [-9.0, 36.9],     # off Cape St Vincent 4 Sep (Albo)
    [-6.9, 36.8],     # Sanlucar 6 Sep 1522
]
