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
from enum import Enum
from collections import defaultdict


class TimeSeries(Enum):
    """
    Toutes les séries temporelles disponibles.
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

    return bool(extracted)
