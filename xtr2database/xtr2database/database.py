from functools import partial

import psycopg
from psycopg import ClientCursor
from psycopg.rows import dict_row
from psycopg.sql import SQL, Identifier

from .metrics import TimeSeries

db_connection = partial(
    psycopg.connect,
    dbname="quality_check_data",
    user="m1m", # TODO: changer
    row_factory=dict_row,
    cursor_factory=ClientCursor
) # type: ignore


def clear_tables(cur, network):
    """
    Supprime les données des tables des metriques et skyplots.
    """
    where_clause = """
        where s.station_id in (
            select station_id
            from station_network
            inner join network n on station_network.network_id = n.id
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
            cur, constellation_shortname,
            "select id from constellation where shortname = %s;",

            "insert into constellation (fullname, shortname) values (%s, %s) returning id;",
            (constellation_shortname, constellation_shortname)
        )

    def get_observation_id(self, cur, observation_type):
        """
        Récupère l'ID d'un type d'observation à partir de la base de données.
        """
        return self.fetch_or_create(
            cur, observation_type,
            "select id from observation_type where type = %s;",

            "insert into observation_type (type) values (%s) returning id;",
            (observation_type,)
        )
