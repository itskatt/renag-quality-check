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
    for constel, (_, csall, expobs) in extracted.items():
        observation_dest["length"] += 1

        obs_data["date"].append(current_date)
        obs_data["constellation"].append(constel)
        obs_data["value"].append(csall / expobs * 100)


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
        f"insert into {Metric.OBSERVATION_CS.value}(date, station_id, constellation_id, value) values " +
        ",".join(to_insert)
    )
