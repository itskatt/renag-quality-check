from datetime import date
from pathlib import Path

import pytest

from xtr2database.extractors import (get_file_date, get_station_coords,
                                     get_station_id)


@pytest.mark.parametrize(
    "file_stem, expected",
    [
        ("ADER00FRA-2023-01-02", date(2023, 1, 2)),
        ("ADER00FRA-2023-12-31", date(2023, 12, 31)),
        ("ADER00FRA-2023-05-31", date(2023, 5, 31)),
        ("BOUF00FRA-2023-05-01", date(2023, 5, 1))
    ]
)
def test_get_file_date(file_stem, expected):
    assert get_file_date(file_stem) == expected


@pytest.mark.parametrize(
    "file_stem",
    [
        "file-2023-31-05.xtr",
        "file-2023-ss",
        "file-2023-05-ss",
        "file-2023-05-ss.xtr"
    ]
)
def test_get_file_date_bad_arguments(file_stem):
    with pytest.raises(ValueError):
        get_file_date(file_stem)


def test_get_station_id():
    file = Path("ADER00FRA-2023-01-02.xtr")
    assert get_station_id(file) == "ADER00FRA"
