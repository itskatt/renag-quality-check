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


def extract_sig_noise_ratio(f):
    """
    Extrait le sig2noise moyen d'un fichier xtr
    """
    next(f)  # entête de section
    next(f)  # entête des moyennes

    out = {}

    line: str = next(f)
    while line.startswith("="):
        splitted = line.split()

        band = splitted[0][1:]  # "GPSS1C" par ex
        try:
            mean = float(splitted[3])
        except ValueError:
            mean = 0.0

        out[band] = mean

        line = next(f)

    return out

