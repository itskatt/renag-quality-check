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
from datetime import datetime


def get_xtr_file_date(file_stem):
    """
    Renvoie la date d'un fichier xtr.
    """
    date_ = file_stem.split("-", 1)[1]
    parsed = datetime.strptime(date_, "%Y-%m-%d")
    return parsed.date()


def get_xtr_station_id(file):
    """
    Renvoie l'identifiant d'une station en fonction de son nom de fichier (xtr).
    """
    return file.stem.split("-", 1)[0]


def get_xtr_file_stem_station_id(file_stem):
    return file_stem.split("-", 1)[0]


def get_rinex3_file_date(file_stem):
    date_part = file_stem.split("_")[2]

    year = int(date_part[:4])
    day_number = int(date_part[4:7])

    parsed = datetime.strptime(f"{year} {day_number}", "%Y %j")
    return parsed.date()


def get_rinex3_station_id(file_stem):
    return file_stem.split("_")[0]


def get_station_coords(f):
    """
    Extrait les coordonées d'une station d'un de ses fichiers.
    """
    line = next(f)

    while True:
        if line.startswith("=BLHGNS"):
            break
        elif line == "\n":  # Pas de BLHGNS
            return None, None

        line = next(f)

    splitted = line.split()

    return (float(splitted[3]), float(splitted[4]))
