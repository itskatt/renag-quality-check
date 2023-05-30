# -*- coding: utf-8 -*-
"""
Script principal.
=================

Parse les fichiers XTR et insère les résultats dans une base de données.
"""
import argparse
import os
import sys
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import date
from itertools import groupby
from multiprocessing import Manager
from pathlib import Path

from tqdm import tqdm

from .database import DatabaseFetcher, clear_tables, create_db_connection
from .extractors import get_file_date, get_station_coords, get_station_id
from .metrics import (TimeSeries, common, create_metric_dest, cycle_slip,
                      extract_from_section_header_into, skyplot)


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
        - Les coordonées de la station
        - La liste des fichiers traités
    """
    sig2noise_data = create_metric_dest(TimeSeries.SIG2NOISE)
    multipath_data = create_metric_dest(TimeSeries.MULTIPATH)

    observation_cs = create_metric_dest(TimeSeries.OBSERVATION_CS)
    satellite_cs = create_metric_dest(TimeSeries.SATELLITE_CS)

    skyplot_data = skyplot.create_dest()

    station_coords = (None, None)

    inserted_files = []

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
                if parsed_sections == 7:
                    break

                elif line.startswith("#====== Summary statistics"):
                    nb_constell = cycle_slip.extract_from_sum_stats(f, observation_cs, satellite_cs, current_date)
                    parsed_sections += 1

                elif line.startswith("#====== Estimated values"):
                    if station_coords[0] is None:
                        station_coords = get_station_coords(f)
                    parsed_sections += 1

                elif line.startswith("#====== Band available"):
                    cycle_slip.extract_from_band_avail(f, satellite_cs, nb_constell)
                    parsed_sections += 1

                elif line.startswith("#====== Preprocessing results"):
                    cycle_slip.extract_from_prepro_res(f, satellite_cs, skyplot_data, nb_constell, current_date)
                    parsed_sections += 1

                elif line.startswith("#====== Elevation & Azimuth"):
                    skyplot.extract_elevation_azimut(f, skyplot_data, current_date)
                    parsed_sections += 1

                elif line.startswith("#====== Code multipath"):
                    if extract_from_section_header_into(f, multipath_data, current_date):
                        skyplot.extract_multipath(f, skyplot_data, current_date)
                    parsed_sections += 1

                elif line.startswith("#====== Signal to noise ratio"):
                    if extract_from_section_header_into(f, sig2noise_data, current_date):
                        skyplot.extract_sig2noise(f, skyplot_data, current_date)
                    parsed_sections += 1

        inserted_files.append(filename)

    return ((
            sig2noise_data,
            multipath_data,
            observation_cs,
            satellite_cs
        ),
        skyplot_data,
        station_coords,
        inserted_files
    )


def insert_into_database(cur, fetcher, data, station_fullname, station_network):
    """
    Insère toute les données d'une station dans la base de données.
    """
    # récupération de la station
    station_lat, station_long = data[2]

    station_id = fetcher.fetch_or_create(
        cur, station_fullname,
        "select id from station where fullname = %s;",

        "insert into station (shortname, fullname, lat, long) values (%s , %s, %s, %s) returning id;",
        (station_fullname[:4], station_fullname, station_lat, station_long)
    )

    # lien avec le réseau
    network_id = fetcher.fetch_or_create(
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
            cycle_slip.insert_observation(cur, fetcher, station_id, time_serie)

        elif time_serie["type"] == TimeSeries.SATELLITE_CS.value:
            cycle_slip.insert_satellite(cur, fetcher, station_id, time_serie)

        else:
            common.insert_header_section_metric(cur, fetcher, station_id, time_serie)

    # ensuite le skyplot (pas de boucle comme y'en a un seul)
    skyplot.insert(cur, fetcher, station_id, data[1])

    # On note les fichiers traités
    to_insert = ",".join(cur.mogrify("(%s,%s)", (f, station_id)) for f in data[3])
    cur.execute(
        f"""--sql
        insert into inserted_file (name, station_id)
        values {to_insert}
        on conflict do nothing;
        """
    )


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


def process_station(db_connection, station_fullname, station_files, station_network, lock=None):
    """
    Extrait les données d'une sation et les insère dans la base de données.
    Les noms des fichiers doivent être des chaines de caractère
    """
    try:
        station_data = get_station_data(station_files)

        with db_connection() as conn:
            with conn.cursor() as cur:
                insert_into_database(cur, DatabaseFetcher(lock), station_data, station_fullname, station_network)
    except Exception:
        with open("concurent-errors.log", "a") as f:
            f.write(f"Erreur lors du traitement de la station {station_fullname}\n")
            traceback.print_exc(file=f)
            f.write("\n")


def process_sequencial(db_connection, stations, network):
    print("Traitement des stations en séquenciel...")

    for name, files in tqdm(stations):
        process_station(db_connection, name, files, network)


def process_parallel(db_connection, stations, network):
    print("Traitement des stations en paralèlle...")
    manager = Manager()
    lock = manager.Lock()

    with tqdm(total=len(stations)) as pbar:
        # On traite la première station toute seule pour limiter les conditions de concurence
        first = stations.pop(0)
        process_station(db_connection, first[0], first[1], network)
        pbar.update(1)

        with ProcessPoolExecutor() as executor:
            # NOTE : ne pas oublier de mettre a jour en fonction de la signature de process_station
            futures = [executor.submit(process_station, name, files, network, lock) for name, files in stations]
            for _ in as_completed(futures):
                pbar.update(1)


def get_args():
    """
    Parse les arguments en lignes de commandes avec argparse.
    """
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
        help="Ecrase toute les données du réseau de station avant de les insérer",
        action="store_true"
    )

    parser.add_argument(
        "-p", "--parallel",
        help="Traite les stations en parallèle sur plusieurs processus",
        action="store_true"
    )

    parser.add_argument(
        "-U", "--user",
        help="Spécifie le nom d'utilisateur pour se connecter à la base de données"
    )

    parser.add_argument(
        "-P", "--password",
        help="Spécifie le mot de passe à utiliser pour se connecter à la base de données"
    )

    return parser.parse_args()


def override_insert(cur, args):
    """
    Prépare pour une insertion en écrasant les données existantes.
    Renvoie la liste de tout les fichiers sans filtre.
    """
    print(f"Toutes les données du réseau {args.network} vont êtres ecrasées.")
    print("Suppression...")
    clear_tables(cur, args.network)
    return get_all_files(args.xtr_files)


def strict_insert(cur, args):
    """
    Prépare pour une insertion en se basant sur les fichiers déjà insérés.
    Renvoie la liste de tout les fichiers qui ne sont pas déjà insérés.
    """
    print("Récupération des fichiers insérés dans la base de données...")
    cur.execute(
        """--sql
        select i.name as name
        from inserted_file i
        inner join station s on s.id = i.station_id
        inner join station_network sn on s.id = sn.station_id
        inner join network n on n.id = sn.network_id
        where n.name = %s;
        """,
        (args.network,)
    )
    res = cur.fetchall()

    blacklisted_files = [r["name"] for r in res]
    print(f"{len(blacklisted_files)} fichiers trouvés.")

    return [file for file in get_all_files(args.xtr_files) if file.stem not in blacklisted_files]


def main():
    """
    Programme principal.
    """
    args = get_args()

    # Les arguments CLI sont prioritaire sur les variables d'env
    if not args.user:
        try:
            user = os.environ["X2D_USER"]
        except KeyError:
            print(
                "Erreur : pas d'utilisateur spécifié (ni dans la variable "
                "d'environement X2D_USER ni en argument de ligne de commande)"
            )
            sys.exit(-1)
    else:
        user = args.user

    password = args.password or os.environ.get("X2D_PASSWORD")

    db_connection = create_db_connection(user, password)

    with db_connection() as conn:
        with conn.cursor() as cur:

            if args.override:
                all_files = override_insert(cur, args)

            else:
                all_files = strict_insert(cur, args)

    nb_files = len(all_files)
    print(nb_files, "fichiers vont être traitées.")

    if nb_files == 0:
        sys.exit()

    # groupement des fichiers par station
    stations = []
    for key, group in groupby(all_files, get_station_id):
        stations.append((key, list(str(f.resolve()) for f in group))) # type: ignore

    if args.parallel:
        process_parallel(db_connection, stations, args.network)
    else:
        process_sequencial(db_connection, stations, args.network)

    print("OK !")
