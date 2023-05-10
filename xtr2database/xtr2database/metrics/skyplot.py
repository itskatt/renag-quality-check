from collections import defaultdict
import datetime as dt

from ..database import get_constellation_id


def _dd_callback():
    return {
        "ELE": [],
        "AZI": [],
        #     toute les bandes
        "mp": defaultdict(list),
        "sig2noise": defaultdict(list)
    }


def create_dest():
    #      constel             datetime
    return defaultdict(lambda: defaultdict(_dd_callback))


def _extract_coord(f, date, data):
    next(f) # entête partie

    line = next(f)
    while line != "\n":
        splitted = line.split()

        constel = splitted[0][0:3]
        coord = splitted[0][3:7] # ELE ou AZI

        time = dt.time.fromisoformat(splitted[2])
        line_datetime = dt.datetime.combine(date, time)


        data[constel][line_datetime][coord].append(
            [int(v) if v != "-" else None for v in splitted[4:]]
        )

        line = next(f)


def extract_elevation_azimut(f, data, date):
    # elevation
    _extract_coord(f, date, data)

    # azimut
    _extract_coord(f, date, data)


def _extract_individual_metric(f, data, date, metric_type):
    while True:
        line = next(f)

        if line == "\n":
            # est-ce que on se situe entre deux bandes ou à
            # la fin des données à extraire
            line = next(f)
            if line == "\n":
                # fin des données à extraire
                break

        # on peut commencer à extraire
        splitted = line.split()

        constel = splitted[0][0:3]
        band = splitted[0][4:7]

        time = dt.time.fromisoformat(splitted[2])
        line_datetime = dt.datetime.combine(date, time)

        data[constel][line_datetime][metric_type][band].append(
            [int(v) if v != "-" else None for v in splitted[4:]]
        )


def extract_multipath(f, data, date):
    _extract_individual_metric(f, data, date, "mp")


def extract_sig2noise(f, data, date):
    _extract_individual_metric(f, data, date, "sig2noise")


def insert(cur, station_id, skyplot_data):
    to_insert = []

    for constel, constel_data in skyplot_data.items():
        constellation_id = get_constellation_id(cur, constel)

        for datetime, all_data in constel_data.items():

            # Pour chaque "lignes" de coordonées
            for ele_coords, azi_coords in zip(all_data["ELE"], all_data["AZI"]):
                
                # On joint les coordonées ensemble (ele, azi)
                for i, (ele, azi) in enumerate(zip(ele_coords, azi_coords)):
                    satellite_number = i + 1

                    # Reste plus qu'a calculer les mp et sig2noises...
                    # TODO
