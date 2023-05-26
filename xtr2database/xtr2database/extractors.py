"""
Fonctions pour extraire des données des fichiers XTR.
"""
from datetime import datetime


def get_file_date(filename):
    """
    Renvoie la date d'un fichier xtr.
    """
    date_ = filename.split("-", 1)[1]
    parsed = datetime.strptime(date_, "%Y-%m-%d")
    return parsed.date()


def get_station_id(file):
    """
    Renvoie l'identifiant d'une station en fonction de son nom de fichier.
    """
    return file.stem.split("-", 1)[0]


def get_station_coords(f):
    """
    Extrait les coordonées d'une station d'un de ses fichiers.
    """
    line = next(f)

    while True:
        if line.startswith("=BLHGNS"):
            break
        elif line == "\n": # Pas de BLHGNS
            return None, None

        line = next(f)

    splitted = line.split()

    return (
        float(splitted[3]),
        float(splitted[4])
    )
