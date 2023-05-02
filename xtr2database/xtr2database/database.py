from functools import partial

import psycopg
from psycopg import ClientCursor
from psycopg.rows import dict_row


db_connection = partial(
    psycopg.connect,
    dbname="quality_check_data",
    user="m1m", # TODO: changer
    row_factory=dict_row,
    cursor_factory=ClientCursor
) # type: ignore

_database_fetch_cache = {}


def fetch_or_create(cur, key, fetch_query, *insert_args):
    """
    Récupère l'ID d'un objet à partir de la base de données ou crée un nouvel objet
    avec l'ID spécifié si aucun n'existe dans la base de données.
    """
    # Si l'id a déjà été recupéré, on le prend du cache
    cached = _database_fetch_cache.get(key)
    if cached:
        return cached

    cur.execute(fetch_query, (key,))
    res = cur.fetchone()

    if not res:
        cur.execute(*insert_args)
        obj_id = cur.fetchone()["id"]
    else:
        obj_id = res["id"]

    _database_fetch_cache[key] = obj_id
    return obj_id


def get_constellation_id(cur, constellation_shortname):
    """
    Récupère l'ID d'une constellation à partir de la base de données.
    """
    return fetch_or_create(
        cur, constellation_shortname,
        "select id from constellation where shortname = %s;",

        "insert into constellation (fullname, shortname) values (%s, %s) returning id;",
        ("??", constellation_shortname)
    )


def get_observation_id(cur, observation_type):
    """
    Récupère l'ID d'un type d'observation à partir de la base de données.
    """
    return fetch_or_create(
        cur, observation_type,
        "select id from observation_type where type = %s;",

        "insert into observation_type (type) values (%s) returning id;",
        (observation_type,)
    )
