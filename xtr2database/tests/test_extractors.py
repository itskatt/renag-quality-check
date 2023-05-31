from datetime import datetime
from pathlib import Path

import pytest

from xtr2database.extractors import (get_file_date, get_station_coords,
                                     get_station_id)


def test_get_file_date():
    filename = "ADER00FRA-2023-01-02"
    expected_date = datetime(2023, 1, 2).date()

    assert get_file_date(filename) == expected_date


def test_get_file_date_bad_arguments():
    with pytest.raises(ValueError):
        get_file_date("file-2023-31-05.xtr")


def test_get_station_id():
    file = Path("ADER00FRA-2023-01-02.xtr")
    assert get_station_id(file) == "ADER00FRA"
