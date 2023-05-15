# -*- coding: utf-8 -*-
"""
Script principal.
=================

Parse les fichiers XTR et insère les résultats dans une base de données.
"""
import argparse
import os
import sys
from concurrent.futures import ProcessPoolExecutor as PoolExecutor
from concurrent.futures import as_completed
from datetime import date
from itertools import groupby
from pathlib import Path

from tqdm import tqdm

from .database import (clear_tables, db_connection, fetch_or_create,
                       get_latest_date)
from .extractors import get_file_date, get_station_id
from .metrics import (TimeSeries, create_metric_dest, cycle_slip,
                      extract_from_section_header_into,
                      common, skyplot)


def get_station_data(files):
    """
    Extrait les données d'une station et les met en forme pour l'insertion dans
    une bdd de type relationelle.

    Les données extraites :
        - Sig2Noise
        - Multipath
        - Observation CS
        - Satellite CS
        - Skyplots
    """
    sig2noise_data = create_metric_dest(TimeSeries.SIG2NOISE)
    multipath_data = create_metric_dest(TimeSeries.MULTIPATH)

    observation_cs = create_metric_dest(TimeSeries.OBSERVATION_CS)
    satellite_cs = create_metric_dest(TimeSeries.SATELLITE_CS)

    skyplot_data = skyplot.create_dest()

    # Extraction des informations des fichiers
    for file in files:
        filename = file.split(".")[-2].rpartition(os.sep)[-1]
        current_date = get_file_date(filename)

        parsed_sections = 0
        with open(file, "r", encoding="ascii") as f:  # l'encodage ascii est le plus rapide
            # extract_from_prepro_res et extract_from_band_avail ont besoin de savoir
            #   cb ya de constellation au total dans le fichier (pour
            #   marquer clairement à 0 les absences de CS et eviter les décalages)
            # on initialisa a None pour clairement afficher un état illégal
            nb_constell = None
            for line in f:
                if parsed_sections == 6:
                    break

                elif line.startswith("#====== Summary statistics"):
                    nb_constell = cycle_slip.extract_from_sum_stats(f, observation_cs, satellite_cs, current_date)
                    parsed_sections += 1

                elif line.startswith("#====== Band available"):
                    cycle_slip.extract_from_band_avail(f, satellite_cs, nb_constell)
                    parsed_sections += 1

                elif line.startswith("#====== Preprocessing results"):
                    cycle_slip.extract_from_prepro_res(f, satellite_cs, nb_constell)
                    parsed_sections += 1

                elif line.startswith("#====== Elevation & Azimuth"):
                    skyplot.extract_elevation_azimut(f, skyplot_data, current_date)
                    parsed_sections += 1

                elif line.startswith("#====== Code multipath"):
                    extract_from_section_header_into(f, multipath_data, current_date)
                    skyplot.extract_multipath(f, skyplot_data, current_date)
                    parsed_sections += 1

                elif line.startswith("#====== Signal to noise ratio"):
                    extract_from_section_header_into(f, sig2noise_data, current_date)
                    skyplot.extract_sig2noise(f, skyplot_data, current_date)
                    parsed_sections += 1

    return ((
            sig2noise_data,
            multipath_data,
            observation_cs,
            satellite_cs
        ),
        skyplot_data
    )


