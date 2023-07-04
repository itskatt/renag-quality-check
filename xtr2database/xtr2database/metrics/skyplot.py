"""
MIT License

Copyright (c) 2023 Raphaël Caldwell

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import datetime as dt
from collections import defaultdict


def _dd_callback():
    """
    Contruit la partie qui acceuil l'évélation, l'azimut ainsi que les multipath et
    le sig2noise en fonction des bandes.
    """
    return {
        "ELE": [],
        "AZI": [],
        #     toute les bandes
        "mp": {},
        "sig2noise": {},
        # si ça a cs
        "cs": {},
    }


def create_dest():
    """
    Contruit la structure de données qui acceuil les données pour les skyplots
    d'une station.
    """
    #      constel             datetime
    return defaultdict(lambda: defaultdict(_dd_callback))


def _safe_to_int(value):
    try:
        return int(value)
    except ValueError:
        return None


def _extract_coord(f, date, data):
    """
    Extrait l'evevation où l'azimut.
    """
    next(f)  # entête partie

    line = next(f)
    while line != "\n":
        splitted = line.split()

        constel = splitted[0][0:3]
        coord = splitted[0][3:7]  # ELE ou AZI

        time = dt.time.fromisoformat(splitted[2])
        line_datetime = dt.datetime.combine(date, time)

        data[constel][line_datetime][coord].append([_safe_to_int(v) for v in splitted[4:]])

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

        data[constel][line_datetime][metric_type][band].append([_safe_to_int(v) for v in splitted[4:]])


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


_SKYPLOT_OBS_TYPE = {
    1: {"GPS": ("1C", "1*"), "GLO": ("1C", "1*"), "GAL": ("1X", "1*"), "BDS": ("2I", "2*")},
    2: {"GPS": ("2W", "2*"), "GLO": ("2P", "2*"), "GAL": ("7X", "7*"), "BDS": ("6I", "6*")},
    5: {"GPS": ("5X", "5*"), "GLO": ("3X", "3*"), "GAL": ("6X", "6*"), "BDS": ("7I", "7*")},
}


def _get_skyplot_obs_type(constel, metric, number, i_line, i_coord, all_data):
    """
    Renvoie le type d'observable sur lequel se baser pour créer des skyplots.
    """
    try:
        band, backup = _SKYPLOT_OBS_TYPE[number][constel]
    except KeyError:
        # Si la constellation n'est pas dans le tableau
        return None, None

    to_return = None
    used_band = None
    try:
        to_return = all_data[metric][band][i_line][i_coord]
        used_band = band
    except KeyError:
        for key in all_data[metric].keys():
            if key[0] == backup[0]:
                to_return = all_data[metric][key][i_line][i_coord]
                used_band = key

    return to_return, used_band


_already_inserted_obs_types = set()


def insert(cur, fetcher, station_id, skyplot_data):
    """
    Insère les données du skyplot dans la base de données.
    """
    to_insert = []

    for constel, constel_data in skyplot_data.items():
        constellation_id = fetcher.get_constellation_id(cur, constel)

        for datetime, all_data in constel_data.items():
            date = datetime.date()
            date_id = fetcher.fetch_or_create(
                cur,
                date,
                "select id from skyplot_date where date = %s;",
                "insert into skyplot_date (date) values (%s) returning id;",
                (date,),
            )

            # Pour chaque "lignes" de coordonées
            for i_line, (ele_coords, azi_coords) in enumerate(zip(all_data["ELE"], all_data["AZI"])):
                # On joint les coordonées ensemble (ele, azi)
                for i_coord, (ele, azi) in enumerate(zip(ele_coords, azi_coords)):
                    if ele is None:
                        continue

                    satellite_number = i_coord + 1

                    mp1, used_mp1 = _get_skyplot_obs_type(constel, "mp", 1, i_line, i_coord, all_data)
                    mp2, used_mp2 = _get_skyplot_obs_type(constel, "mp", 2, i_line, i_coord, all_data)
                    mp5, used_mp5 = _get_skyplot_obs_type(constel, "mp", 5, i_line, i_coord, all_data)

                    sig2noise1, used_sig2noise1 = _get_skyplot_obs_type(
                        constel, "sig2noise", 1, i_line, i_coord, all_data
                    )
                    sig2noise2, used_sig2noise2 = _get_skyplot_obs_type(
                        constel, "sig2noise", 2, i_line, i_coord, all_data
                    )
                    sig2noise5, used_sig2noise5 = _get_skyplot_obs_type(
                        constel, "sig2noise", 5, i_line, i_coord, all_data
                    )

                    # insertion des used_* dans la bdd si ils n'y sont pas
                    if (date_id, station_id, constellation_id) not in _already_inserted_obs_types:
                        cur.execute(
                            """--sql
                            insert into skyplot_used_band
                                (
                                    date_id, station_id, constellation_id,
                                    mp1_observation_type_id,
                                    mp2_observation_type_id,
                                    mp5_observation_type_id,
                                    sig2noise1_observation_type_id,
                                    sig2noise2_observation_type_id,
                                    sig2noise5_observation_type_id
                                )
                            values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            on conflict do nothing;
                            """,
                            (
                                date_id,
                                station_id,
                                constellation_id,
                                fetcher.get_observation_id(cur, used_mp1),
                                fetcher.get_observation_id(cur, used_mp2),
                                fetcher.get_observation_id(cur, used_mp5),
                                fetcher.get_observation_id(cur, used_sig2noise1),
                                fetcher.get_observation_id(cur, used_sig2noise2),
                                fetcher.get_observation_id(cur, used_sig2noise5),
                            ),
                        )

                        _already_inserted_obs_types.add((date_id, station_id, constellation_id))

                    # On determine si ça a cycle slip
                    cs_bands = all_data["cs"].get(satellite_number, [])

                    cs1 = used_mp1 in cs_bands
                    cs2 = used_mp2 in cs_bands
                    cs5 = used_mp5 in cs_bands

                    # On peut enfin insèrer la rangée !
                    row = "\t".join(
                        map(
                            str,
                            (
                                datetime,
                                date_id,
                                station_id,
                                constellation_id,
                                satellite_number,
                                ele,
                                azi,
                                # Les mp1-5
                                mp1,
                                mp2,
                                mp5,
                                # Les sig2noise1-5
                                sig2noise1,
                                sig2noise2,
                                sig2noise5,
                                # Si ça a cycle slip
                                cs1,
                                cs2,
                                cs5,
                            ),
                        )
                    )

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
                datetime, date_id, station_id, constellation_id,
                satellite, elevation, azimut,
                mp1, mp2, mp5,
                sig2noise1, sig2noise2, sig2noise5,
                cs1, cs2, cs5
            ) from stdin
            with null as 'None'
            """
        ) as copy:
            copy.write("\n".join(to_insert))

        cur.execute(
            """--sql
            insert into skyplot
            (
                datetime, date_id, station_id, constellation_id,
                satellite, elevation, azimut,
                mp1, mp2, mp5,
                sig2noise1, sig2noise2, sig2noise5,
                cs1, cs2, cs5
            )
            (select 
                datetime, date_id, station_id, constellation_id,
                satellite, elevation, azimut,
                mp1, mp2, mp5,
                sig2noise1, sig2noise2, sig2noise5,
                cs1, cs2, cs5
            from tmp_skyplot)
            on conflict do nothing;
            """
        )
