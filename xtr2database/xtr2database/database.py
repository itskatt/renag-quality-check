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
from functools import partial

import psycopg
from psycopg import ClientCursor
from psycopg.rows import dict_row
from psycopg.sql import SQL, Identifier

from .metrics import TimeSeries


def create_db_connection(user, password, remote_host, port):
    """
    Créer une fonction de connexion à la base de données.
    """
    return partial(
        psycopg.connect,
        host=remote_host,
        port=port,
        dbname="quality_check_data",
        user=user,
        password=password,
        row_factory=dict_row,
        cursor_factory=ClientCursor,
    )  # type: ignore


def clear_tables(cur, network):
    """
    Supprime les données des tables des metriques et skyplots.
    """
    where_clause = """
        where s.station_id in (
            select sta.id
            from station sta
            inner join network n on sta.network_id = n.id
            where n.name = %s
        );
    """

    for metric in TimeSeries:
        cur.execute(SQL("delete from {} s" + where_clause).format(Identifier(metric.value)), (network,))

    cur.execute("delete from skyplot s" + where_clause, (network,))
    cur.execute("delete from inserted_file s" + where_clause, (network,))


class DatabaseFetcher:
    """
    Opérations de récupérations de la base de données, versions thread-safe et non.
    """

    _database_fetch_cache = {}

    def __init__(self, lock=None):
        self._lock = lock

    def _create(self, cur, key, fetch_query, insert_args):
        """
        Créer un objet dans la base de donné parce qu'il n'existe pas.
        """
        cur.execute(fetch_query, (key,))
        res = cur.fetchone()

        if not res:
            cur.execute(*insert_args)
            obj_id = cur.fetchone()["id"]
        else:
            obj_id = res["id"]

        self._database_fetch_cache[key] = obj_id
        return obj_id

    def fetch_or_create(self, cur, key, fetch_query, *insert_args):
        """
        Récupère l'ID d'un objet à partir de la base de données ou crée un nouvel objet
        avec l'ID spécifié si aucun n'existe dans la base de données.
        """
        # Si l'id a déjà été recupéré, on le prend du cache
        cached = self._database_fetch_cache.get(key, "-empty")
        if cached != "-empty":
            return cached

        if not self._lock:
            return self._create(cur, key, fetch_query, insert_args)

        with self._lock:
            return self._create(cur, key, fetch_query, insert_args)

    def get_constellation_id(self, cur, constellation_shortname):
        """
        Récupère l'ID d'une constellation à partir de la base de données.
        """
        return self.fetch_or_create(
            cur,
            constellation_shortname,
            "select id from constellation where shortname = %s;",
            "insert into constellation (fullname, shortname) values (%s, %s) returning id;",
            (constellation_shortname, constellation_shortname),
        )

    def get_observation_id(self, cur, observation_type):
        """
        Récupère l'ID d'un type d'observation à partir de la base de données.
        """
        return self.fetch_or_create(
            cur,
            observation_type,
            "select id from observation_type where type = %s;",
            "insert into observation_type (type) values (%s) returning id;",
            (observation_type,),
        )
