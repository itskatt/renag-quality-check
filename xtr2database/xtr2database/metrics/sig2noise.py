from ..database import fetch_or_create

def extract_into(f, dest, current_date):
    """
    Extrait le sig2noise moyen d'un fichier xtr
    """
    next(f)  # entête de section
    next(f)  # entête des moyennes

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


def insert(cur, station_id, sig2noise_data):
    to_insert = []
    data = sig2noise_data["data"]
    for i in range(sig2noise_data["length"]):
        # Constellation
        constellation_shortname = data["constellation"][i]
        constellation_id = fetch_or_create(
            cur, constellation_shortname,
            "select id from constellation where shortname = %s;",

            "insert into constellation (fullname, shortname) values (%s, %s) returning id;",
            ("??", constellation_shortname)
        )

        # Observation
        observation_type = data["observation_type"][i]
        observation_id = fetch_or_create(
            cur, observation_type,
            "select id from observation_type where type = %s;",

            "insert into observation_type (type) values (%s) returning id;",
            (observation_type,)
        )

        # On colle tout ensemble
        row = cur.mogrify(
            "(%s,%s,%s,%s,%s)",
            (data["date"][i], station_id, constellation_id, observation_id, data["value"][i])
        )
        to_insert.append(row)

    # On envoie dans la base de données
    cur.execute(
        "insert into sig2noise(date, station_id, constellation_id, observation_type_id, value) values " +
        ",".join(to_insert)
    )