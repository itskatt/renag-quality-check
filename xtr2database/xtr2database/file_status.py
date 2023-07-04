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
from collections import defaultdict

from .extractors import (get_rinex3_file_date, get_rinex3_station_id,
                         get_xtr_file_date, get_xtr_file_stem_station_id)


def process_files(file_type, files_gen, get_date, get_station, data_dict):
    for file in files_gen:
        station = get_station(file.stem)
        date = get_date(file.stem)

        data_dict[station][date][file_type] = True


def _data_dict_default_factory():
    #        V Date
    return defaultdict(lambda: {
        "rinex": False,
        "xtr": False
    })


def file_status(args, db_connection):
    # TODO verif db

    # Rassemblement des informations
    rinex_files = args.rinex3_files
    xtr_files = args.xtr_files

    data = defaultdict(_data_dict_default_factory)

    print("Traitement des fichiers Rinex 3...")
    process_files("rinex", rinex_files.rglob("*.crx.gz"), get_rinex3_file_date, get_rinex3_station_id, data)

    print("Traitement des fichiers xtr...")
    pattern = "*.xtr.gz" if args.gziped else "*.xtr"
    process_files("xtr", xtr_files.rglob(pattern), get_xtr_file_date, get_xtr_file_stem_station_id, data)

    # Insertion dans la base de données
    # TODO
    print(data)
