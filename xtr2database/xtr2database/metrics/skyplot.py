from collections import defaultdict
import datetime as dt

from ..database import get_constellation_id


def _dd_callback():
    """
    Contruit la partie qui acceuil l'évélation, l'azimut ainsi que les multipath et
    le sig23noise en fonction des bandes.
    """
    return {
        "ELE": [],
        "AZI": [],
        #     toute les bandes
        "mp": {},
        "sig2noise": {}
    }


def create_dest():
    """
    Contruit la structure de données qui acceuil les données pour les skyplots
    d'une station.
    """
    #      constel             datetime
    return defaultdict(lambda: defaultdict(_dd_callback))


def _extract_coord(f, date, data):
    """
    Extrait l'evevation où l'azimut.
    """
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
    """
    Extrait l'elevation et l'azimut de la section correspondante.
    """
    # elevation
    _extract_coord(f, date, data)

    # azimut
    _extract_coord(f, date, data)


def _extract_individual_metric(f, data, date, metric_type):
    """
    Extrait une metrique "individuelle" : dans notre cas le multipath ou
    le sig2noise.
    """
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

        if band not in data[constel][line_datetime][metric_type].keys():
            data[constel][line_datetime][metric_type][band] = []

        data[constel][line_datetime][metric_type][band].append(
            [int(v) if v != "-" else None for v in splitted[4:]]
        )


def extract_multipath(f, data, date):
    """
    Extrait le multipath indivuduel de sa section.
    """
    _extract_individual_metric(f, data, date, "mp")


def extract_sig2noise(f, data, date):
    """
    Extrait le sig2noise indivuduel de sa section.
    """
    _extract_individual_metric(f, data, date, "sig2noise")


_SKYPLOT_METRICS = {
    1: {
        "GPS": ("1C", "1*"),
        "GLO": ("1C", "1*"),
        "GAL": ("1X", "1*"),
        "BDS": ("2I", "2*")
    },
    2: {
        "GPS": ("2W", "2*"),
        "GLO": ("2P", "2*"),
        "GAL": ("7X", "7*"),
        "BDS": ("6I", "6*")
    },
    5: {
        "GPS": ("5X", "5*"),
        "GLO": ("3X", "3*"),
        "GAL": ("6X", "6*"),
        "BDS": ("7I", "7*")
    }
}


def _get_skyplot_metric(constel, metric, number, i_line, i_coord, all_data):
    try:
        band, backup = _SKYPLOT_METRICS[number][constel]
    except KeyError:
        # Si la constellation n'est pas dans le tableau
        return None

    to_return = None
    try:
        to_return = all_data[metric][band][i_line][i_coord]
    except KeyError:
        for key in all_data[metric].keys():
            if key[0] == backup[0]:
                to_return = all_data[metric][key][i_line][i_coord]

    return to_return or None


def insert(cur, station_id, skyplot_data):
    """
    Insère les données du skyplot dans la base de données.
    """
    to_insert = []

    for constel, constel_data in skyplot_data.items():
        constellation_id = get_constellation_id(cur, constel)

        for datetime, all_data in constel_data.items():

            # Pour chaque "lignes" de coordonées
            for i_line, (ele_coords, azi_coords) in enumerate(zip(all_data["ELE"], all_data["AZI"])):

                # On joint les coordonées ensemble (ele, azi)
                for i_coord, (ele, azi) in enumerate(zip(ele_coords, azi_coords)):
                    if ele is None:
                        continue

                    satellite_number = i_coord + 1

                    # On peut enfin insèrer la rangée !
                    row = "\t".join(map(str, (
                            datetime, station_id, constellation_id,
                            satellite_number, ele, azi,

                            # Les mp1-5
                            _get_skyplot_metric(constel, "mp", 1, i_line, i_coord, all_data),
                            _get_skyplot_metric(constel, "mp", 2, i_line, i_coord, all_data),
                            _get_skyplot_metric(constel, "mp", 5, i_line, i_coord, all_data),

                            # Les sig2noise1-5
                            _get_skyplot_metric(constel, "sig2noise", 1, i_line, i_coord, all_data),
                            _get_skyplot_metric(constel, "sig2noise", 2, i_line, i_coord, all_data),
                            _get_skyplot_metric(constel, "sig2noise", 5, i_line, i_coord, all_data),
                    )))

                    to_insert.append(row)

    with cur.connection.transaction():
        # On est obligé de passer par une table intermédiaire parce que COPY
        # ne supporte pas ON CONFLICT
        cur.execute(
            """--sql
            create temporary table tmp_skyplot
            (like skyplot including defaults)
            on commit drop;
            """
        )

        with cur.copy(
            """--sql
            copy tmp_skyplot (
                datetime, station_id, constellation_id,
                satellite, elevation, azimut,
                mp1, mp2, mp5,
                sig2noise1, sig2noise2, sig2noise5
            ) from stdin
            with null as 'None'
            """) as copy:
                copy.write("\n".join(to_insert))

        cur.execute(
            """--sql
            insert into skyplot
            (
                datetime, station_id, constellation_id,
                satellite, elevation, azimut,
                mp1, mp2, mp5,
                sig2noise1, sig2noise2, sig2noise5
            )
            (select 
                datetime, station_id, constellation_id,
                satellite, elevation, azimut,
                mp1, mp2, mp5,
                sig2noise1, sig2noise2, sig2noise5
            from tmp_skyplot)
            on conflict do nothing;
            """
        )
