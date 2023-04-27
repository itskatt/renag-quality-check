import os
from pathlib import Path

import xtr2database

HERE = Path(__file__).parent

infiles = HERE / ".." /".." / "graphes simples" / "data_2023"

os.environ["XTR_FILES_ROOT"] = str(infiles.resolve())

xtr2database.main()
