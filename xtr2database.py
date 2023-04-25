"""
Script principal.
=================

Parse les fichiers XTR et insère les résultats dans une base de données.
"""
from itertools import groupby
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from tqdm import tqdm

from extractors import extract_sig_noise_ratio, get_file_date, get_station_id

HERE = Path(__file__).parent

# Temporaire
INFILES = HERE / ".." / "graphes simples" / "data_2023"


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


def get_or_create(cur, key, fetch_query, *insert_args):
    cur.execute(fetch_query, (key,))
    res = cur.fetchone()

    if not res:
        cur.execute(*insert_args)
        return cur.fetchone()["id"]
    else:
        return res["id"]


def insert_into_database(cur, data, station_fullname, length):
    # Récupération de l'id de la station et insertion si pas présente
    cur.execute("select id from station where fullname = %s;", (station_fullname,))
    res = cur.fetchone()

    if not res:
        cur.execute(
            "insert into station (shortname, fullname) values (%s , %s) returning id;",
            (station_fullname[:4], station_fullname)
        )
        station_id = cur.fetchone()["id"]
    else:
        station_id = res["id"]

    for i in range(length):
        # Constellation
        constel_shortname = data["constellation"][i]
        cur.execute("select id from constellation where shortname = %s;", (constel_shortname,))
        res = cur.fetchone()

        if not res:
            cur.execute(
                "insert into constellation (fullname, shortname) values (%s, %s) returning id;",
                ("??", constel_shortname)
            )
            constel_id = cur.fetchone["id"]
        else:
            constel_id = res["id"]

        # Observation
        obs_type = data["observation_type"][i]


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
    with psycopg.connect("dbname=quality_check_data user=m1m", row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            for data, station_fullname, length in tqdm(extracted):
                insert_into_database(cur, data, station_fullname, length)

    print("OK !")
