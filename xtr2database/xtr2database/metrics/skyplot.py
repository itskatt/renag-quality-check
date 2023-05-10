from collections import defaultdict
import datetime as dt

from ..database import get_constellation_id


def _extract_coord(f, data):
    next(f) # entête partie

    line = next(f)
    while line != "\n":
        splitted = line.split()

        constel = splitted[0][0:3]
        coord = splitted[0][3:7]

        data[constel][coord].append(
            [int(v) if v != "-" else -1 for v in splitted[4:]]
        )

        line = next(f)


def extract_elevation_azimut(f):
    data = defaultdict(lambda: dict(ELE=list(), AZI=list()))

    # elevation
    _extract_coord(f, data)

    # azimut
    _extract_coord(f, data)

    return data


def extract_individual_metric(f, date):
    data = defaultdict(lambda: defaultdict(list))

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

        data[constel][band].append((
            line_datetime,
            [int(v) if v != "-" else -1 for v in splitted[4:]]
        ))

    return data


def insert(cur, station_id, skyplot_data):
    to_insert = []

    for ele_azi_data, ind_multipath_data, ind_sig2noise_data in skyplot_data:
        
        # Pour chaque constellation de satellites...
        for constel, coords in ele_azi_data.items():
            constellation_id = get_constellation_id(cur, constel)

            # Pour chaque "lignes" de coordonées (même datetime)
            for ele_coords, azi_coords in zip(coords["ELE"], coords["AZI"]):
                # On joint les coordonées ensemble (ele, azi)
                for i, (ele, azi) in enumerate(zip(ele_coords, azi_coords)):
                    satellite_number = i + 1

                    (ele, azi)
