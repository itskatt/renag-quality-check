from datetime import date
from io import StringIO
from pathlib import Path
from math import isclose
from textwrap import dedent

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


@pytest.fixture
def file_with_blhgns():
    data = dedent("""\
    =XYZGLO 2023-01-02 00:00:00     4687285.2234      31077.7674    4313523.3340     5.0     3.9     5.6    96     0
    =XYZGNS 2023-01-02 00:00:00     4687284.9409      31079.1006    4313523.3731     1.3     0.7     1.1    96     0
    =BLHGPS 2023-01-02 00:00:00     42.813272463     0.379895887       1788.8304     1.3     1.3     2.0    96     0
    =BLHGAL 2023-01-02 00:00:00     42.813274044     0.379895774       1788.7777     0.7     0.7     1.0    96     2
    =BLHGLO 2023-01-02 00:00:00     42.813270222     0.379878487       1788.9486     3.2     5.3     6.8    96     0
    =BLHGNS 2023-01-02 00:00:00     42.813272271     0.379894785       1788.7243     1.0     0.9     1.3    96     1

    #POSGNS 2023-01-02 00:00:00           X [m]           Y [m]           Z [m]         B [deg]         L [deg]     H [m]   GDOP  PDOP  HDOP  VDOP      REC_CLK[m] #Sat #Excl
    POSGPS 2023-01-02 00:00:00     4687282.3898      31078.9649    4313520.6936    42.813270072     0.379893353 1785.0814   2.2   2.0   0.7   1.7             0.1    9     1
    POSGPS 2023-01-02 00:15:00 
    """)
    return StringIO(data)


def test_get_station_coords(file_with_blhgns):
    found_lat, found_long = get_station_coords(file_with_blhgns)

    assert found_lat is not None
    assert found_long is not None

    assert isclose(found_lat, 42.813272271)
    assert isclose(found_long, 0.379894785)


@pytest.fixture
def file_no_blhgns():
    data = dedent("""\
    =BLHGLO 2023-01-02 00:00:00     42.813270222     0.379878487       1788.9486     3.2     5.3     6.8    96     0

    #POSGNS 2023-01-02 00:00:00           X [m]           Y [m]           Z [m]         B [deg]         L [deg]     H [m]   GDOP  PDOP  HDOP  VDOP      REC_CLK[m] #Sat #Excl
    """)
    return StringIO(data)


def test_get_station_coords_no_blhgns(file_no_blhgns):
    found_lat, found_long = get_station_coords(file_no_blhgns)

    assert found_lat is None
    assert found_long is None
