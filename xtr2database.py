"""
Script principal.
=================

Parse les fichiers XTR et insère les résultats dans une base de données.
"""
from itertools import groupby
from pathlib import Path

import psycopg
from psycopg import ClientCursor
from psycopg.rows import dict_row
from tqdm import tqdm

from extractors import extract_sig_noise_ratio, get_file_date, get_station_id

HERE = Path(__file__).parent

# Temporaire
INFILES = HERE / ".." / "graphes simples" / "data_2023"


_database_fetch_cache = {}


def get_station_data(files):
    """
    Extrait les données d'une station et les met en forme pour l'insertion dans
    une bdd de type relationelle.
    """
    dates = []
    band_data = []
    all_bands = set()

    # Extraction des informations des fichiers
    for file in files:
        dates.append(get_file_date(file.stem))

        with file.open("r", encoding="ascii") as f:  # l'encodage ascii est le plus rapide
            for line in f:
                if line.startswith("#====== Signal to noise ratio"):
                    data = extract_sig_noise_ratio(f)
                    band_data.append(data)

                    for band in data.keys():
                        all_bands.add(band)

                    break

    # Conversion dans un format tabulaire
    data = {
        "date": [],
        # la sation est rajoutéé lors de l'insertion
        "constellation": [],
        "observation_type": [],
        "value": []
    }

    length = 0
    for band in all_bands:
        for i, band_value in enumerate(d.get(band, 0) for d in band_data):
            if band_value == 0:
                continue  # grafana gère bien les trous

            data["date"].append(dates[i].date())
            data["constellation"].append(band[:3]) # shortname
            data["observation_type"].append(band[3:])
            data["value"].append(band_value)

            length += 1

    return data, length


def fetch_or_create(cur, key, fetch_query, *insert_args):
    # Si l'id a déjà été recupéré, on le prend du cache
    cached = _database_fetch_cache.get(key)
    if not cached:
        return cached

    cur.execute(fetch_query, (key,))
    res = cur.fetchone()

    if not res:
        cur.execute(*insert_args)
        obj_id = cur.fetchone()["id"]
    else:
        obj_id = res["id"]

    _database_fetch_cache[key] = obj_id
    return obj_id


def insert_into_database(cur, data, station_fullname, length):
    station_id = fetch_or_create(
        cur, station_fullname,
        "select id from station where fullname = %s;",

        "insert into station (shortname, fullname) values (%s , %s) returning id;",
        (station_fullname[:4], station_fullname)
    )

    to_insert = []
    for i in range(length):
        # Constellation
        constellation_shortname = data["constellation"][i]
        constellation_id = fetch_or_create(
            cur, constellation_shortname,
            "select id from constellation where shortname = %s;",

            "insert into constellation (fullname, shortname) values (%s, %s) returning id;",
            ("??", constellation_shortname)
        )

        # Observation
        observation_type = data["observation_type"][i]
        observation_id = fetch_or_create(
            cur, observation_type,
            "select id from observation_type where type = %s;",

            "insert into observation_type (type) values (%s) returning id;",
            (observation_type,)
        )

        # On colle tout ensemble
        row = cur.mogrify(
            "(%s,%s,%s,%s,%s)",
            (data["date"][i], station_id, constellation_id, observation_id, data["value"][i])
        )
        to_insert.append(row)

    # On envoie dans la base de données
    cur.execute(
        "insert into sig2noise(date, station_id, constellation_id, observation_type_id, value) values " + \
        ",".join(to_insert)
    )


if __name__ == "__main__":
    flattened = []
    for dire in INFILES.iterdir():
        for file in dire.iterdir():
            flattened.append(file)

    flattened.sort(key=get_station_id)

    stations = []
    for key, group in groupby(flattened, get_station_id):
        stations.append((key, list(group)))

    print("Extraction des données...")
    extracted = []
    for station_fullname, files in tqdm(stations):
        data, length = get_station_data(files)
        extracted.append((data, station_fullname, length))

        break

    print("Insertion des données...")
    with psycopg.connect(
        "dbname=quality_check_data user=m1m",
        row_factory=dict_row, cursor_factory=ClientCursor
    ) as conn:
        with conn.cursor() as cur:
            for data, station_fullname, length in tqdm(extracted):
                insert_into_database(cur, data, station_fullname, length)

    print("OK !")