def insert_into_database(cur, data, station_fullname, station_network):
    """
    Insère toute les données d'une station dans la base de données.
    """
    # récupération de la station
    station_id = fetch_or_create(
        cur, station_fullname,
        "select id from station where fullname = %s;",

        "insert into station (shortname, fullname) values (%s , %s) returning id;",
        (station_fullname[:4], station_fullname)
    )

    # lien avec le réseau
    network_id = fetch_or_create(
        cur, station_network,
        "select id from network where name = %s;",

        "insert into network (name) values (%s) returning id;",
        (station_network,)
    )

    cur.execute(
        f"""--sql
        select count(*)
        from station_network
        where station_id = {station_id} and network_id = {network_id};
        """
    )
    res = cur.fetchone()

    # Si la station ne fait pas partie du réseau, on la relie
    if res["count"] == 0:
        cur.execute(f"insert into station_network (station_id, network_id) values ({station_id}, {network_id});")

    # Insertion des données de la station
    for time_serie in data[0]: # en premier les séries temporelles
        if time_serie["type"] == TimeSeries.OBSERVATION_CS.value:
            cycle_slip.insert_observation(cur, station_id, time_serie)

        elif time_serie["type"] == TimeSeries.SATELLITE_CS.value:
            cycle_slip.insert_satellite(cur, station_id, time_serie)

        else:
            common.insert_header_section_metric(cur, station_id, time_serie)

    # ensuite le skyplot (pas de boucle comme y'en a un seul)
    skyplot.insert(cur, station_id, data[1])


def get_all_files(infiles, after=None):
    """
    Renvoie la liste de tout les fichiers qui doivent êtres traités.
    On peut les filtrer pour uniquement avoir ceux crées après une certaine date.
    """
    if not after:
        after = date.fromtimestamp(0)

    flattened = [f for f in infiles.rglob("*.xtr") if get_file_date(f.stem) > after]

    flattened.sort(key=get_station_id)

    return flattened


def process_station(station_fullname, station_files, station_network):
    """
    Extrait les données d'une sation et les insère dans la base de données.
    Les noms des fichiers doivent être des chaines de caractère
    """
    station_data = get_station_data(station_files)

    # TODO réutiliser les connections ?
    with db_connection() as conn:
        with conn.cursor() as cur:
            insert_into_database(cur, station_data, station_fullname, station_network)


def process_parallel(stations):
    raise NotImplementedError("Pas encore utilisable...")

    print("Traitement des stations en paralèlle...")
    with tqdm(total=len(stations)) as pbar:
        with PoolExecutor() as executor:
            # NOTE : ne pas oublier de mettre a jour en fonction de la signature de process_station
            futures = [executor.submit(process_station, name, files) for name, files in stations]
            for _ in as_completed(futures):
                pbar.update(1)


def process_sequencial(stations, network):
    print("Traitement des stations en séquenciel...")
    for name, files in tqdm(stations):
        process_station(name, files, network)


def get_args():
    parser = argparse.ArgumentParser("xtr2database")

    parser.add_argument(
        "xtr_files",
        help="Sources des fichiers xtr à traiter",
        type=Path
    )

    parser.add_argument(
        "network",
        help="Le réseau de station dont proviennent les fichiers"
    )

    parser.add_argument(
        "-o", "--override",
        help="Ecrase toute les données de cette station",
        action="store_true"
    )

    parser.add_argument(
        "-p", "--parallel",
        help="Traite les stations en parallèle",
        action="store_true"
    )

    return parser.parse_args()


def main():
    args = get_args()

    with db_connection() as conn:
        with conn.cursor() as cur:

            if args.override:
                print("Toutes les tables vont êtres ecrasées.")
                clear_tables(cur)
                latest_date = None

            else:
                print("Intérogation de la base de données...")
                dates = [get_latest_date(cur, m.value) for m in TimeSeries]
                dates.append(get_latest_date(cur, "skyplot"))

                if len(set(dates)) == 1 and dates[0] is not None:
                    latest_date = dates[0]
                    print(f"Traitement des fichiers produits après le {latest_date}.")
                else:
                    print("La base de données n'est pas consistante, nous allons tout envoyer.")
                    print("Suppression...")
                    clear_tables(cur)
                    latest_date = None

    all_files = get_all_files(args.xtr_files, latest_date)

    nb_files = len(all_files)
    print(nb_files, "fichiers vont être traitées.")

    if nb_files == 0:
        sys.exit()

    # groupement des fichiers par station
    stations = []
    for key, group in groupby(all_files, get_station_id):
        stations.append((key, list(str(f.resolve()) for f in group)))

    if args.parallel:
        process_parallel(stations)
    else:
        process_sequencial(stations, args.network)

    print("OK !")
