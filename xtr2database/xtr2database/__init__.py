# -*- coding: utf-8 -*-
"""
Script principal.
=================

Parse les fichiers XTR et insère les résultats dans une base de données.
"""
import argparse
import os
import sys
from datetime import date
from itertools import groupby
from pathlib import Path

from tqdm import tqdm

from .database import db_connection, fetch_or_create
from .extractors import get_file_date, get_station_id
from .metrics import (Metric, create_metric_dest, extract_from_section_header_into,
                      insert_header_section_metric, cycle_slip)


def get_station_data(files):
    """
    Extrait les données d'une station et les met en forme pour l'insertion dans
    une bdd de type relationelle.

    Les données extraites :
        - Sig2Noise
        - Multipath
        - Observation CS
        - Satellite CS
    """
    sig2noise_data = create_metric_dest(Metric.SIG2NOISE)
    multipath_data = create_metric_dest(Metric.MULTIPATH)

    observation_cs = create_metric_dest(Metric.OBSERVATION_CS)
    satellite_cs = create_metric_dest(Metric.SATELLITE_CS)

    # Extraction des informations des fichiers
    for file in files:
        current_date = get_file_date(file.stem)

        parsed_sections = 0
        with file.open("r", encoding="ascii") as f:  # l'encodage ascii est le plus rapide
            for line in f:
                if parsed_sections == 5:
                    break

                # TODO : mettre dans l'ordre du fichier
                elif line.startswith("#====== Summary statistics"):
                    cycle_slip.extract_from_sum_stats(f, observation_cs, satellite_cs, current_date)
                    parsed_sections += 1

                elif line.startswith("#====== Preprocessing results"):
                    cycle_slip.extract_from_prepro_res(f, satellite_cs)
                    parsed_sections += 1

                elif line.startswith("#====== Band available"):
                    cycle_slip.extract_from_band_avail(f, satellite_cs)
                    parsed_sections += 1

                elif line.startswith("#====== Signal to noise ratio"):
                    extract_from_section_header_into(f, sig2noise_data, current_date)
                    parsed_sections += 1

                elif line.startswith("#====== Code multipath"):
                    extract_from_section_header_into(f, multipath_data, current_date)
                    parsed_sections += 1

    return [
        sig2noise_data,
        multipath_data,
        observation_cs,
        satellite_cs
    ]


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
        if metric["type"] == Metric.OBSERVATION_CS.value:
            cycle_slip.insert_observation(cur, station_id, metric)

        elif metric["type"] == Metric.SATELLITE_CS.value:
            cycle_slip.insert_satellite(cur, station_id, metric)

        else:
            insert_header_section_metric(cur, station_id, metric)


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
                print("Les series temporelle précédentes vont êtres écrasées.")
                for metric in Metric:
                    cur.execute("delete from " + metric.value) # FIXME
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
                    latest_date = res["date"] # type: ignore
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