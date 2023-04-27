# -*- coding: utf-8 -*-
"""
Script principal.
=================

Parse les fichiers XTR et insère les résultats dans une base de données.
"""
import argparse
import sys
from functools import partial
from itertools import groupby
from pathlib import Path
from datetime import date

import psycopg
from psycopg import ClientCursor
from psycopg.rows import dict_row
from tqdm import tqdm

from extractors import extract_sig2noise, get_file_date, get_station_id

HERE = Path(__file__).parent

# TODO: changer
INFILES = HERE / ".." / "graphes simples" / "data_2023"

db_connection = partial(
    psycopg.connect,
    dbname="quality_check_data",
    user="m1m", # TODO: changer
    row_factory=dict_row,
    cursor_factory=ClientCursor
)

_database_fetch_cache = {}


def get_station_data(files):
    """
    Extrait les données d'une station et les met en forme pour l'insertion dans
    une bdd de type relationelle.
    """
    extractors = {
        "Signal to noise ratio": 1
    }

    dates = []
    band_data = []
    all_bands = set()

    # Extraction des informations des fichiers
    for file in files:
        dates.append(get_file_date(file.stem))

        with file.open("r", encoding="ascii") as f:  # l'encodage ascii est le plus rapide
            for line in f:
                if line.startswith("#====== Signal to noise ratio"):
                    data = extract_sig2noise(f)
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

            data["date"].append(dates[i])
            data["constellation"].append(band[:3])  # shortname
            data["observation_type"].append(band[3:])
            data["value"].append(band_value)

            length += 1

    return data, length


def fetch_or_create(cur, key, fetch_query, *insert_args):
    """
    Récupère l'ID d'un objet à partir de la base de données ou crée un nouvel objet
    avec l'ID spécifié si aucun n'existe dans la base de données.
    """
    # Si l'id a déjà été recupéré, on le prend du cache
    cached = _database_fetch_cache.get(key)
    if cached:
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
    """
    Insère toute les données d'une station dans la base de données.
    """
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
        "insert into sig2noise(date, station_id, constellation_id, observation_type_id, value) values " +
        ",".join(to_insert)
    )


def get_all_files(after=None):
    """
    Renvoie la liste de tout les fichiers qui doivent êtres traités.
    On peut les filtrer pour uniquement avoir ceux crées après une certaine date.
    """
    if not after:
        after = date.fromtimestamp(0)

    flattened = [f for f in INFILES.rglob("*.xtr") if get_file_date(f.stem) > after]

    flattened.sort(key=get_station_id)

    return flattened


def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-o", "--override",
        help="Ecrase toute les données de la table de serie temporelle",
        action="store_true"
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()

    with db_connection() as conn:
        with conn.cursor() as cur:

            if args.override:
                print("La serie temporelle précédente va être écrasée.")
                cur.execute("delete from sig2noise;")
                latest_date = None

            else:
                cur.execute("""--sql
                    select distinct date
                    from sig2noise
                    order by date desc
                    limit 1;
                """)
                res = cur.fetchone()

                if res:
                    latest_date = res["date"]
                    print("Traitement des fichiers produits après le", latest_date, ".")
                else:
                    print("La base de données semble vide, nous allons tout envoyer.")
                    latest_date = None

    all_files = get_all_files(latest_date)

    nb_files = len(all_files)
    print(nb_files, "fichiers vont être traitées.")

    if nb_files == 0:
        sys.exit()

    # groupement des fichiers par station
    stations = []
    for key, group in groupby(all_files, get_station_id):
        stations.append((key, list(group)))

    print("Extraction des données...")
    extracted = []
    for station_fullname, files in tqdm(stations):
        data, length = get_station_data(files)
        extracted.append((data, station_fullname, length))

    print("Insertion des données...")
    with db_connection() as conn:
        with conn.cursor() as cur:
            for data, station_fullname, length in tqdm(extracted):
                insert_into_database(cur, data, station_fullname, length)

    print("OK !")
