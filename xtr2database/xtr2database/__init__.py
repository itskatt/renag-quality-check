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
import argparse
import os
import sys
from pathlib import Path

from .database import create_db_connection
from .xtr_import import xtr_import


def get_args():
    """
    Parse les arguments en lignes de commandes avec argparse.
    """
    parser = argparse.ArgumentParser("xtr2database")

    # arguments communs
    parser.add_argument(
        "-H", "--remote-host",
        help="Spécifie l'adresse du serveur pour se connecter à la base de données"
    )

    parser.add_argument(
        "-p", "--port",
        help="Spécifie le port pour se connecter à la base de données"
    )

    parser.add_argument(
        "-U", "--user",
        help="Spécifie le nom d'utilisateur pour se connecter à la base de données"
    )

    parser.add_argument(
        "-P", "--password",
        help="Spécifie le mot de passe à utiliser pour se connecter à la base de données"
    )

    parser.add_argument(
        "-o", "--override",
        help="Ecrase toute les données du réseau de station avant de les insérer",
        action="store_true"
    )

    parser.add_argument(
        "-z", "--gziped",
        help="Recherche des fichiers .xtr.gz au lieux de .xtr, et décompresse-les à la volée si besoin",
        action="store_true"
    )

    subparsers = parser.add_subparsers(dest="mode")

    # importation des fichiers xtr
    xtr_import = subparsers.add_parser(
        "import",
        help="Importe les fichiers xtr d'un réseau de station"
    )

    xtr_import.add_argument(
        "xtr_files",
        help="Sources des fichiers xtr à traiter",
        type=Path
    )

    xtr_import.add_argument(
        "network",
        help="Le réseau de station dont proviennent les fichiers"
    )

    xtr_import.add_argument(
        "--parallel",
        help="Traite les stations en parallèle sur plusieurs processus. Experimental",
        action="store_true"
    )

    # verification de la disponibilité des fichiers
    file_status = subparsers.add_parser(
        "file_status",
        help="Verifie la présence des fichiers xtr et Rinex 3 d'un réseau de stations"
    )

    file_status.add_argument(
        "rinex3_files",
        help="Source des fichiers Rinex 3 à vérifier",
    )

    file_status.add_argument(
        "xtr_files",
        help="Source des fichiers xtr à vérifier",
    )

    file_status.add_argument(
        "network",
        help="Le réseau de station dont proviennent les fichiers",
    )

    return parser.parse_args()


def main():
    """
    Programme principal.
    """
    args = get_args()

    # Les arguments CLI sont prioritaire sur les variables d'env
    if not args.user:
        try:
            user = os.environ["X2D_USER"]
        except KeyError:
            print(
                "Erreur : pas d'utilisateur spécifié (ni dans la variable "
                "d'environement X2D_USER ni en argument de ligne de commande)"
            )
            sys.exit(-1)
    else:
        user = args.user

    password = args.password or os.environ.get("X2D_PASSWORD")

    db_connection = create_db_connection(user, password, args.remote_host, args.port)

    if args.mode == "import":
        xtr_import(args, db_connection)
