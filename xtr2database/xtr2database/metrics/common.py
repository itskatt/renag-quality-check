from psycopg.sql import SQL, Identifier

from ..database import get_constellation_id, get_observation_id


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

    # On envoie dans la base de données si il y a des données à envoyer
    if to_insert:
        cur.execute(
            SQL("insert into {}(date, station_id, constellation_id, observation_type_id, value) values ")
            .format(Identifier(metric_data["type"])).as_string(cur) +
            ",".join(to_insert)
        )
