# -*- coding: utf-8 -*-
"""
Script principal.
=================

Parse les fichiers XTR et insère les résultats dans une base de données.
"""
import argparse
import sys
import os
from datetime import date
from itertools import groupby
from pathlib import Path

from tqdm import tqdm

from .database import db_connection, fetch_or_create
from .extractors import get_file_date, get_station_id
from .metrics import sig2noise


def get_station_data(files):
    """
    Extrait les données d'une station et les met en forme pour l'insertion dans
    une bdd de type relationelle.

    Les données extraites :
        - Sig2Noise
        - Multipath
    """
    station_data = []

    sig2noise_data = {
        "type": "sig2noise",
        "length": 0,
        "data": {
            "date": [],
            # la sation est rajoutée lors de l'insertion
            "constellation": [],
            "observation_type": [],
            "value": []
        }
    }

    # Extraction des informations des fichiers
    for file in files:
        current_date = get_file_date(file.stem)

        with file.open("r", encoding="ascii") as f:  # l'encodage ascii est le plus rapide
            for line in f:
                if line.startswith("#====== Signal to noise ratio"):
                    sig2noise_extracted = sig2noise.extract(f)

                    data = sig2noise_data["data"]
                    for band, value in sig2noise_extracted.items():
                        sig2noise_data["length"] += 1

                        data["date"].append(current_date)
                        data["constellation"].append(band[:3])  # shortname
                        data["observation_type"].append(band[-2:]) # 2 derniers caractères
                        data["value"].append(value)

                    break

    station_data.append(sig2noise_data)
    return station_data


def insert_into_database(cur, data, station_fullname):
    """
    Insère toute les données d'une station dans la base de données.
    """
    station_id = fetch_or_create(
        cur, station_fullname,
        "select id from station where fullname = %s;",

        "insert into station (shortname, fullname) values (%s , %s) returning id;",
        (station_fullname[:4], station_fullname)
    )

    for metric in data:
        if metric["type"] == "sig2noise":
            sig2noise.insert(cur, station_id, metric)


def get_all_files(after=None):
    """
    Renvoie la liste de tout les fichiers qui doivent êtres traités.
    On peut les filtrer pour uniquement avoir ceux crées après une certaine date.
    """
    infiles = Path(os.environ["XTR_FILES_ROOT"])

    if not after:
        after = date.fromtimestamp(0)

    flattened = [f for f in infiles.rglob("*.xtr") if get_file_date(f.stem) > after]

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


def main():
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
        station_data = get_station_data(files)
        extracted.append((station_data, station_fullname))

    print("Insertion des données...")
    with db_connection() as conn:
        with conn.cursor() as cur:
            for station_data, station_fullname in tqdm(extracted):
                insert_into_database(cur, station_data, station_fullname)

    print("OK !")
