import os
from pathlib import Path

import xtr2database

HERE = Path(__file__).parent

infiles = HERE / ".." /".." / "graphes simples" / "data_2023"

# TODO : documenter cette variable d'environnement ou bien
#      la rendre configurable par un argument de ligne de commande
os.environ["XTR_FILES_ROOT"] = str(infiles.resolve())

xtr2database.main()
