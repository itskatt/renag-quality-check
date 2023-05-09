from enum import Enum
from collections import defaultdict

from psycopg.sql import SQL, Identifier

from ..database import get_constellation_id, get_observation_id


class TimeSeries(Enum):
    """
    Toutes les métriques disponibles.
    """
    SIG2NOISE = "sig2noise"
    MULTIPATH = "multipath"
    OBSERVATION_CS = "observation_cs"
    SATELLITE_CS = "satellite_cs"


def create_metric_dest(metric_type: TimeSeries):
    """
    Crée un dictionnaire qui contiendra les données d'une métrique.
    """
    return {
        "type": metric_type.value,
        "length": 0,
        "data": defaultdict(list)
    }


def extract_from_section_header_into(f, dest, current_date):
    """
    Extrait une donnée dans l'entête d'une section d'un fichier
    xtr et le formatte dans un format tabulaire, prêt pour une
    insertion dans une base de données.
    """
    next(f)  # entête de section
    next(f)  # entête des moyennes

    # Extraction
    extracted = []

    line: str = next(f)
    while line.startswith("="):
        splitted = line.split()

        band = splitted[0][1:]  # "GPSS1C" par ex
        try:
            mean = float(splitted[3])
        except ValueError:
            mean = 0.0

        extracted.append((band, mean))

        line = next(f)
    
    # Mise en forme tabulaire
    data = dest["data"]
    for band, value in extracted:
        dest["length"] += 1

        data["date"].append(current_date)
        data["constellation"].append(band[:3])  # shortname
        data["observation_type"].append(band[-2:]) # 2 derniers caractères
        data["value"].append(value)


def insert_header_section_metric(cur, station_id, metric_data):
    """
    Insère les données d'une métrique extraite dans l'entête d'une section
    dans une base de données.
    """
    to_insert = []
    data = metric_data["data"]
    for i in range(metric_data["length"]):
        # Constellation
        constellation_id = get_constellation_id(cur, data["constellation"][i])

        # Observation type
        observation_id = get_observation_id(cur, data["observation_type"][i])

        # On colle tout ensemble
        row = cur.mogrify(
            "(%s,%s,%s,%s,%s)",
            (data["date"][i], station_id, constellation_id, observation_id, data["value"][i])
        )
        to_insert.append(row)

    # On envoie dans la base de données
    cur.execute(
        SQL("insert into {}(date, station_id, constellation_id, observation_type_id, value) values ")
        .format(Identifier(metric_data["type"])).as_string(cur) +
        ",".join(to_insert)
    )
