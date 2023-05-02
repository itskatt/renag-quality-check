from collections import defaultdict
from statistics import mean

from psycopg.sql import SQL, Identifier

from ..database import get_constellation_id
from . import Metric


def extract_from_sum_stats(f, observation_dest, satellite_dest, current_date):
    line: str = next(f)

    # On va jusqu'a la partie interessante
    while not line.startswith("#G"):
        line = next(f)
    next(f) # seconde ligne

    extracted = {}
    line = next(f)
    while line.startswith("="):
        splitted = line.split()

        constel = splitted[0][1:4] # GPS par ex
        havep = int(splitted[4]) if splitted[4] != "-" else 0
        csall = int(splitted[9]) if splitted[9] != "-" else 0

        extracted[constel] = [havep, csall, None]
        line = next(f)

    # suite des données pour le observation cs
    next(f) # ligne vide
    next(f) # entête
    line = next(f)
    curr_constel = ""
    while line.startswith("="):
        splitted = line.split()

        constel = splitted[0][1:4]
        if constel == curr_constel:
            line = next(f)
            continue
            
        curr_constel = constel
        expobs = int(splitted[4]) if splitted[4] != "-" else 1
        extracted[constel][2] = expobs

        line = next(f)

    # formats tabulaire
    obs_data = observation_dest["data"]
    sat_data = satellite_dest["data"]
    for constel, (havep, csall, expobs) in extracted.items():
        observation_dest["length"] += 1
        obs_data["date"].append(current_date)
        obs_data["constellation"].append(constel)
        obs_data["value"].append(csall / expobs * 100)

        # Première fonction a manipuler le satellite cs
        satellite_dest["length"] += 1
        sat_data["date"].append(current_date)
        sat_data["constellation"].append(constel)
        sat_data["havep"].append(havep)

    return len(extracted)


def extract_from_prepro_res(f, satellite_dest, nb_constell):
    line = next(f)
    while not line.startswith("#GNSSLP"):
        line = next(f)
    line = next(f)

    count = defaultdict(int)
    while line != "\n": # NOTE : ici on arrive juste avant la section "Elevation & Azimuth"
        count[line[1:4]] += 1
        line = next(f)

    sat_data = satellite_dest["data"]
    for i in range(satellite_dest["length"] - nb_constell, satellite_dest["length"]):
        constel = sat_data["constellation"][i]
        sat_data["nb_sat"].append(count[constel]) # si rien alors 0 (parfait)


def extract_from_band_avail(f, satellite_dest):
    line = next(f)
    while not line.startswith("#N"): # #NxBAND
        line = next(f)
    line = next(f)

    count = defaultdict(list)
    while True:
        splitted = line.split()
        if splitted[0][-3:] != "CBN":
            break

        # nSatell
        count[splitted[0][:3]].append(int(splitted[3] if splitted[3] != "-" else 0))

        line = next(f)

    sat_data = satellite_dest["data"]
    for i in range(satellite_dest["length"] - len(count), satellite_dest["length"]):
        constel = sat_data["constellation"][i]
        sat_data["avg_sat"].append(mean(count[constel]) if len(count[constel]) > 0 else 1)


def insert_observation(cur, station_id, observation_cs):
    to_insert = []
    data = observation_cs["data"]
    for i in range(observation_cs["length"]):
        constellation_id = get_constellation_id(cur, data["constellation"][i])

        row = cur.mogrify(
            "(%s,%s,%s,%s)",
            (data["date"][i], station_id, constellation_id, data["value"][i])
        )
        to_insert.append(row)

    cur.execute(
        SQL("insert into {}(date, station_id, constellation_id, value) values ")
        .format(Identifier(Metric.OBSERVATION_CS.value)).as_string(cur) +
        ",".join(to_insert)
    )

def insert_satellite(cur, station_id, satellite_cs):
    to_insert = []
    data = satellite_cs["data"]
    for i in range(satellite_cs["length"]):
        constellation_id = get_constellation_id(cur, data["constellation"][i])

        row = cur.mogrify(
            "(%s,%s,%s,%s)",
            (
                data["date"][i], station_id, constellation_id,
                # FIXME : il n'arrive pas a compter le nombre de satellites
                # pour certains fichiers/constellations
                data["nb_sat"][i] / data["avg_sat"][i] / data["havep"][i] * 100
            )
        )
        to_insert.append(row)


    cur.execute(
        SQL("insert into {}(date, station_id, constellation_id, value) values ")
        .format(Identifier(Metric.SATELLITE_CS.value)).as_string(cur) +
        ",".join(to_insert)
    )
