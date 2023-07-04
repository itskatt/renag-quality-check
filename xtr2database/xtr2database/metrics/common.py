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
from psycopg.sql import SQL, Identifier


def insert_header_section_metric(cur, fetcher, station_id, metric_data):
    """
    Insère les données d'une métrique extraite dans l'entête d'une section
    dans une base de données.
    """
    to_insert = []
    data = metric_data["data"]
    for i in range(metric_data["length"]):
        # Constellation
        constellation_id = fetcher.get_constellation_id(cur, data["constellation"][i])

        # Observation type
        observation_id = fetcher.get_observation_id(cur, data["observation_type"][i])

        # On colle tout ensemble
        row = cur.mogrify(
            "(%s,%s,%s,%s,%s)", (data["date"][i], station_id, constellation_id, observation_id, data["value"][i])
        )
        to_insert.append(row)

    # On envoie dans la base de données si il y a des données à envoyer
    if to_insert:
        cur.execute(
            SQL("insert into {}(date, station_id, constellation_id, observation_type_id, value) values ")
            .format(Identifier(metric_data["type"]))
            .as_string(cur)
            + ",".join(to_insert)
        )
