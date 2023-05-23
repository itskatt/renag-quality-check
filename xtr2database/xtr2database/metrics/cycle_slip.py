import datetime as dt
from collections import defaultdict

from psycopg.sql import SQL, Identifier

from ..database import get_constellation_id
from . import TimeSeries

try: # Compatibilité python 3.7
    from statistics import fmean as mean  # type: ignore
except ImportError:
    from statistics import mean


def extract_from_sum_stats(f, observation_dest, satellite_dest, current_date):
    """
    Extraits des données de la section "Summary statistics" utilisé pour les
    calculs des metriques observation cs et satellite cs.
    """
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


def extract_from_prepro_res(f, satellite_dest, skyplot_dest, nb_constell, current_date):
    """
    Extraits des données de la section "Preprocessing results" utilisé pour les
    calculs du satellite_cs ainsi que le tracage des skyplot de cycle slip.
    """
    line = next(f)
    while not line.startswith("#GNSSLP"):
        line = next(f)

    # Ici on récupère les bandes dans l'entête de section
    bands = [b[1:] for b in line.split()[4:]]

    # On rentre dans la partie interessante
    line = next(f)

    count = defaultdict(int)
    while line != "\n": # NOTE : ici on arrive juste avant la section "Elevation & Azimuth"
        splitted = line.split()

        constel = line[1:4]
        time = dt.time.fromisoformat(splitted[2])
        datetime = dt.datetime.combine(current_date, time)
        sat_number = int(splitted[3][1:])
        cs_bands = [bands[i] for i, b in enumerate(splitted[4:]) if b != "-"]

        skyplot_dest[constel][datetime]["cs"][sat_number] = cs_bands

        count[constel] += 1
        line = next(f)

    sat_data = satellite_dest["data"]
    for i in range(satellite_dest["length"] - nb_constell, satellite_dest["length"]):
        constel = sat_data["constellation"][i]
        sat_data["nb_sat"].append(count[constel]) # si rien alors 0 (parfait)


def extract_from_band_avail(f, satellite_dest, nb_constell):
    """
    Extraits des données de la section "Band available" utilisé pour les
    calculs du satellite cs.
    """
    line = next(f)
    while not line.startswith("#N"): # #NxBAND
        line = next(f)
    line = next(f)

    count = defaultdict(list)
    while True:
        splitted = line.split()
        if not splitted or splitted[0][-3:] != "CBN":
            break

        # nSatell
        count[splitted[0][:3]].append(int(splitted[3] if splitted[3] != "-" else 0))

        line = next(f)

    sat_data = satellite_dest["data"]
    for i in range(satellite_dest["length"] - nb_constell, satellite_dest["length"]):
        constel = sat_data["constellation"][i]
        sat_data["avg_sat"].append(mean(count[constel]) if len(count[constel]) > 0 else 1)


def insert_observation(cur, station_id, observation_cs):
    """
    Insère dans la base de données les données de la metrique observation cs.
    """
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
        .format(Identifier(TimeSeries.OBSERVATION_CS.value)).as_string(cur) +
        ",".join(to_insert)
    )


def insert_satellite(cur, station_id, satellite_cs):
    """
    Insère dans la base de données les données de la metrique satellite cs.
    """
    to_insert = []
    data = satellite_cs["data"]
    for i in range(satellite_cs["length"]):
        constellation_id = get_constellation_id(cur, data["constellation"][i])

        row = cur.mogrify(
            "(%s,%s,%s,%s)",
            (
                data["date"][i], station_id, constellation_id,
                data["nb_sat"][i] / data["avg_sat"][i] / data["havep"][i] * 100
            )
        )
        to_insert.append(row)

    cur.execute(
        SQL("insert into {}(date, station_id, constellation_id, value) values ")
        .format(Identifier(TimeSeries.SATELLITE_CS.value)).as_string(cur) +
        ",".join(to_insert)
    )
